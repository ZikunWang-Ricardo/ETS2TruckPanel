import json
from pathlib import Path
import sys
import tempfile
import unittest
import importlib.util
import subprocess
import zipfile
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'portable'))
import setup_core as core


class PortableTests(unittest.TestCase):
    def test_chords_and_scan_codes(self):
        self.assertEqual(core.KEYS[10],('f11',87))
        self.assertEqual(core.KEYS[11],('f12',88))
        controls=core.portable_controls([{'mix':'engine'},{'mix':'parkingbrake'}])
        self.assertEqual(controls[0]['keys'],[285,54,59])
        self.assertNotIn(29,controls[0]['keys'])

    def test_patch_keeps_user_inputs_and_is_idempotent(self):
        raw=b'SiiNunit\r\n{\r\n config_lines[0]: "mix engine `keyboard.x?0 | joy.b9?0`"\r\n config_lines[1]: "mix advmouse `keyboard.f1?0`"\r\n config_lines[2]: "mix geardown `keyboard.lctrl?0 | joy.b2?0`"\r\n}\r\n'
        controls=core.portable_controls([{'mix':'engine'}])
        new=core.patch_profile(raw,controls)
        self.assertIn(b'keyboard.x?0 | joy.b9?0',new)
        self.assertIn(b'mix geardown `keyboard.lctrl?0 | joy.b2?0`',new)
        self.assertIn(b'keyboard.f1?0 & !',new)
        self.assertEqual(core.patch_profile(new,controls,managed=True),new)
        self.assertEqual(new.count(b'\r\n'),raw.count(b'\r\n'))

    def test_independent_legacy_shortcuts_are_preserved(self):
        raw=b'SiiNunit\n"mix engine `(keyboard.lctrl?0 & keyboard.lalt?0 & keyboard.f2?0) | (joy.b1?0)`"'
        new=core.patch_profile(raw,core.portable_controls([{'mix':'engine'}]))
        self.assertIn(b'keyboard.lctrl?0',new)
        self.assertIn(b'keyboard.f2?0',new)
        self.assertIn(b'joy.b1?0',new)

    def test_reserved_custom_shortcuts_require_ownership_and_unrelated_legacy_is_untouched(self):
        controls=core.portable_controls([{'mix':'engine'}])
        raw=b'SiiNunit\n"mix engine `keyboard.e?0`"\n"mix unrelated `(keyboard.lctrl?0 & keyboard.lalt?0 & keyboard.f2?0) | (joy.b2?0)`"'
        new=core.patch_profile(raw,controls)
        self.assertIn(raw.splitlines()[2],new)
        with self.assertRaises(ValueError):core.patch_profile(new,controls)
        self.assertEqual(core.patch_profile(new,controls,managed=True),new)

    def test_missing_action_and_binary_config_rejected(self):
        with self.assertRaises(ValueError): core.patch_profile(b'SiiNunit\n{}',[{'mix':'x','bind':'f1'}])
        with self.assertRaises(ValueError): core.patch_profile(b'SCSbinary',[])

    def test_install_and_restore_does_not_touch_save(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tests') as t:
            root=Path(t); config=root/'profile/controls.sii'; config.parent.mkdir()
            config.write_bytes(b'original'); save=root/'profile/save/game.sii';save.parent.mkdir();save.write_bytes(b'career progress')
            dll=root/'plugins/scs-telemetry.dll'
            receipt=core.apply_plan([(config,b'patched'),(dll,b'newdll')],root/'backups')
            self.assertEqual(save.read_bytes(),b'career progress')
            core.restore(receipt)
            self.assertEqual(config.read_bytes(),b'original')
            self.assertFalse(dll.exists())
            self.assertEqual(save.read_bytes(),b'career progress')

    def test_restore_preflights_all_files_before_changing_any(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tests') as t:
            root=Path(t);a=root/'a';b=root/'b';a.write_bytes(b'old');b.write_bytes(b'old')
            receipt=core.apply_plan([(a,b'new'),(b,b'new')],root/'backups')
            b.write_bytes(b'user changes')
            with self.assertRaises(ValueError):core.restore(receipt)
            self.assertEqual(a.read_bytes(),b'new')

    def test_failed_install_rolls_back_previous_writes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'tests') as t:
            root=Path(t);a=root/'a';b=root/'b';a.write_bytes(b'old')
            original=core.atomic_write
            def failing(path,data):
                if Path(path)==b:raise PermissionError('blocked')
                return original(path,data)
            with patch.object(core,'atomic_write',side_effect=failing):
                with self.assertRaises(PermissionError):core.apply_plan([(a,b'new'),(b,b'new')],root/'backups')
            self.assertEqual(a.read_bytes(),b'old')
            self.assertFalse(b.exists())


class ShareIntegrationTests(unittest.TestCase):
    def test_archive_bootstrap_from_relocated_unicode_path(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root/'tests',prefix='便携 test-') as t:
            with zipfile.ZipFile(root/'dist/ETS2TruckPanel-v0.1.0-windows-x64.zip') as z:z.extractall(t)
            package=Path(t)/'TouchTruck-Share-Windows-x64'
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                                   str(package/'setup/bootstrap.ps1'),'-Check'],capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,(result.stdout+result.stderr).decode('utf-8',errors='replace'))
            self.assertTrue((package/'_setup_runtime/python.exe').is_file())
            self.assertFalse((package/'installation-backups').exists())

    def test_share_install_restore_and_embedded_runtime(self):
        root=Path(__file__).resolve().parents[1]
        package=root/'release/TouchTruck-Share-Windows-x64'
        spec=importlib.util.spec_from_file_location('share_installer',root/'portable/install.py')
        installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
        controls=json.loads((package/'shortcuts.json').read_text(encoding='utf-8'))
        raw=('SiiNunit\r\n{\r\n'+'\r\n'.join(f' config_lines[{i}]: "mix {c["mix"]} `joy.b{i+1}?0`"' for i,c in enumerate(controls))+'\r\n}\r\n').encode()
        with tempfile.TemporaryDirectory(dir=root/'tests') as t:
            fake=Path(t);game=fake/'Game';exe=game/'bin/win_x64/eurotrucks2.exe';exe.parent.mkdir(parents=True);exe.write_bytes(b'fixture')
            profile=fake/'Documents/Euro Truck Simulator 2/steam_profiles/AB/controls.sii';profile.parent.mkdir(parents=True);profile.write_bytes(raw)
            save=profile.parent/'save/autosave/game.sii';save.parent.mkdir(parents=True);save.write_bytes(b'progress must survive')
            tp=fake/'AppData/TouchPortal'
            plan=installer.installation_plan(package,game,profile,tp)
            self.assertTrue(all(p.name!='game.sii' for p,_ in plan))
            receipt=core.apply_plan(plan,fake/'backups')
            patched=profile.read_bytes()
            for i in range(len(controls)):self.assertIn(f'joy.b{i+1}?0'.encode(),patched)
            self.assertEqual(patched,core.patch_profile(patched,controls,managed=True))
            launch=tp/'plugins/TouchTruck/runtime/python.exe'
            bridge=tp/'plugins/TouchTruck/app/run_bridge.py'
            result=subprocess.run([str(launch),'-X','utf8',str(bridge),'--probe'],capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            self.assertIn('connected',json.loads(result.stdout))
            core.restore(receipt)
            self.assertEqual(profile.read_bytes(),raw)
            self.assertEqual(save.read_bytes(),b'progress must survive')
            self.assertFalse(launch.exists())

    def test_share_contains_no_creator_paths_or_private_artifacts(self):
        root=Path(__file__).resolve().parents[1]
        package=root/'dist/ETS2TruckPanel-v0.1.0-windows-x64.zip'
        import io
        with zipfile.ZipFile(package) as z:
            self.assertIsNone(z.testzip())
            for name in z.namelist():
                self.assertFalse(any(x in name.lower() for x in ('backups/','logs/','target.json','controls.sii')))
                data=z.read(name)
                if name.endswith('.tpp'):
                    with zipfile.ZipFile(io.BytesIO(data)) as inner:
                        self.assertIsNone(inner.testzip())
                        for n in inner.namelist():
                            if n.endswith(('.py','.json','.tp')):
                                self.assertNotIn(b'anaconda3',inner.read(n).lower())
                                self.assertNotIn(b'C:\\Users\\',inner.read(n))
                elif name.endswith(('.py','.json','.txt','.md','.html')):
                    self.assertNotIn(b'anaconda3',data.lower())
                    self.assertNotIn(b'C:\\Users\\',data)


if __name__=='__main__':unittest.main()

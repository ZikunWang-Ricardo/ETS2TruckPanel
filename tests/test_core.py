import json
import socket
import struct
import threading
import unittest

from touchtruck.telemetry import decode_snapshot, SnapshotTracker
from touchtruck.input import InputController, WindowsInput
from touchtruck.bindings import patch_controls
from touchtruck.bridge import JsonLines, pair


class TelemetryTests(unittest.TestCase):
    def sample(self):
        b = bytearray(32768)
        b[0] = 1
        struct.pack_into('<Q', b, 8, 123)
        struct.pack_into('<I', b, 40, 12)
        struct.pack_into('<I', b, 52, 1)
        struct.pack_into('<f', b, 948, 20)
        struct.pack_into('<f', b, 988, 25)
        struct.pack_into('<f', b, 1000, 321.5)
        struct.pack_into('<f', b, 1008, 900)
        b[1566] = 1  # parkBrake, first truck bool after 66 config bools
        b[1580] = 1  # blinkerLeftOn
        b[6064] = 1  # first trailer attached
        return b

    def test_units_and_flags(self):
        s = decode_snapshot(self.sample())
        self.assertAlmostEqual(s['speed'], 72)
        self.assertAlmostEqual(s['cruise_speed'], 90)
        self.assertEqual(s['fuel'], 321.5)
        self.assertEqual(s['range'], 900)
        self.assertTrue(s['parking'])
        self.assertTrue(s['left'])
        self.assertTrue(s['trailer'])

    def test_bad_revision_and_short_buffer(self):
        b = self.sample()
        struct.pack_into('<I', b, 40, 99)
        with self.assertRaises(ValueError): decode_snapshot(b)
        with self.assertRaises(ValueError): decode_snapshot(b'abc')

    def test_nan_rejected(self):
        b = self.sample()
        struct.pack_into('<f', b, 1000, float('nan'))
        with self.assertRaises(ValueError): decode_snapshot(b)

    def test_stale_and_recovery(self):
        t = SnapshotTracker(timeout=2)
        s = decode_snapshot(self.sample())
        self.assertTrue(t.update(s, 0)['connected'])
        stale = t.update(s, 3)
        self.assertFalse(stale['connected'])
        self.assertIsNone(stale['fuel'])
        s['timestamp'] += 1
        self.assertTrue(t.update(s, 4)['connected'])


class InputTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.focus = True
        self.c = InputController(lambda k, down: self.events.append((k, down)), lambda: self.focus)

    def test_hold_release_and_focus_loss(self):
        self.c.down('window', [29, 56, 59], 0)
        self.c.down('window', [29, 56, 59], 0.1)
        self.assertEqual(len(self.events), 3)
        self.focus = False
        self.c.tick(0.2)
        self.assertEqual(self.events[-3:], [(59, False), (56, False), (29, False)])
        self.assertFalse(self.c.held)
        self.c.down('window', [29, 56, 59], 1)
        self.assertEqual(len(self.events), 6)

    def test_lost_up_times_out(self):
        self.c.down('horn', [35], 0)
        self.c.tick(9)
        self.assertEqual(self.events, [(35, True), (35, False)])

    def test_shared_modifiers_remain_until_last_release(self):
        self.c.down('a', [29, 56, 59], 0)
        self.c.down('b', [29, 56, 60], 0)
        self.c.up('a')
        self.assertNotIn((29, False), self.events)
        self.c.release_all()
        self.assertEqual(self.events[-1], (29, False))

    def test_failed_release_retries_and_does_not_skip_other_keys(self):
        failed = [False]
        def backend(key, down):
            self.events.append((key, down))
            if not down and key == 59 and not failed[0]:
                failed[0] = True
                raise OSError('transient release failure')
        self.c.send_key = backend
        self.c.down('window', [29,56,59], 0)
        self.c.up('window')
        self.assertIn((29,False), self.events)
        self.assertIn((56,False), self.events)
        self.assertEqual(self.c.held['window'], [59])
        self.c.release_all()
        self.assertFalse(self.c.held)

    def test_right_ctrl_scan_is_extended_and_right_shift_is_not(self):
        backend=WindowsInput()
        events=[]
        class User:
            def SendInput(self, count, pointer, size):
                event=pointer._obj
                events.append((event.ki.wScan,event.ki.dwFlags))
                return 1
        backend.user=User()
        backend.send(285,True)
        backend.send(54,True)
        backend.send(285,False)
        self.assertEqual(events,[(29,9),(54,8),(29,11)])


class BindingTests(unittest.TestCase):
    def test_preserve_joy_and_guard_existing_base_key(self):
        old = ' config_lines[1]: "mix test `keyboard.f1?0 | joy.b2?0`"\n config_lines[2]: "mix lwinopen `semantical.lwinopen?0`"\n'
        result = patch_controls(old, {'lwinopen': 'f1'})
        self.assertIn('joy.b2?0', result)
        self.assertIn('semantical.lwinopen?0', result)
        self.assertIn('!(keyboard.rctrl?0 & keyboard.rshift?0)', result)
        self.assertEqual(result, patch_controls(result, {'lwinopen': 'f1'}))

    def test_missing_action_is_error(self):
        with self.assertRaises(ValueError): patch_controls('', {'madeup': 'f1'})

    def test_duplicate_new_keys_is_error(self):
        with self.assertRaises(ValueError): patch_controls('', {'a': 'f1', 'b': 'f1'})

    def test_migrate_left_modifier_bindings_without_changing_manual_geardown(self):
        old = (' config_lines[1]: "mix geardown `keyboard.lctrl?0 | joy.b2?0`"\n'
               ' config_lines[2]: "mix cruiectrlinc `(keyboard.lctrl?0 & keyboard.lalt?0 & keyboard.f2?0) | (semantical.cruiectrlinc?0)`"\n'
               ' config_lines[3]: "mix showmirrors `(keyboard.f2?0 & !(keyboard.lctrl?0 & keyboard.lalt?0)) | semantical.showmirrors?0`"\n'
               ' config_lines[4]: "mix cabinlight `semantical.cabinlight?0`"\n')
        result=patch_controls(old, {'cruiectrlinc':'f2','cabinlight':'f12'})
        self.assertIn('mix geardown `keyboard.lctrl?0 | joy.b2?0`', result)
        self.assertNotIn('keyboard.lctrl?0 & keyboard.lalt?0', result)
        self.assertIn('(keyboard.rctrl?0 & keyboard.rshift?0 & keyboard.f2?0)', result)
        self.assertIn('(keyboard.rctrl?0 & keyboard.rshift?0 & keyboard.f12?0)', result)
        self.assertEqual(result,patch_controls(result, {'cruiectrlinc':'f2','cabinlight':'f12'}))

    def test_config_chords_do_not_press_left_ctrl_and_cabin_light_is_bound(self):
        from pathlib import Path
        controls=json.loads((Path(__file__).resolve().parents[1]/'config/controls.json').read_text(encoding='utf-8'))
        for c in controls:
            if c.get('bind'):
                self.assertEqual(c['keys'][:2], [285,54])
                self.assertNotIn(29,c['keys'])
        cabin=next(c for c in controls if c['id']=='cabin_light')
        self.assertEqual(cabin['mix'],'cabinlight')
        self.assertEqual(cabin['bind'],'f12')
        self.assertNotIn('unavailable',cabin)


class ProtocolTests(unittest.TestCase):
    def test_partial_utf8_multiple_lines_and_bad_json(self):
        f = JsonLines()
        b = (json.dumps({'name': '油量'}, ensure_ascii=False) + '\nBAD\n{}\n').encode()
        result = []
        for byte in b: result += f.feed(bytes([byte]))
        self.assertEqual(result, [{'name': '油量'}, {}])

    def test_fake_socket_pair(self):
        class FakeSocket:
            def sendall(self, data): self.data = data
        sock = FakeSocket()
        pair(sock)
        self.assertTrue(sock.data.endswith(b'\n'))
        self.assertEqual(json.loads(sock.data), {'type': 'pair', 'id': 'touchtruck'})


if __name__ == '__main__': unittest.main()

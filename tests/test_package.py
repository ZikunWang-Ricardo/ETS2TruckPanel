import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_all_controls_and_plugin_references(self):
        controls = json.loads((ROOT / 'config/controls.json').read_text(encoding='utf-8'))
        self.assertEqual(len(controls), 29)
        expected = {'engine','parking','trailer','diff_lock','axle','engine_brake','cab','top',
                    'left','right','hazard','lights','high_beam','flash','horn','wipers',
                    'cruise','cruise_down','cruise_up','lane_mode','lane_assist','cabin_light',
                    'shade_up','shade_down','lwinopen','lwinclose','rwinopen','rwinclose','acc_mode'}
        self.assertEqual({c['id'] for c in controls}, expected)
        with zipfile.ZipFile(ROOT / 'dist/TouchTruck.tpp') as z:
            self.assertIsNone(z.testzip())
            plugin = json.loads(z.read('TouchTruck/entry.tp'))
        category = plugin['categories'][0]
        actions = {a['id'] for a in category['actions']}
        states = {s['id'] for s in category['states']}
        with zipfile.ZipFile(ROOT / 'dist/TouchTruck.tpz') as z:
            self.assertIsNone(z.testzip())
            page = json.loads(z.read('pages/TouchTruck.tml'))
            self.assertEqual((page['KEY_COLUMNS'], page['KEY_ROWS']), (8, 5))
            ids = set()
            for r, row in enumerate(page['BUTTONS']):
                for c, b in enumerate(row):
                    if not b: continue
                    self.assertNotIn(b['id'], ids)
                    ids.add(b['id'])
                    self.assertLessEqual(c+b['COLS'], 8)
                    self.assertLess(r, 5)
                    self.assertIn('icons/'+b['I'], z.namelist())
                    for a in b['A'] + ([b['HA']] if b.get('HA') else []):
                        self.assertIn(a['kID'], actions)
                    for e in b['E']:
                        if e['KEY_TYPE'] == 'PLUGIN_EVENT': self.assertIn(e['kVSI'], states)
                        if e.get('KEY_FILENAME'): self.assertIn('icons/'+e['KEY_FILENAME'], z.namelist())

    def test_hold_controls_use_hold_action_only(self):
        with zipfile.ZipFile(ROOT/'dist/TouchTruck.tpz') as z:
            page = json.loads(z.read('pages/TouchTruck.tml'))
        buttons = {b['id']: b for row in page['BUTTONS'] for b in row if b}
        for name in ('horn','flash','engine_brake','lwinopen','rwinclose','shade_up'):
            b = buttons['touchtruck.button.'+name]
            self.assertEqual(b['A'], [])
            self.assertEqual(b['HA']['kHHF'], 'true')
        self.assertEqual(buttons['touchtruck.button.cabin_light']['A'][0]['kID'], 'touchtruck.action.cabin_light')

    def test_legacy_plugin_actions_have_string_flags_and_required_fields(self):
        with zipfile.ZipFile(ROOT/'dist/TouchTruck.tpz') as z:
            page=json.loads(z.read('pages/TouchTruck.tml'))
        for row in page['BUTTONS']:
            for b in row:
                for a in b.get('A',[]) + ([b['HA']] if b.get('HA') else []):
                    for field in ('kHHF','kInline','kStatic'):
                        self.assertIsInstance(a[field],str)
                    for field in ('kFormat','kmald','kmold','kCTS','kET','kcD','kcL'):
                        self.assertIn(field,a)


if __name__ == '__main__': unittest.main()

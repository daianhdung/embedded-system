import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from evaluate_ai import audit_manifest,image_metrics

class DatasetTests(unittest.TestCase):
    def test_missing_dataset_and_split_leakage_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest=root/'manifest.json'
            base=dict(v=1,dataset_id='test',source='unit fixture',license='unit fixture',samples=[])
            manifest.write_text(json.dumps(base))
            with self.assertRaises(ValueError):audit_manifest(manifest)
            (root/'a.jpg').write_bytes(b'fixture1');(root/'b.jpg').write_bytes(b'fixture2')
            base['samples']=[dict(path='a.jpg',label='lua',group='same-video',split='train'),dict(path='b.jpg',label='lua',group='same-video',split='test')]
            manifest.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,'group leaks'):audit_manifest(manifest)
            base['samples'][1]['group']='different-video';(root/'b.jpg').write_bytes(b'fixture1')
            manifest.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,'content leaks'):audit_manifest(manifest)
    def test_unknown_background_not_fabricated_as_correct_normal(self):
        rows=[dict(truth='binh_thuong',prediction='unknown'),dict(truth='binh_thuong',prediction='khoi'),dict(truth='lua',prediction='lua')]
        result=image_metrics(rows)
        self.assertEqual(result['background_false_alarm_rate'],.5)
        self.assertEqual(result['per_class']['binh_thuong']['recall'],0)
        self.assertEqual(result['per_class']['lua']['recall'],1)

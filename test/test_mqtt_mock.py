"""Unit checks for mock generation, not broker/ESP runtime evidence."""
import importlib.util
import json
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('mqtt_mock', Path(__file__).resolve().parents[1] / 'tools/mqtt_mock.py')
mock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock)

class PayloadTests(unittest.TestCase):
    def test_valid(self):
        p = json.loads(mock.payload_for('valid', now_ms=1793152800000))
        self.assertEqual(p, {'v': 1, 'nhan': 'lua', 'do_tin_cay': 0.93, 'ts_ms': 1793152800000})
    def test_negative_cases(self):
        self.assertNotIn('nhan', json.loads(mock.payload_for('missing')))
        self.assertIsInstance(json.loads(mock.payload_for('type'))['do_tin_cay'], str)
        self.assertGreater(json.loads(mock.payload_for('confidence'))['do_tin_cay'], 1)
        self.assertEqual(json.loads(mock.payload_for('old', now_ms=20000))['ts_ms'], 0)
        self.assertEqual(json.loads(mock.payload_for('future', now_ms=0))['ts_ms'], 60000)
        self.assertGreater(len(mock.payload_for('oversize')), 256)
        self.assertEqual(mock.payload_for('clear-retained'), b'')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(mock.payload_for('json'))

if __name__ == '__main__':
    unittest.main()

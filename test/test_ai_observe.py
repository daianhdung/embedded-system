"""Per-frame model gate tests; no camera, broker or trained-model accuracy claims."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import yolo_plugin
from yolo_plugin import assess


class ObservationGateTests(unittest.TestCase):
    def test_reported_hair_false_positive_is_not_selected(self):
        selected, status = assess([dict(label='smoke', confidence=.36)])
        self.assertIsNone(selected)
        self.assertEqual(status, 'BELOW_THRESHOLD')

    def test_previous_true_image_scores_also_fail_current_gate(self):
        for label, confidence in [('fire', .426), ('smoke', .689)]:
            self.assertEqual(assess([dict(label=label, confidence=confidence)])[1], 'BELOW_THRESHOLD')

    def test_no_detection_is_unknown_not_normal(self):
        self.assertEqual(assess([]), (None, 'NO_DETECTION'))

    def test_eligible_fire_outranks_smoke_but_ineligible_fire_does_not(self):
        result, status = assess([dict(label='fire', confidence=.8), dict(label='smoke', confidence=.99)])
        self.assertEqual((result.label, status), ('lua', 'ABOVE_THRESHOLD'))
        result, _ = assess([dict(label='fire', confidence=.79), dict(label='smoke', confidence=.9)])
        self.assertEqual(result.label, 'khoi')

    def test_slow_inference_does_not_produce_eligible_prediction(self):
        self.assertEqual(assess([dict(label='fire', confidence=.99)], inference_ms=15000), (None, 'STALE'))

    def test_bad_confidence_and_timing_are_rejected(self):
        for confidence in [float('nan'), float('inf'), 1.1, True]:
            with self.assertRaises(ValueError):
                assess([dict(label='fire', confidence=confidence)])
        for timing in [-1, float('nan')]:
            with self.assertRaises(ValueError): assess([], inference_ms=timing)

    def test_plugin_loads_once_and_preserves_unknown(self):
        with patch.object(yolo_plugin, '_detector', None), patch.object(yolo_plugin, 'YoloDetector') as detector:
            detector.return_value.observe.return_value.prediction = None
            self.assertIsNone(yolo_plugin.predict(object()))
            self.assertIsNone(yolo_plugin.predict(object()))
            detector.assert_called_once_with()
            self.assertEqual(detector.return_value.observe.call_count, 2)


if __name__ == '__main__':
    unittest.main()

from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from temporal_filter import TemporalGate
from ai_adapter import Prediction

class TemporalTests(unittest.TestCase):
    def test_requires_time_and_count_and_does_not_reuse_old_score(self):
        g=TemporalGate(2,3,5)
        self.assertIsNone(g.update(Prediction('lua',.9),0))
        self.assertIsNone(g.update(Prediction('lua',.95),1))
        result=g.update(Prediction('lua',.81),2)
        self.assertEqual(result.confidence,.81)
        self.assertIsNone(g.update(None,3))
        self.assertIsNone(g.update(Prediction('lua',.99),4))
    def test_gaps_and_label_changes_reset(self):
        g=TemporalGate(2,2,3)
        g.update(Prediction('lua',.9),0)
        self.assertIsNone(g.update(Prediction('lua',.9),4))
        self.assertIsNone(g.update(Prediction('khoi',.9),5))
        self.assertIsNone(g.update(Prediction('lua',.79),6))
    def test_disabled_preserves_existing_behavior(self):
        p=Prediction('binh_thuong',.9)
        self.assertIs(TemporalGate().update(p,0),p)

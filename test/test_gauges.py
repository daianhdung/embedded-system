from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.gauges import gauge_svg
from dashboard.presentation import METRICS

class GaugeTests(unittest.TestCase):
    def test_missing_reading_is_unknown_not_zero(self):
        svg=gauge_svg(METRICS['temperature_c'],None,False)
        ET.fromstring(svg)
        self.assertIn('—',svg)
        self.assertIn('stroke-dasharray="0.000 100"',svg)
    def test_out_of_scale_reading_is_printed_unchanged(self):
        svg=gauge_svg(METRICS['temperature_c'],-12.5)
        ET.fromstring(svg)
        self.assertIn('>-12.5</text>',svg)
        self.assertIn('>-20</text>',svg)
        svg=gauge_svg(METRICS['smoke_adc'],4500)
        self.assertIn('>4,500</text>',svg)
        self.assertIn('>4095</text>',svg)

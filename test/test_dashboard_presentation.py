"""Traceability and stale-data boundaries, independent from firmware decisions."""
from datetime import datetime,timezone
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.presentation import thresholds,reading_status,since_for,selected_ids
from dashboard.store import Store

class PresentationTests(unittest.TestCase):
    def test_stale_or_missing_never_normal(self):
        t=thresholds()
        self.assertEqual(t['kSmokeWarningAdc'],1800)
        self.assertEqual(reading_status('temperature_c',{'temperature_c':None},True,t)[1],'muted')
        self.assertEqual(reading_status('temperature_c',{'temperature_c':70},False,t)[1],'muted')
        self.assertEqual(reading_status('temperature_c',{'temperature_c':54,'active_mask':8},True,t)[1],'danger')
        self.assertEqual(reading_status('humidity_pct',{'humidity_pct':99},True,t)[1],'info')
    def test_filter_clock_and_stable_chart_record_ids(self):
        self.assertEqual(since_for('1 giờ qua',datetime(2026,10,29,4,tzinfo=timezone.utc)),'2026-10-29T03:00:00+00:00')
        self.assertEqual(selected_ids({'selection':{'record':[{'record_id':42}]}}),[42])
    def test_window_applies_before_limit_and_preserves_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            s=Store(Path(temp)/'test.sqlite','test/pccc')
            try:
                for i,boot in enumerate(['first','second','second']):
                    p=dict(v=1,record_type='TELEMETRY',state='NORMAL',firmware_id='FAKE',boot_id=boot,uptime_ms=i,local_level=0,ai_level=0,merged_level=0,pump_cmd=False,valve_cmd=False,door_open_cmd=False,buzzer_cmd=False,smoke_adc=1000+i)
                    s.add('test/pccc/device/esp32-01/telemetry',json.dumps(p).encode(),received_utc=f'2026-10-29T04:00:0{i}+00:00')
                rows=s.window('telemetry',since='2026-10-29T04:00:01+00:00',boot_id='second',limit=1)
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]['payload']['smoke_adc'],1002)
                self.assertEqual(rows[0]['id'],s.latest('telemetry')['id'])
            finally:s.close()

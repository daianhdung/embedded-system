import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.store import Store,device_view

PREFIX='test/pccc'

def sample(**changes):
    value=dict(v=1,record_type='TELEMETRY',firmware_id='R7-live',boot_id='boot',uptime_ms=100,
               state='NORMAL',local_level=0,ai_level=0,merged_level=0,pump_cmd=False,valve_cmd=False,
               door_open_cmd=False,buzzer_cmd=False,temperature_c=None,humidity_pct=None)
    value.update(changes);return json.dumps(value).encode()

class DashboardStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=Store(Path(self.temp.name)/'db.sqlite',PREFIX)
    def tearDown(self):self.store.close();self.temp.cleanup()
    def add(self,body=None,**kwargs):return self.store.add(PREFIX+'/device/esp32-01/telemetry',body or sample(),**kwargs)
    def test_old_import_retained_and_previous_session_never_live(self):
        self.add()
        self.assertFalse(device_view(self.store,'current',True,now=100)['live'])
        self.add(sample(uptime_ms=200),retained=True,session='current',monotonic=100)
        self.assertFalse(device_view(self.store,'current',True,now=100)['live'])
        self.add(sample(uptime_ms=300),session='previous',monotonic=100)
        self.assertFalse(device_view(self.store,'current',True,now=100)['live'])
    def test_fresh_turns_stale_and_offline(self):
        self.add(session='s',monotonic=100)
        self.assertTrue(device_view(self.store,'s',True,now=110)['live'])
        self.assertFalse(device_view(self.store,'s',True,now=116)['live'])
        self.assertFalse(device_view(self.store,'s',False,now=110)['live'])
        self.store.add(PREFIX+'/device/esp32-01/availability',b'offline',session='s',monotonic=110)
        self.assertFalse(device_view(self.store,'s',True,now=110)['live'])
    def test_wrong_firmware_and_fixture_not_live(self):
        self.add(session='s',monotonic=100)
        self.assertTrue(device_view(self.store,'s',True,'other',now=100)['wrong_firmware'])
        self.add(sample(firmware_id='FAKE_TEST',uptime_ms=200),session='s',monotonic=100)
        self.assertFalse(device_view(self.store,'s',True,now=100)['live'])
    def test_duplicates_do_not_refresh_time(self):
        self.assertTrue(self.add(session='s',monotonic=100))
        self.assertFalse(self.add(session='s',monotonic=200))
        self.assertFalse(device_view(self.store,'s',True,now=200)['live'])
    def test_invalid_message_does_not_replace_good_data(self):
        self.add()
        for body in [b'{}',b'[]',sample(state='SAFE'),sample(pump_cmd='false'),sample(ai_level=True),sample(temperature_c=float('nan'))]:
            with self.assertRaises(ValueError):self.add(body)
        self.assertEqual(len(self.store.rows('telemetry')),1)
    def test_namespace_isolated(self):
        self.add()
        other=Store(self.store.path,'other/pccc')
        try:self.assertEqual(other.rows(),[])
        finally:other.close()

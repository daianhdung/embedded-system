"""Explicit simulated clock tests; no dependency on a live device or current UTC."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from wokwi_clock import WokwiClock

BASE=1793185775000

def telemetry(**changes):
    data=dict(record_type='TELEMETRY',mode='SIMULATION',firmware_id='R7-test',boot_id='boot-a',
              ts_ms=BASE-98000,wifi=True,mqtt=True,subscribed=True,clock_synced=True)
    data.update(changes)
    return json.dumps(data)


class WokwiClockTests(unittest.TestCase):
    def test_slow_clock_uses_device_time_preserves_source_utc(self):
        clock=WokwiClock('R7-test')
        clock.observe(telemetry(),now=10)
        row=clock.timestamp(BASE,BASE+50,10.05)
        self.assertEqual(row['ts_ms'],BASE-98000)
        self.assertEqual(row['source_utc_ms'],BASE)
        self.assertEqual(row['timestamp_domain'],'WOKWI_SIMULATED_UTC')
        # A PC clock 98s ahead is mapped; the original UTC parser is NOT changed.
        self.assertLessEqual(row['ts_ms'],BASE-98000+2000)

    def test_anchor_precedes_frame_even_when_new_telemetry_arrives_during_inference(self):
        clock=WokwiClock('R7-test');clock.observe(telemetry(),now=10)
        anchor=clock.sample.copy()
        clock.observe(telemetry(ts_ms=BASE-97000),now=11)
        self.assertEqual(clock.timestamp(BASE,BASE+1000,11,anchor)['ts_ms'],BASE-98000)

    def test_expired_frames_and_pc_clock_errors_rejected(self):
        for now in [BASE+15000,BASE-2001]:
            clock=WokwiClock('R7-test');clock.observe(telemetry(),now=10)
            with self.assertRaises(ValueError):clock.timestamp(BASE,now,10)

    def test_missing_and_stale_telemetry_do_not_generate_timestamp(self):
        clock=WokwiClock('R7-test')
        self.assertIsNone(clock.timestamp(BASE,BASE,10))
        clock.observe(telemetry(),now=10)
        self.assertIsNone(clock.timestamp(BASE,BASE,15.01))

    def test_same_anchor_cannot_refresh_ai(self):
        clock=WokwiClock('R7-test');clock.observe(telemetry(),now=10)
        self.assertIsNotNone(clock.timestamp(BASE,BASE,10))
        self.assertIsNone(clock.timestamp(BASE+1000,BASE+1000,11))
        self.assertFalse(clock.observe(telemetry(ts_ms=BASE-99000),now=11))
        clock.observe(telemetry(ts_ms=BASE-97000),now=11)
        self.assertIsNotNone(clock.timestamp(BASE+1000,BASE+1000,11))

    def test_retained_wrong_firmware_or_unsynced_samples_ignored(self):
        for changes in [dict(firmware_id='other'),dict(clock_synced=False),dict(mode='HARDWARE'),dict(ts_ms=True),dict(ts_ms=0),dict(subscribed=0)]:
            self.assertFalse(WokwiClock('R7-test').observe(telemetry(**changes),now=1))
        self.assertFalse(WokwiClock('R7-test').observe(telemetry(),retained=True,now=1))

    def test_restart_aborts_instead_of_mixing_sessions(self):
        clock=WokwiClock('R7-test');clock.observe(telemetry(),now=10)
        clock.observe(telemetry(boot_id='boot-b',ts_ms=BASE),now=11)
        with self.assertRaises(RuntimeError):clock.timestamp(BASE,BASE,11)

    def test_disconnect_invalidates_sample(self):
        clock=WokwiClock('R7-test');clock.observe(telemetry(),now=10)
        anchor=clock.sample.copy()
        clock.invalidate()
        self.assertIsNone(clock.timestamp(BASE,BASE,11,anchor))
        clock.observe(telemetry(ts_ms=BASE-97000),now=11)
        self.assertIsNone(clock.timestamp(BASE,BASE,11,anchor))

if __name__=='__main__':unittest.main()

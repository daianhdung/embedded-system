import csv
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import types
import argparse
import contextlib
import io

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ai_adapter import Prediction, prediction_from, detection_result
import s8_track

class AdapterTests(unittest.TestCase):
    def test_validation_and_unknown(self):
        self.assertIsNone(prediction_from(None))
        for value in [dict(label='fire',confidence=.9),dict(label='lua',confidence=True),dict(label='lua',confidence=float('nan')),dict(label='lua',confidence=2)]:
            with self.assertRaises(ValueError): prediction_from(value)
        self.assertEqual(Prediction('lua',.9).packet(1793152800000)['nhan'],'lua')
        self.assertIsNone(detection_result([]))
        self.assertIsNone(detection_result([dict(label='fire',confidence=.5)]))
        self.assertEqual(detection_result([dict(label='Smoke',confidence=.99),dict(label='Fire',confidence=.8)]).label,'lua')
    def test_replay_dry_run_no_publish_for_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'input.jsonl';source.write_text('{"label":"lua","confidence":0.9}\nnull\n')
            completed=subprocess.run([sys.executable,str(ROOT/'tools/ai_publish.py'),'--dry-run','--input',str(source),'--interval','0.1'],capture_output=True,text=True,check=True)
            rows=[json.loads(line) for line in completed.stdout.splitlines()]
            self.assertEqual(sum(r['event']=='DRY_RUN' for r in rows),1)
            self.assertEqual(sum(r['event']=='UNAVAILABLE' for r in rows),1)
            self.assertTrue(all(r['backend']=='REPLAY_MOCK' for r in rows))

    def test_camera_unavailable_does_not_produce_normal(self):
        from ai_publish import plugin_frames
        cap=types.SimpleNamespace(isOpened=lambda:False,release=lambda:released.append(True))
        released=[]
        with patch.dict(sys.modules,{'cv2':types.SimpleNamespace(VideoCapture=lambda source:cap)}):
            with self.assertRaises(RuntimeError): list(plugin_frames('0',lambda image:None))
        self.assertTrue(released)

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.path=self.root/'ledger.csv';self.evidence=self.root/'observed.log';self.evidence.write_text('UNIT TEST FIXTURE, not MCU evidence')
        with self.path.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=s8_track.FIELDS);writer.writeheader()
            for tc in range(1,14):
                for run in range(1,21): writer.writerow(dict(scenario_id=f'TC{tc:02}',run=run,status='NOT_RUN',expected='fixture'))
    def tearDown(self): self.temp.cleanup()
    def test_exact_schema(self):
        self.assertEqual(len(s8_track.read_ledger(self.path)),260)
        self.assertEqual(s8_track.summary(self.path)['TC11']['NOT_RUN'],20)
    def test_reject_mock_formal_pass_and_host_domain(self):
        before=self.path.read_bytes()
        for model,domain,tc in [('MOCK','WOKWI','TC06'),('NONE','WOKWI','TC11'),('real','HOST_SYNTHETIC','TC02')]:
            with self.assertRaises(ValueError):
                s8_track.record(self.path,tc,1,'PASS','fixture','R7-unit',model,self.evidence,domain,audit_dir=self.root/'audit')
        self.assertEqual(before,self.path.read_bytes())
    def test_single_record_and_audit(self):
        audit=s8_track.record(self.path,'TC02',1,'PASS','unit fixture observed','R7-unit','NONE',self.evidence,'WOKWI',audit_dir=self.root/'audit')
        self.assertEqual(s8_track.summary(self.path)['TC02']['PASS'],1)
        self.assertEqual(s8_track.summary(self.path)['TC03']['NOT_RUN'],20)
        self.assertEqual(json.loads(audit.read_text())['before']['status'],'NOT_RUN')
    def test_invalid_ledger(self):
        self.path.write_text('invalid,csv\n')
        with self.assertRaises(ValueError): s8_track.read_ledger(self.path)
    def test_capture_invariants_no_auto_pass(self):
        capture=self.root/'capture.jsonl'
        q=dict(record_type='TELEMETRY',firmware_id='FAKE_UNIT',boot_id='unit',state='NORMAL',pump_cmd=True,local_level=0,ai_level=0,merged_level=2)
        capture.write_text(json.dumps(dict(kind='device',payload=q))+'\n')
        result=s8_track.capture_summary(capture)
        self.assertEqual(len(result['data_invariant_violations']),2)
        self.assertNotIn('PASS',result)

class RunnerTests(unittest.TestCase):
    def test_missing_command_cannot_be_reported_pass(self):
        import verify_project
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'report'
            args=argparse.Namespace(out=out,broker_smoke=False)
            with patch('argparse.ArgumentParser.parse_args',return_value=args), patch('subprocess.run',side_effect=OSError('unit missing command')), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit): verify_project.main()
            report=json.loads((out/'report.json').read_text())
            self.assertEqual(report['software_status'],'FAIL')
            self.assertIsNone(report['firmware_bin_sha256'])

if __name__=='__main__': unittest.main()

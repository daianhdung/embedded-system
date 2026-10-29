"""Configuration boundaries: no shell expansion; env/CLI override local defaults."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from runtime_config import read_env
ROOT=Path(__file__).resolve().parents[1]

class RuntimeConfigTests(unittest.TestCase):
    def test_literals_and_quotes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'.env'
            p.write_text('# comment\nPCCC_MQTT_PASSWORD="a # b $HOME $(echo bad)"\nEMPTY=\nPORT=1883 # note\n')
            values=read_env(p)
            self.assertEqual(values['PCCC_MQTT_PASSWORD'],'a # b $HOME $(echo bad)')
            self.assertEqual(values['EMPTY'],'')
            self.assertEqual(values['PORT'],'1883')
            p.write_text('BAD KEY=value')
            with self.assertRaises(ValueError):read_env(p)
    def test_environment_and_cli_override(self):
        env=dict(os.environ,PCCC_MQTT_HOST='override.invalid')
        p=subprocess.run([sys.executable,'-c','import sys;sys.path.insert(0,"tools");import runtime_config as c;print(c.MQTT_HOST)'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertEqual(p.stdout.strip(),'override.invalid')
        p=subprocess.run([sys.executable,'tools/ai_publish.py','--backend','replay','--dry-run','--interval','.1','--duration','.1'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('REPLAY_MOCK',p.stdout)

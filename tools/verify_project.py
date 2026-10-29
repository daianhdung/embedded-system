#!/usr/bin/env python3
"""One-command reproducible software checks. Does not execute Wokwi or models."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from s8_track import LEDGER

ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,help='New report directory, must not exist')
    p.add_argument('--broker-smoke',action='store_true',help='Requires optional amqtt test requirements')
    p.add_argument('--dashboard',action='store_true',help='Streamlit UI check; with broker-smoke also test MQTT->SQLite')
    a=p.parse_args()
    folder=(a.out or ROOT/'runs'/('checks-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    pio=shutil.which('pio') or str(Path.home()/'.platformio/penv/bin/pio')
    jobs=[('esp32-build',[pio,'run']),('host-core',[sys.executable,'test/run_host_tests.py']),
          ('python-tools',[sys.executable,'-m','unittest','discover','-s','test','-p','test_*.py']),
          ('s8-host-synthetic',[sys.executable,'tools/run_s8_host.py','--out',str(folder/'s8-host-synthetic.csv')])]
    if a.broker_smoke: jobs.append(('pc-localhost-broker-smoke',[sys.executable,'test/broker_smoke.py']))
    if getattr(a,'dashboard',False):
        jobs.append(('dashboard-ui',[sys.executable,'test/dashboard_ui_check.py']))
        if a.broker_smoke:jobs.append(('dashboard-localhost-broker',[sys.executable,'test/dashboard_smoke.py']))
    before=sha(LEDGER) if LEDGER.exists() else None
    report=dict(domain='SOFTWARE_CHECKS_NOT_ACCEPTANCE',started_utc=datetime.now(timezone.utc).isoformat(),
                formal_ledger=str(LEDGER),formal_ledger_before_sha256=before,stages=[],model='PRETRAINED_UNVERIFIED; these stages do not evaluate model metrics',
                runtime_wokwi='NOT_RUN',real_image_metrics='NOT_RUN')
    failed=False
    try:
        for name,command in jobs:
            start=time.monotonic();log=folder/(name+'.log')
            with log.open('w') as f:
                try:
                    completed=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
                    code=completed.returncode
                except OSError as error:
                    f.write(str(error)+'\n');code=127
            report['stages'].append(dict(name=name,status='PASS' if code==0 else 'FAIL',
                command=command,seconds=round(time.monotonic()-start,3),log=log.name,sha256=sha(log)))
            print(name+': '+report['stages'][-1]['status'],flush=True)
            if code: failed=True;break
    finally:
        report['formal_ledger_unchanged']=(sha(LEDGER)==before) if before else None
        if report['formal_ledger_unchanged'] is False: failed=True
        binary=ROOT/'.pio/build/esp32dev/firmware.bin'
        report['firmware_bin_sha256']=sha(binary) if binary.exists() and report['stages'] and report['stages'][0]['status']=='PASS' else None
        identity=ROOT/'.pio/generated/pccc_build_identity.h'
        report['firmware_identity_header']=identity.read_text() if identity.exists() else None
        report['completed_utc']=datetime.now(timezone.utc).isoformat()
        if len(report['stages'])!=len(jobs): failed=True
        report['software_status']='FAIL' if failed else 'PASS'
        tracked=list((ROOT/'dashboard').glob('*.py'))+[ROOT/'platformio.ini']+[file for file in (ROOT/'include').glob('*.h') if file.name!='secrets.h']+list((ROOT/'scripts').glob('*.py'))+list((ROOT/'src').glob('*.cpp'))+list((ROOT/'tools').glob('*.py'))+list((ROOT/'test').glob('*.py'))+list((ROOT/'test/host').glob('*.cpp'))
        report['source_sha256']={str(file.relative_to(ROOT)):sha(file) for file in sorted(tracked)}
        (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Report: '+str(folder/'report.json'))
    print('Formal260runs, real model and Wokwi checks are not marked PASS.')
    if failed: raise SystemExit(1)
if __name__=='__main__': main()

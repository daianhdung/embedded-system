#!/usr/bin/env python3
"""One canonical260-run acceptance ledger; mock/host results stay separate."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import fcntl
import json
from pathlib import Path
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT.parent/'tests/integration-results.csv'
FIELDS=['scenario_id','run','status','expected','observed','firmware_version','model_version','evidence_path','notes']
MODEL_CASES={'TC01','TC06','TC08','TC10','TC11'}


def read_ledger(path):
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS: raise ValueError('unexpected ledger schema')
        rows=list(reader)
    keys=[(r['scenario_id'],int(r['run'])) for r in rows]
    expected={(f'TC{i:02}',run) for i in range(1,14) for run in range(1,21)}
    if len(keys)!=260 or set(keys)!=expected: raise ValueError('ledger must contain exactly13TC x20 unique runs')
    if any(r['status'] not in {'NOT_RUN','PASS','FAIL','BLOCKED'} for r in rows): raise ValueError('unknown status')
    return rows


def summary(path):
    rows=read_ledger(path)
    return {case:{status:sum(r['scenario_id']==case and r['status']==status for r in rows)
                  for status in ('NOT_RUN','PASS','FAIL','BLOCKED')} for case in sorted({r['scenario_id'] for r in rows})}


def record(path,scenario,run,status,observed,firmware,model,evidence,domain,notes='',audit_dir=None):
    path=Path(path)
    with path.with_suffix(path.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _record_locked(path,scenario,run,status,observed,firmware,model,evidence,domain,notes,audit_dir)


def _record_locked(path,scenario,run,status,observed,firmware,model,evidence,domain,notes,audit_dir):
    path=Path(path);rows=read_ledger(path)
    if status not in {'PASS','FAIL','BLOCKED'}: raise ValueError('record status must be PASS/FAIL/BLOCKED')
    if domain not in {'WOKWI','HARDWARE'}: raise ValueError('host/mock executions cannot enter formal acceptance ledger')
    if not observed.strip() or not firmware.strip(): raise ValueError('observed and actual firmware identity required')
    evidence=Path(evidence).resolve()
    if not evidence.is_file(): raise ValueError('evidence file does not exist')
    if evidence.suffix.lower() not in {'.txt','.log','.jsonl','.png','.jpg','.jpeg','.mp4','.webm'}:
        raise ValueError('provide runtime log/image/video, not synthetic resultCSV')
    if status=='PASS' and scenario in MODEL_CASES:
        name=model.upper()
        if not name or any(token in name for token in ('MOCK','NONE','DEFERRED','UNVERIFIED','HOST')):
            raise ValueError('model-dependent acceptance cannot PASS with mock/absent/unverified model')
    if status=='PASS' and evidence.suffix.lower()=='.jsonl':
        captured=capture_summary(evidence)
        if captured['missing_identity'] or captured['fixture_records'] or captured['firmware_ids']!=[firmware]:
            raise ValueError('capture identity missing/mismatched or contains PC/host fixture')
        if scenario in MODEL_CASES and captured['declared_backend']!='REAL_MODEL':
            raise ValueError('model-dependent PASS requires capture declared REAL_MODEL, not mock')
    match=[r for r in rows if r['scenario_id']==scenario and int(r['run'])==run]
    if not match: raise ValueError('unknown scenario/run')
    previous=match[0].copy()
    updated=dict(previous,status=status,observed=observed,firmware_version=firmware,
                 model_version=model,evidence_path=str(evidence),notes=f'[{domain}] '+notes)
    audit_dir=Path(audit_dir or ROOT/'docs/evidence/acceptance-audit')
    audit_dir.mkdir(parents=True,exist_ok=True)
    audit_path=audit_dir/(uuid.uuid4().hex+'.json')
    original=path.read_bytes()
    audit=dict(applied=False,recorded_utc=datetime.now(timezone.utc).isoformat(),domain=domain,
               ledger=str(path.resolve()),ledger_before_sha256=hashlib.sha256(original).hexdigest(),
               evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),before=previous,after=updated,
               note='Operator-supplied observation; this tool cannot certify its physical truth.')
    # Exclusive audit creation and optimistic hash check prevent silent overwrites.
    with audit_path.open('x') as f: json.dump(audit,f,indent=2)
    match[0].update(updated)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False,newline='') as f:
        temporary=Path(f.name);writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(rows)
    if path.read_bytes()!=original:
        temporary.unlink();raise RuntimeError('ledger changed concurrently; retry after reviewing audit')
    temporary.replace(path)
    audit['applied']=True; audit['ledger_after_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    audit_path.write_text(json.dumps(audit,indent=2)+'\n')
    return audit_path


def capture_summary(path):
    payloads=[];ids=set();boots=set();states=set();violations=[];max_gap=0;metadata=None;fixtures=0
    with Path(path).open() as f:
        for line in f:
            row=json.loads(line)
            if row.get('kind')=='metadata': metadata=row
            q=row.get('payload')
            if row.get('kind')!='device' or not isinstance(q,dict) or q.get('record_type') not in {'TELEMETRY','EVENT'}: continue
            if q.get('fixture_not_mcu') or str(q.get('firmware_id','')).upper().startswith(('HOST','FAKE','MOCK')): fixtures+=1
            payloads.append(q);ids.add(q.get('firmware_id','MISSING'));boots.add(q.get('boot_id','MISSING'));states.add(q.get('state','MISSING'))
            if isinstance(q.get('max_loop_gap_ms'),(int,float)): max_gap=max(max_gap,q['max_loop_gap_ms'])
            if all(type(q.get(k)) is int for k in ('local_level','ai_level','merged_level')):
                if q['merged_level']!=max(q['local_level'],q['ai_level']): violations.append('merged level mismatch')
            if q.get('state') in {'NORMAL','RECOVERY','WARNING'} and (q.get('pump_cmd') or q.get('valve_cmd')):
                violations.append('loads on outside FIRE')
            if q.get('state')=='NORMAL' and q.get('door_open_cmd'): violations.append('door open in NORMAL')
    expected=metadata.get('expected_firmware_id','UNSPECIFIED') if metadata else 'UNSPECIFIED'
    mismatch=expected!='UNSPECIFIED' and ids!={expected}
    return dict(domain='MQTT_OBSERVATION_NOT_ACCEPTANCE',records=len(payloads),firmware_ids=sorted(ids),expected_firmware_mismatch=mismatch,
                boot_ids=sorted(boots),fixture_records=fixtures,states=sorted(states),max_loop_gap_ms=max_gap,
                missing_identity=not payloads or 'MISSING' in ids or 'MISSING' in boots or '' in boots,
                declared_backend=metadata.get('ai_backend_declared_by_operator') if metadata else None,
                declared_clock_domain=metadata.get('ai_clock_domain_declared_by_operator','UNSPECIFIED') if metadata else None,
                data_invariant_violations=violations,
                note='No automatic PASS. Compare test inputs, actual outputs/images and expected behavior.')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    status=sub.add_parser('status');status.add_argument('--ledger',type=Path,default=LEDGER)
    cap=sub.add_parser('capture-summary');cap.add_argument('--capture',type=Path,required=True)
    rec=sub.add_parser('record');rec.add_argument('--ledger',type=Path,default=LEDGER)
    rec.add_argument('--scenario',required=True);rec.add_argument('--run',type=int,required=True)
    rec.add_argument('--status',choices=['PASS','FAIL','BLOCKED'],required=True)
    rec.add_argument('--observed',required=True);rec.add_argument('--firmware',required=True)
    rec.add_argument('--model',default='NONE');rec.add_argument('--evidence',type=Path,required=True)
    rec.add_argument('--domain',choices=['WOKWI','HARDWARE'],required=True);rec.add_argument('--notes',default='')
    a=p.parse_args()
    if a.command=='status':
        result=summary(a.ledger)
        print('TC    PASS FAIL BLOCKED NOT_RUN')
        for case,counts in result.items():
            print(f"{case}  {counts['PASS']:4} {counts['FAIL']:4} {counts['BLOCKED']:7} {counts['NOT_RUN']:7}")
        print('Formal acceptance ledger; host/mock results are stored separately.')
    elif a.command=='capture-summary': print(json.dumps(capture_summary(a.capture),indent=2))
    else: print(record(a.ledger,a.scenario,a.run,a.status,a.observed,a.firmware,a.model,a.evidence,a.domain,a.notes))

if __name__=='__main__': main()

#!/usr/bin/env python3
"""Prepare a reviewable source/evidence ZIP. No publishing, no secrets, no fake report."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile
from s8_track import LEDGER,summary

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','.pio','.venv','.venv-ai','.host-build','__pycache__','runs','node_modules'}


def package(out,include_weights=False,report=None):
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    files={}
    for folder in ('src','include','scripts','tools','dashboard','test','docs','models'):
        for path in (ROOT/folder).rglob('*'):
            rel=path.relative_to(ROOT)
            if (not path.is_file() or path.is_symlink() or any(part in EXCLUDED for part in rel.parts)
                or path.name in ('secrets.h','.env') or path.suffix in ('.pyc','.sqlite','.sqlite3','.db')):continue
            if folder=='models' and path.suffix in ('.pt','.pth','.onnx') and not include_weights:continue
            files[str(rel)]=path
    for name in ('.env.example','README.md','platformio.ini','diagram.json','wokwi.toml','PCCC.code-workspace','.gitignore'):
        files[name]=ROOT/name
    if LEDGER.exists():files['acceptance/integration-results.csv']=LEDGER
    if report:
        report=Path(report).resolve()
        if not report.is_file() or report.suffix.lower() not in ('.docx','.pdf'):raise ValueError('actual DOCX/PDF report required')
        files['report/'+report.name]=report
    counts=summary(LEDGER) if LEDGER.exists() else None
    manifest=dict(status='REVIEW_BUNDLE_NOT_ACCEPTANCE_CERTIFICATE',created_utc=datetime.now(timezone.utc).isoformat(),
        report_included=bool(report),weights_included=include_weights,formal_acceptance=counts,
        warnings=['Report deferred until acceptance','Local camera data/runs/credentials excluded','Check dataset/model license and lecturer submission requirements'],
        files={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files.items())})
    # Open exclusively: never overwrite a previous submission artifact.
    with out.open('xb') as handle:
        with zipfile.ZipFile(handle,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,path in sorted(files.items()):archive.write(path,'PCCC/'+name)
            archive.writestr('PCCC/bundle-manifest.json',json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--include-weights',action='store_true');p.add_argument('--report',type=Path)
    a=p.parse_args();result=package(a.out,a.include_weights,a.report)
    print(f'Prepared {len(result["files"])} files: {a.out}; review manifest, not automatic acceptance PASS.')
if __name__=='__main__':main()

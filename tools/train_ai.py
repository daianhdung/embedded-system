#!/usr/bin/env python3
"""Explicit fine-tune entrypoint; requires real audited data. Never runs at import."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from evaluate_ai import audit_manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--data',type=Path,required=True,help='YOLO data YAML with boxes, not image-level labels')
    p.add_argument('--weights',type=Path,default=Path('models/fire-smoke-yolov8n.pt'))
    p.add_argument('--epochs',type=int,default=50);p.add_argument('--device',default='cpu');p.add_argument('--out',type=Path)
    a=p.parse_args()
    if not 1<=a.epochs<=500:p.error('epochs must be 1..500')
    doc,samples,counts=audit_manifest(a.manifest)
    if any(not counts.get(split) for split in ('train','val','test')):p.error('train/val/test splits required')
    if not a.data.is_file() or not a.weights.is_file():p.error('YOLO data YAML and weights must exist')
    import yaml
    config_data=yaml.safe_load(a.data.read_text())
    names=config_data.get('names')
    ordered=list(names.values()) if isinstance(names,dict) else names
    if ordered!=['smoke','fire']:p.error('YOLO class IDs must be 0=smoke, 1=fire for these weights')
    dataset_root=(a.data.parent/config_data.get('path','.')).resolve()
    for split in ('train','val','test'):
        location=config_data.get(split)
        if not isinstance(location,str) or not (dataset_root/location).is_dir():
            p.error('This reproducible trainer requires train/val/test directory paths in YAML')
        actual={path.resolve() for path in (dataset_root/location).rglob('*') if path.suffix.lower() in ('.jpg','.jpeg','.png','.webp','.bmp')}
        audited={Path(sample['path']) for sample in samples if sample['split']==split}
        if actual!=audited:p.error('YOLO YAML image set does not match audited manifest split: '+split)
    folder=a.out or Path('runs')/('ai-train-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    config=dict(dataset_id=doc['dataset_id'],manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
                data_yaml_sha256=hashlib.sha256(a.data.read_bytes()).hexdigest(),
                initial_weights_sha256=hashlib.sha256(a.weights.read_bytes()).hexdigest(),epochs=a.epochs,
                seed=42,imgsz=640,device=a.device,
                note='Image-manifest audit does not prove YOLO YAML/box consistency; inspect annotation provenance and split alignment before training.')
    (folder/'run-config.json').write_text(json.dumps(config,indent=2)+'\n')
    from ultralytics import YOLO
    model=YOLO(str(a.weights))
    model.train(data=str(a.data.resolve()),epochs=a.epochs,imgsz=640,seed=42,device=a.device,project=str(folder.resolve()),name='training')
    print('Training finished. Independently evaluate test split; do not copy train/val metrics as system acceptance.')
if __name__=='__main__':main()

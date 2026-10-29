#!/usr/bin/env python3
"""Audit labeled images and evaluate image-level fire/smoke decisions. No MQTT."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time

LABELS=('lua','khoi','binh_thuong')

def audit_manifest(path):
    path=Path(path).resolve();doc=json.loads(path.read_text())
    if doc.get('v')!=1 or not all(isinstance(doc.get(k),str) and doc[k].strip() for k in ('dataset_id','source','license')):
        raise ValueError('dataset v1/id/source/license required')
    if any(token in str(doc[k]).upper() for k in ('dataset_id','source','license') for token in ('REPLACE','TODO','UNKNOWN')):
        raise ValueError('replace dataset provenance/license placeholders with real values')
    samples=doc.get('samples')
    if not isinstance(samples,list) or not samples:raise ValueError('no labeled samples; do not fabricate a dataset')
    groups={};hash_splits={};seen=set();counts=defaultdict(Counter);validated=[]
    for sample in samples:
        label=sample.get('label');split=sample.get('split');group=sample.get('group')
        if label not in LABELS or split not in ('train','val','test') or not isinstance(group,str) or not group.strip():
            raise ValueError('sample needs valid label, split and source/video group')
        image=(path.parent/sample['path']).resolve()
        if image in seen:raise ValueError('duplicate image path')
        if not image.is_file():raise ValueError(f'missing image: {image}')
        if image.suffix.lower() not in ('.jpg','.jpeg','.png','.webp','.bmp'):raise ValueError('image expected')
        digest=hashlib.sha256(image.read_bytes()).hexdigest()
        if group in groups and groups[group]!=split:raise ValueError('video/source group leaks across splits')
        if digest in hash_splits and hash_splits[digest]!=split:raise ValueError('duplicate image content leaks across splits')
        groups[group]=split;hash_splits[digest]=split;seen.add(image);counts[split][label]+=1
        validated.append(dict(sample,path=str(image),sha256=digest))
    return doc,validated,dict(counts)


def image_metrics(rows):
    confusion={truth:{pred:0 for pred in (*LABELS,'unknown')} for truth in LABELS}
    for row in rows:confusion[row['truth']][row['prediction']]+=1
    scores={}
    for label in LABELS:
        tp=confusion[label][label];actual=sum(confusion[label].values())
        predicted=sum(confusion[t][label] for t in LABELS)
        scores[label]=dict(precision=tp/predicted if predicted else None,recall=tp/actual if actual else None,support=actual)
    normal=sum(confusion['binh_thuong'].values())
    false_alarm=confusion['binh_thuong']['lua']+confusion['binh_thuong']['khoi']
    return dict(confusion=confusion,per_class=scores,samples=len(rows),
                coverage=sum(r['prediction']!='unknown' for r in rows)/len(rows) if rows else None,
                background_false_alarm_rate=false_alarm/normal if normal else None,
                note='Detector no-box is unknown, not binh_thuong. Image-level metrics are not bounding-box mAP or system acceptance.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--audit-only',action='store_true')
    p.add_argument('--split',choices=['val','test'],default='test')
    p.add_argument('--weights',type=Path,default=Path('models/fire-smoke-yolov8n.pt'))
    p.add_argument('--device',default='cpu');p.add_argument('--threshold',type=float,default=.8)
    p.add_argument('--out',type=Path);a=p.parse_args()
    doc,samples,counts=audit_manifest(a.manifest)
    report=dict(domain='DATASET_AUDIT' if a.audit_only else 'PROVIDED_IMAGE_EVALUATION_NOT_ACCEPTANCE',
                dataset_id=doc['dataset_id'],source=doc['source'],license=doc['license'],counts=counts,
                manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
                independent_from_pretrained_training=doc.get('independent_from_pretrained_training') is True,
                requirement_200_per_class_met=all(sum(c.get(label,0) for c in counts.values())>=200 for label in LABELS),
                evaluated=False)
    folder=a.out or Path('runs')/('ai-eval-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'audited-manifest.json').write_text(json.dumps(dict(doc,samples=samples),indent=2)+'\n')
    if not a.audit_only:
        from yolo_plugin import YoloDetector
        import cv2
        detector=YoloDetector(a.weights,a.device,view_conf=min(.25,a.threshold),threshold=a.threshold)
        rows=[]
        for sample in samples:
            if sample['split']!=a.split:continue
            image=cv2.imread(sample['path'])
            if image is None:raise ValueError('unreadable image: '+sample['path'])
            start=time.perf_counter();obs=detector.observe(image);elapsed=(time.perf_counter()-start)*1000
            prediction=obs.prediction
            rows.append(dict(path=sample['path'],truth=sample['label'],prediction=prediction.label if prediction else 'unknown',
                             confidence=prediction.confidence if prediction else None,inference_ms=round(elapsed,3),sha256=sample['sha256']))
        if not rows:raise ValueError('selected split has no samples')
        report.update(evaluated=True,split=a.split,weights_sha256=detector.sha256,threshold=a.threshold,
                      metrics=image_metrics(rows),device=a.device,temporal_filter=False,
                      timing_note='First image includes warmup; PC inference only, not end-to-end latency')
        (folder/'predictions.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));print('Report:',folder/'report.json')
if __name__=='__main__':main()

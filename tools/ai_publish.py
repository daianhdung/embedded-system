#!/usr/bin/env python3
"""S7 shell: replay mock now, plug in a real image model later."""
import argparse
import importlib
import json
import math
from pathlib import Path
import sys
import time
from ai_adapter import prediction_from
from mqtt_transport import MqttTransport
from mqtt_mock import DEFAULT_PREFIX


def replay_frames(path):
    with Path(path).open() as f:
        for line in f:
            if line.strip(): yield int(time.time()*1000), json.loads(line)


def plugin_frames(source, plugin):
    import cv2  # optional: installed only for real video/camera mode
    cap=cv2.VideoCapture(int(source) if source.isdigit() else source)
    try:
        if not cap.isOpened(): raise RuntimeError('camera/video unavailable')
        while True:
            ok,frame=cap.read()
            if not ok: return # stream ended/lost: stop publishing; ESP TTL handles loss
            captured=int(time.time()*1000)
            yield captured,plugin(frame) # BGR image; preprocessing belongs to plugin
    finally: cap.release()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend',choices=['replay','plugin'],default='replay')
    p.add_argument('--input',default=str(Path(__file__).with_name('examples')/'ai-replay.jsonl'))
    p.add_argument('--source',default='0')
    p.add_argument('--plugin',help='module:function; receives BGR frame, returns None or {label,confidence}')
    p.add_argument('--model-id',default='REPLAY_MOCK')
    p.add_argument('--plugin-path',type=Path,default=Path.cwd())
    p.add_argument('--host',default='broker.hivemq.com');p.add_argument('--port',type=int,default=1883)
    p.add_argument('--prefix',default=DEFAULT_PREFIX)
    p.add_argument('--interval',type=float,default=2)
    p.add_argument('--duration',type=float,default=0)
    p.add_argument('--dry-run',action='store_true',help='No MQTT; print publishable packets only')
    p.add_argument('--log',type=Path,help='New JSONL log, exclusive creation')
    a=p.parse_args()
    if not math.isfinite(a.interval) or not math.isfinite(a.duration) or a.interval<0.1 or a.duration<0: p.error('interval>=0.1 and duration>=0')
    if a.backend=='plugin' and (not a.plugin or a.model_id=='REPLAY_MOCK'):
        p.error('plugin backend requires --plugin and --model-id; no model is bundled')
    backend='REPLAY_MOCK' if a.backend=='replay' else 'PLUGIN_UNVERIFIED'
    if a.backend=='replay':
        frames=replay_frames(a.input)
    else:
        sys.path.insert(0,str(a.plugin_path.resolve()))
        module,func=a.plugin.rsplit(':',1)
        plugin=getattr(importlib.import_module(module),func)
        frames=plugin_frames(a.source,plugin)
    log=a.log.open('x') if a.log else None
    transport=None
    start=time.monotonic(); last_ts=0
    def emit(event,**fields):
        record=dict(event=event,backend=backend,model_id=a.model_id,utc_ms=int(time.time()*1000),**fields)
        text=json.dumps(record,allow_nan=False);print(text,flush=True)
        if log: log.write(text+'\n');log.flush()
    try:
        if not a.dry_run:
            transport=MqttTransport(a.host,a.port,a.prefix).__enter__()
        emit('START',dry_run=a.dry_run)
        for captured,value in frames:
            if a.duration and time.monotonic()-start>=a.duration: break
            result=prediction_from(value)
            now=int(time.time()*1000)
            if result is None: emit('UNAVAILABLE',published=False)
            elif captured<=last_ts or now-captured>=15000 or captured-now>2000:
                emit('STALE_OR_CLOCK_ERROR',published=False)
            else:
                packet=result.packet(captured)
                if transport: transport.publish(json.dumps(packet,separators=(',',':'),allow_nan=False))
                last_ts=captured
                emit('DRY_RUN' if a.dry_run else 'PUBACK',packet=packet)
            time.sleep(a.interval)
        emit('STOP',reason='source ended or duration reached; no normal fallback')
    except KeyboardInterrupt: emit('STOP',reason='operator')
    except Exception as error:
        emit('ERROR',message=str(error),published=False)
        raise
    finally:
        if transport: transport.close()
        if log: log.close()

if __name__=='__main__': main()

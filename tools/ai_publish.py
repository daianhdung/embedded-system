#!/usr/bin/env python3
"""S7 shell: replay mock now, plug in a real image model later."""
from runtime_config import MQTT_HOST, MQTT_PORT, TOPIC_PREFIX, setting

import argparse
import importlib
import json
import math
from pathlib import Path
import sys
import time
import uuid
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
    p.add_argument('--backend',choices=['local','replay','plugin'],default=setting('PCCC_AI_BACKEND','local'))
    p.add_argument('--input',default=str(Path(__file__).with_name('examples')/'ai-replay.jsonl'))
    p.add_argument('--source',default=setting('PCCC_AI_SOURCE','0'))
    p.add_argument('--plugin',default=setting('PCCC_AI_PLUGIN','yolo_plugin:predict'),help='module:function; receives BGR frame, returns None or {label,confidence}')
    p.add_argument('--model-id',default=setting('PCCC_AI_MODEL_ID','rabahdev-fire-smoke-yolov8n-13017fe8'))
    p.add_argument('--plugin-path',type=Path,default=Path.cwd())
    p.add_argument('--host',default=MQTT_HOST);p.add_argument('--port',type=int,default=MQTT_PORT)
    p.add_argument('--prefix',default=DEFAULT_PREFIX)
    p.add_argument('--interval',type=float,default=2)
    p.add_argument('--duration',type=float,default=0)
    p.add_argument('--dry-run',action='store_true',help='No MQTT; print publishable packets only')
    p.add_argument('--log',type=Path,help='New JSONL log, exclusive creation')
    p.add_argument('--wokwi-clock',action='store_true',help='SIMULATION ONLY: map timestamps using fresh ESP telemetry; preserve source UTC in logs')
    p.add_argument('--expected-firmware-id',default=setting('PCCC_EXPECTED_FIRMWARE_ID'),help='Required with --wokwi-clock; copy exact identity from ESP boot')
    p.add_argument('--confirm-seconds',type=float,default=0,help='Opt-in temporal confirmation; 0 keeps per-frame behavior')
    p.add_argument('--confirm-frames',type=int,default=3)
    p.add_argument('--confirm-max-gap',type=float,default=5)
    a=p.parse_args()
    if a.backend=='local':
        a.backend='plugin';a.plugin='yolo_plugin:predict'
    if a.backend=='replay': a.model_id='REPLAY_MOCK'
    if not math.isfinite(a.interval) or not math.isfinite(a.duration) or a.interval<0.1 or a.duration<0: p.error('interval>=0.1 and duration>=0')
    if a.backend=='plugin' and (not a.plugin or a.model_id=='REPLAY_MOCK'):
        p.error('plugin backend requires --plugin and --model-id; no model is bundled')
    if a.wokwi_clock and (a.dry_run or not a.expected_firmware_id):
        p.error('--wokwi-clock requires a live broker and --expected-firmware-id')
    from temporal_filter import TemporalGate
    try: gate=TemporalGate(a.confirm_seconds,a.confirm_frames,a.confirm_max_gap)
    except ValueError as error: p.error(str(error))
    if a.confirm_seconds and (a.backend!='plugin' or a.plugin.endswith(':predict_raw')):
        p.error('Temporal confirmation requires model plugin; raw diagnostics/replay keep original behavior')
    backend='REPLAY_MOCK' if a.backend=='replay' else 'PLUGIN_UNVERIFIED'
    if a.backend=='replay':
        frames=replay_frames(a.input)
    else:
        sys.path.insert(0,str(a.plugin_path.resolve()))
        module,func=a.plugin.rsplit(':',1)
        plugin=getattr(importlib.import_module(module),func)
        frames=plugin_frames(a.source,plugin)
    log=a.log.open('x') if a.log else None
    clock=None
    if a.wokwi_clock:
        from wokwi_clock import WokwiClock
        clock=WokwiClock(a.expected_firmware_id)
    transport=None
    start=time.monotonic(); last_ts=0
    publisher_id=uuid.uuid4().hex
    def emit(event,**fields):
        record=dict(event=event,backend=backend,model_id=a.model_id,publisher_id=publisher_id,
                    timestamp_domain='WOKWI_SIMULATED_UTC' if clock else 'UTC',
                    utc_ms=int(time.time()*1000),**fields)
        text=json.dumps(record,allow_nan=False);print(text,flush=True)
        if log: log.write(text+'\n');log.flush()
        if transport and transport.ready.is_set():
            transport.publish_status(text)
    try:
        if not a.dry_run:
            transport=MqttTransport(a.host,a.port,a.prefix)
            if clock:
                transport.watch_topic=a.prefix+'/device/esp32-01/telemetry'
                def observe_clock(c,u,m):
                    if len(m.payload)<=4096:
                        clock.observe(m.payload, retained=m.retain)
                transport.client.on_message=observe_clock
                original_disconnect=transport.client.on_disconnect
                def disconnected(c,u,flags,reason,props):
                    clock.invalidate()
                    original_disconnect(c,u,flags,reason,props)
                transport.client.on_disconnect=disconnected
            transport.client.will_set(a.prefix+'/ai/status',json.dumps(dict(event='OFFLINE',backend=backend,model_id=a.model_id,publisher_id=publisher_id)),qos=0,retain=False)
            transport.__enter__()
            if clock and not transport.subscribed.wait(5):
                raise RuntimeError('Wokwi telemetry subscription timed out')
        emit('START',dry_run=a.dry_run, expected_firmware_id=a.expected_firmware_id,
             filter_policy=dict(confirm_seconds=a.confirm_seconds,confirm_frames=a.confirm_frames,max_gap=a.confirm_max_gap))
        if clock:
            emit('SIMULATION_CLOCK_MODE',note='Not hardware UTC; TTL on ESP uses simulated seconds. Waiting for live matching telemetry.')
        frames=iter(frames)
        while True:
            if a.duration and time.monotonic()-start>=a.duration: break
            anchor=clock.wait_anchor() if clock else None
            try:
                captured,value=next(frames)
            except StopIteration:
                break
            result=prediction_from(value)
            candidate=result
            source_now=int(time.time()*1000)
            if captured<=last_ts or source_now-captured>=15000 or captured-source_now>2000:
                gate.update(None,time.monotonic())
                emit('STALE_OR_CLOCK_ERROR',published=False)
                time.sleep(a.interval)
                continue
            result=gate.update(result,time.monotonic())
            if a.confirm_seconds and candidate is not None and result is None:
                emit('CONFIRMING',published=False,label=candidate.label,confidence=candidate.confidence)
                time.sleep(a.interval)
                continue
            now=int(time.time()*1000)
            if result is None: emit('UNAVAILABLE',published=False)
            elif captured<=last_ts or now-captured>=15000 or captured-now>2000:
                emit('STALE_OR_CLOCK_ERROR',published=False)
            else:
                mapping=None
                if clock:
                    with clock.condition:
                        mapping=clock.timestamp(captured,int(time.time()*1000),time.monotonic(),anchor)
                    if mapping is None:
                        emit('WOKWI_CLOCK_EXPIRED',published=False)
                        time.sleep(a.interval)
                        continue
                packet=result.packet(mapping['ts_ms'] if mapping else captured)
                if transport: transport.publish(json.dumps(packet,separators=(',',':'),allow_nan=False))
                last_ts=captured
                emit('DRY_RUN' if a.dry_run else 'PUBACK',packet=packet, clock_mapping=mapping,
                     firmware_confidence_threshold_hint=0.8,
                     meets_confidence_threshold=packet['do_tin_cay']>=0.8)
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

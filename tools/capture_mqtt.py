#!/usr/bin/env python3
"""Capture MQTT observations to a new JSONL file; never marks acceptance PASS."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import uuid
from mqtt_transport import MqttTransport
from mqtt_mock import DEFAULT_PREFIX


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=60)
    p.add_argument('--host',default='broker.hivemq.com');p.add_argument('--port',type=int,default=1883)
    p.add_argument('--prefix',default=DEFAULT_PREFIX)
    p.add_argument('--expected-firmware-id',default='UNSPECIFIED')
    p.add_argument('--ai-backend',choices=['MOCK','MODEL_UNVERIFIED','REAL_MODEL'],default='MOCK')
    p.add_argument('--ai-clock-domain',choices=['UTC','WOKWI_SIMULATED_UTC'],default='UTC',help='Operator-declared publisher clock domain; not proof of runtime')
    a=p.parse_args()
    if not 0<a.duration<=86400: p.error('duration must be in(0,86400] seconds')
    run_id=uuid.uuid4().hex
    lock=threading.Lock(); count=0
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x') as f:
        def write(kind,**fields):
            nonlocal count
            row=dict(kind=kind,run_id=run_id,received_utc=datetime.now(timezone.utc).isoformat(),
                     monotonic_ns=time.monotonic_ns(),**fields)
            with lock:
                f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();count+=1
        write('metadata',domain='MQTT_OBSERVATION_NOT_ACCEPTANCE',host=a.host,port=a.port,
              prefix=a.prefix,expected_firmware_id=a.expected_firmware_id,
              ai_backend_declared_by_operator=a.ai_backend,
              ai_clock_domain_declared_by_operator=a.ai_clock_domain)
        transport=MqttTransport(a.host,a.port,a.prefix)
        transport.watch_topic=a.prefix+'/device/esp32-01/+'
        original_connect=transport.client.on_connect
        original_disconnect=transport.client.on_disconnect
        def connected(c,u,flags,reason,props):
            original_connect(c,u,flags,reason,props)
            write('connection',connected=not reason.is_failure,reason=str(reason))
        def disconnected(c,u,flags,reason,props):
            original_disconnect(c,u,flags,reason,props)
            write('connection',connected=False,reason=str(reason))
        def message(c,u,m):
            text=m.payload[:4096].decode('utf-8',errors='replace')
            if len(m.payload)>4096:
                write('invalid',topic=m.topic,error='payload exceeds4096bytes');return
            try:
                data=json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            except ValueError:
                write('non_json',topic=m.topic,payload_text=text,retained=m.retain);return
            write('device',topic=m.topic,retained=m.retain,qos=m.qos,payload=data)
        transport.client.on_connect=connected
        transport.client.on_disconnect=disconnected
        transport.client.on_message=message
        try:
            with transport:
                if not transport.subscribed.wait(5): raise RuntimeError('SUBACK timed out')
                print('[CAPTURE ready] '+str(a.out),flush=True)
                end=time.monotonic()+a.duration
                while time.monotonic()<end: time.sleep(0.1)
        except KeyboardInterrupt: write('stop',reason='operator')
        except Exception as error:
            write('error',message=str(error));raise
        finally: write('end',records_before_end=count)
    print('Saved observations; no test automatically marked PASS.',flush=True)

if __name__=='__main__': main()

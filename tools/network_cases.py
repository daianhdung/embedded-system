#!/usr/bin/env python3
"""Bounded, explicit MQTT protocol probes. Operator runs Wokwi/capture concurrently."""
from runtime_config import MQTT_HOST, MQTT_PORT, TOPIC_PREFIX, setting

import argparse
import json
import time
from mqtt_mock import DEFAULT_PREFIX,payload_for
from mqtt_transport import MqttTransport
from wokwi_clock import WokwiClock


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=['valid','json','missing','type','confidence','old','future','duplicate','oversize','retained','clear-retained','flood'],required=True)
    p.add_argument('--host',default=MQTT_HOST);p.add_argument('--port',type=int,default=MQTT_PORT)
    p.add_argument('--prefix',default=DEFAULT_PREFIX);p.add_argument('--wokwi-clock',action='store_true')
    p.add_argument('--expected-firmware-id');p.add_argument('--count',type=int,default=1)
    a=p.parse_args()
    if not 1<=a.count<=64:p.error('count must be 1..64')
    if a.wokwi_clock and not a.expected_firmware_id:p.error('expected firmware required')
    with MqttTransport(a.host,a.port,a.prefix) as transport:
        clock=None
        if a.wokwi_clock:
            clock=WokwiClock(a.expected_firmware_id)
            transport.watch_topic=a.prefix+'/device/esp32-01/telemetry'
            transport.client.on_message=lambda c,u,m: clock.observe(m.payload,m.retain) if len(m.payload)<=4096 else None
            transport.client.subscribe(transport.watch_topic,qos=1)
            anchor=clock.wait_anchor()
            with clock.condition:
                now=int(time.time()*1000);mapped=clock.timestamp(now,now,time.monotonic(),anchor)
            if mapped is None:raise RuntimeError('clock sample expired')
            stamp=mapped['ts_ms']
        else:stamp=int(time.time()*1000)
        count=2 if a.case=='duplicate' else a.count
        print('PROTOCOL TEST ONLY; not model output. Case:',a.case,flush=True)
        for i in range(count):
            case='valid' if a.case in ('duplicate','flood','retained') else a.case
            body=payload_for(case,now_ms=stamp if a.case=='duplicate' else stamp+i)
            info=transport.client.publish(a.prefix+'/ai/result',body,qos=0 if a.case=='flood' else 1,retain=a.case in ('retained','clear-retained'))
            if a.case!='flood':
                info.wait_for_publish(5)
                if not info.is_published():raise RuntimeError('publish not acknowledged')
            print(json.dumps(dict(case=a.case,index=i+1,clock_domain='WOKWI_SIMULATED_UTC' if clock else 'UTC',body=body.decode(),automatic_pass=False)),flush=True)
            if a.case=='flood':time.sleep(.01)
        if a.case=='flood':time.sleep(1)
        if a.case=='retained':print('Reconnect ESP within TTL to test retained delivery. Afterwards run --case clear-retained. Live retained publish may be delivered with retain=false.')
if __name__=='__main__':main()

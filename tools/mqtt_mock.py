#!/usr/bin/env python3
"""S6 protocol mock only: no camera, model, inference or training."""
import argparse
import json
import os
import threading
import time
import uuid

DEFAULT_PREFIX = 'ptit/nhom07/lab-7c49e2'


def payload_for(case, label='lua', confidence=0.93, now_ms=None):
    now_ms = int(time.time() * 1000) if now_ms is None else now_ms
    p = {'v': 1, 'nhan': label, 'do_tin_cay': confidence, 'ts_ms': now_ms}
    if case == 'json':
        return b'{bad json'
    if case == 'oversize':
        return b'x' * 257
    if case == 'clear-retained':
        return b''
    if case == 'missing':
        del p['nhan']
    elif case == 'type':
        p['do_tin_cay'] = '0.93'
    elif case == 'confidence':
        p['do_tin_cay'] = 1.1
    elif case == 'old':
        p['ts_ms'] -= 20000
    elif case == 'future':
        p['ts_ms'] += 60000
    return json.dumps(p, separators=(',', ':'), allow_nan=False).encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default=os.getenv('PCCC_MQTT_HOST', 'broker.hivemq.com'))
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--prefix', default=os.getenv('PCCC_TOPIC_PREFIX', DEFAULT_PREFIX))
    parser.add_argument('--label', choices=['lua', 'khoi', 'binh_thuong'], default='lua')
    parser.add_argument('--confidence', type=float, default=0.93)
    parser.add_argument('--case', choices=['valid', 'json', 'missing', 'type', 'confidence',
                        'old', 'future', 'duplicate', 'oversize', 'retained', 'clear-retained'], default='valid')
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('--interval', type=float, default=2)
    parser.add_argument('--watch', action='store_true', help='Subscribe to device telemetry/event/availability only')
    parser.add_argument('--duration', type=float, default=0, help='Watch duration, 0 until Ctrl-C')
    args = parser.parse_args()
    if args.count < 1 or args.interval < 0.1 or args.duration < 0:
        parser.error('count>=1, interval>=0.1s, duration>=0 required')
    if not args.prefix or any(c in args.prefix for c in ('#', '+', '\0')) or len(args.prefix)>100:
        parser.error('prefix must be a concrete deployment path (max100 chars)')
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        parser.error('Install tools/requirements-mqtt.txt in a Python venv first')
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id='pccc-s6-mock-' + uuid.uuid4().hex[:10], protocol=mqtt.MQTTv311)
    username = os.getenv('PCCC_MQTT_USERNAME')
    if username:
        client.username_pw_set(username, os.getenv('PCCC_MQTT_PASSWORD'))
    client.connect_timeout = 5
    client.max_queued_messages_set(16)
    client.reconnect_delay_set(1, 30)
    ready = threading.Event()
    subscribed = threading.Event()

    def on_connect(c, userdata, flags, reason, properties):
        if reason.is_failure:
            print('[MQTT] connection rejected:', reason, flush=True)
            return
        ready.set()
        if args.watch:
            c.subscribe(args.prefix + '/device/esp32-01/+', qos=1)

    def on_disconnect(c, userdata, flags, reason, properties):
        ready.clear()
        subscribed.clear()

    def on_subscribe(c, userdata, mid, reasons, properties):
        if all(not r.is_failure for r in reasons):
            subscribed.set()

    def on_message(c, userdata, message):
        print('[RX {} retained={}] {}'.format(message.topic, int(message.retain),
              message.payload.decode('utf-8', errors='replace')), flush=True)

    client.on_connect, client.on_disconnect = on_connect, on_disconnect
    client.on_subscribe, client.on_message = on_subscribe, on_message
    print('S6 MOCK ONLY | {}:{} | {}'.format(args.host, args.port, args.prefix), flush=True)
    client.connect_async(args.host, args.port, 15)
    client.loop_start()
    try:
        if not ready.wait(15):
            raise RuntimeError('MQTT not connected after15s; check broker/network')
        if args.watch:
            if not subscribed.wait(5):
                raise RuntimeError('SUBACK not received')
            print('[WATCH subscribed]', flush=True)
            deadline = time.monotonic() + args.duration if args.duration else float('inf')
            while time.monotonic() < deadline:
                time.sleep(0.1)
        else:
            duplicate = payload_for('valid', args.label, args.confidence)
            for i in range(args.count):
                body = duplicate if args.case == 'duplicate' else payload_for(args.case, args.label, args.confidence)
                retained = args.case in ('retained', 'clear-retained')
                info = client.publish(args.prefix + '/ai/result', body, qos=1, retain=retained)
                info.wait_for_publish(timeout=5)
                if info.rc != mqtt.MQTT_ERR_SUCCESS or not info.is_published():
                    raise RuntimeError('Publish not acknowledged within5s')
                print('[TX {} retained={}] {}'.format(i+1, int(retained), body.decode()), flush=True)
                if i+1 < args.count:
                    time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == '__main__':
    main()

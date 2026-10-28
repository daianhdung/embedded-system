"""Real localhost broker smoke for Python mock only, not ESP32 runtime. Run from firmware/."""
import asyncio
import sys
import socket
import threading
import tempfile
from pathlib import Path
from amqtt.broker import Broker

async def main():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0))
        port = probe.getsockname()[1]
    broker = Broker({'listeners': {'default': {'type': 'tcp', 'bind': f'127.0.0.1:{port}'}},
                     'plugins': {'amqtt.plugins.authentication.AnonymousAuthPlugin': {'allow_anonymous': True}}})
    await broker.start()
    args = [sys.executable, 'tools/mqtt_mock.py', '--host', '127.0.0.1', '--port', str(port),
            '--prefix', 'ptit/nhom07/s6-local-test']
    received = []
    ready = threading.Event()
    all_received = threading.Event()
    import paho.mqtt.client as mqtt
    sub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    sub.on_connect = lambda c,u,f,r,p: c.subscribe('ptit/nhom07/s6-local-test/ai/result', qos=1)
    sub.on_subscribe = lambda c,u,mid,reasons,p: ready.set()
    def on_message(c,u,m):
        received.append(m.payload)
        if len(received)==2:
            all_received.set()
    sub.on_message = on_message
    sub.connect_async('127.0.0.1',port)
    sub.loop_start()
    assert await asyncio.to_thread(ready.wait,5)
    proc = await asyncio.create_subprocess_exec(*args, '--count', '2', '--interval', '0.1',
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    output,_ = await asyncio.wait_for(proc.communicate(),15)
    print(output.decode(),end='')
    assert proc.returncode==0, proc.returncode
    assert await asyncio.to_thread(all_received.wait,5)
    assert len(received)==2, received
    import json
    for body in received:
        obj=json.loads(body)
        assert obj['v']==1 and obj['nhan']=='lua' and obj['do_tin_cay']==0.93
    # Exercise the watch command against a real localhost broker as well.
    watcher=await asyncio.create_subprocess_exec(*args,'--watch','--duration','1.5',
                    stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
    preamble = await asyncio.wait_for(watcher.stdout.readline(),5)
    readiness = await asyncio.wait_for(watcher.stdout.readline(),5)
    assert b'WATCH subscribed' in readiness
    sub.publish('ptit/nhom07/s6-local-test/device/esp32-01/telemetry', '{"state":"NORMAL","mock_device":true}')
    output,_=await asyncio.wait_for(watcher.communicate(),10)
    print((preamble+readiness+output).decode(),end='')
    assert watcher.returncode==0 and b'NORMAL' in output
    # S7 replay + S8 capture through a real localhost broker. Device payload is
    # explicitly a PC fixture; this must never be counted as ESP32 integration.
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp); source=folder/'replay.jsonl'; capture=folder/'capture.jsonl'
        source.write_text('{"label":"lua","confidence":0.9}\nnull\n{"label":"binh_thuong","confidence":0.95}\n')
        cap=await asyncio.create_subprocess_exec(sys.executable,'tools/capture_mqtt.py',
            '--host','127.0.0.1','--port',str(port),'--prefix','ptit/nhom07/s6-local-test',
            '--out',str(capture),'--duration','3','--expected-firmware-id','FAKE_DEVICE_TEST',
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
        line=await asyncio.wait_for(cap.stdout.readline(),5)
        assert b'CAPTURE ready' in line,line
        fixture=dict(v=1,record_type='TELEMETRY',firmware_id='FAKE_DEVICE_TEST',boot_id='unit-session',
                     state='NORMAL',local_level=0,ai_level=0,merged_level=0,pump_cmd=False,
                     valve_cmd=False,door_open_cmd=False,fixture_not_mcu=True)
        sub.publish('ptit/nhom07/s6-local-test/device/esp32-01/telemetry',json.dumps(fixture))
        before=len(received)
        producer=await asyncio.create_subprocess_exec(sys.executable,'tools/ai_publish.py','--backend','replay',
            '--input',str(source),'--host','127.0.0.1','--port',str(port),'--prefix','ptit/nhom07/s6-local-test',
            '--interval','0.1',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
        produced,_=await asyncio.wait_for(producer.communicate(),10)
        assert producer.returncode==0,produced.decode()
        records=[json.loads(row) for row in produced.decode().splitlines()]
        assert sum(r['event']=='PUBACK' for r in records)==2
        assert sum(r['event']=='UNAVAILABLE' for r in records)==1
        result,_=await asyncio.wait_for(cap.communicate(),6)
        assert cap.returncode==0,result.decode()
        captured=[json.loads(row) for row in capture.read_text().splitlines()]
        assert any(row.get('payload',{}).get('firmware_id')=='FAKE_DEVICE_TEST' for row in captured)
        assert len(received)-before==2
        print('PASS S7 replay->MQTT2packets / unknown suppressed; S8 capture PC fixture. No ESP32/model/acceptance PASS.')
    sub.disconnect();sub.loop_stop()
    await broker.shutdown()
    print('PASS localhost broker smoke: mock publish QoS1/receive and watch telemetry. No ESP32 or model involved.')

asyncio.run(main())

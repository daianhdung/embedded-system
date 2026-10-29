"""Localhost MQTT->collector->SQLite integration. Explicit PC fixture, not Wokwi."""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from amqtt.broker import Broker
from dashboard.collector import Collector
from dashboard.store import device_view

async def main():
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    broker=Broker({'listeners':{'default':{'type':'tcp','bind':f'127.0.0.1:{port}'}},'plugins':{'amqtt.plugins.authentication.AnonymousAuthPlugin':{'allow_anonymous':True}}})
    await broker.start()
    with tempfile.TemporaryDirectory() as temp:
        collector=Collector('127.0.0.1',port,'fixture/dashboard',Path(temp)/'test.sqlite3')
        collector.start()
        try:
            for _ in range(50):
                if collector.subscribed:break
                await asyncio.sleep(.1)
            assert collector.subscribed
            import paho.mqtt.client as mqtt
            sender=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2);sender.connect('127.0.0.1',port);sender.loop_start()
            try:
                q=dict(v=1,record_type='TELEMETRY',firmware_id='FAKE_DASH_TEST',boot_id='fixture',uptime_ms=100,
                       state='NORMAL',local_level=0,ai_level=0,merged_level=0,pump_cmd=False,valve_cmd=False,door_open_cmd=False,buzzer_cmd=False,fixture_not_mcu=True)
                sender.publish('fixture/dashboard/device/esp32-01/telemetry',json.dumps(q),qos=1)
                proc=await asyncio.create_subprocess_exec(sys.executable,'tools/ai_publish.py','--backend','replay','--host','127.0.0.1','--port',str(port),'--prefix','fixture/dashboard','--interval','.1',stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
                output,_=await asyncio.wait_for(proc.communicate(),10)
                assert proc.returncode==0,output.decode()
                for _ in range(30):
                    last=collector.store.latest('ai_status')
                    if last and last['payload']['event']=='STOP':break
                    await asyncio.sleep(.1)
                assert collector.store.latest('telemetry')['payload']['firmware_id']=='FAKE_DASH_TEST'
                assert collector.store.latest('ai_status')['payload']['event']=='STOP'
                assert len(collector.store.rows('ai'))==4
                assert device_view(collector.store,collector.session,True)['fixture']
                assert not device_view(collector.store,collector.session,True)['live']
                print('PASS MQTT->dashboard SQLite, source status/STOP, 4 AI packets, fixture never shown live. No ESP/model/acceptance PASS.')
            finally:sender.disconnect();sender.loop_stop()
        finally:collector.stop();collector.store.close()
    await broker.shutdown()
asyncio.run(main())

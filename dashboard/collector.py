"""MQTT subscriber only. No publish method or remote control topics."""
from tools.runtime_config import setting
import os
import threading
import time
import uuid
from .store import Store


class Collector:
    def __init__(self,host,port,prefix,path):
        if not prefix or len(prefix)>100 or any(c in prefix for c in ('#','+','\0')):raise ValueError('invalid prefix')
        self.host,self.port,self.prefix=host,port,prefix
        self.store=Store(path,prefix);self.session=uuid.uuid4().hex
        self.client=None;self.connected=False;self.subscribed=False;self.invalid=0;self.error='';self.lock=threading.RLock()

    def start(self):
        with self.lock:
            if self.client is not None:return
            self.session=uuid.uuid4().hex  # old database samples never become live on reconnect
            import paho.mqtt.client as mqtt
            client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='pccc-dashboard-'+self.session[:12])
            client.connect_timeout=5;client.reconnect_delay_set(1,30)
            if os.getenv('PCCC_MQTT_USERNAME'):client.username_pw_set(os.environ['PCCC_MQTT_USERNAME'],os.getenv('PCCC_MQTT_PASSWORD'))
            if setting('PCCC_MQTT_TLS','0')=='1': client.tls_set()
            def connected(c,u,flags,reason,props):
                self.connected=not reason.is_failure;self.subscribed=False
                if self.connected:
                    c.subscribe([(self.prefix+'/device/esp32-01/+',1),(self.prefix+'/ai/result',1),(self.prefix+'/ai/status',1)])
                else:self.error=str(reason)
            def subscribed(c,u,mid,reasons,props):
                self.subscribed=bool(reasons) and all(not r.is_failure for r in reasons)
            def disconnected(c,u,flags,reason,props):self.connected=False;self.subscribed=False
            def message(c,u,m):
                try:self.store.add(m.topic,m.payload,m.retain,self.session,time.monotonic())
                except (ValueError,TypeError,UnicodeError):self.invalid+=1
                except Exception as error:self.error=type(error).__name__+': '+str(error)
            client.on_connect=connected;client.on_disconnect=disconnected;client.on_subscribe=subscribed;client.on_message=message
            self.client=client
            try:client.connect_async(self.host,self.port,15);client.loop_start()
            except Exception:
                self.client=None;raise

    def stop(self):
        with self.lock:
            client,self.client=self.client,None
            self.connected=False;self.subscribed=False
            if client:client.disconnect();client.loop_stop()

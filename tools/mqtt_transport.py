"""Small synchronous PC transport. Never runs on ESP32's local loop."""
from runtime_config import MQTT_HOST, MQTT_PORT, TOPIC_PREFIX, setting

import os
import threading
import uuid
from mqtt_mock import DEFAULT_PREFIX

class MqttTransport:
    def __init__(self, host=MQTT_HOST, port=MQTT_PORT, prefix=DEFAULT_PREFIX):
        import paho.mqtt.client as mqtt
        if not prefix or len(prefix)>100 or any(c in prefix for c in ('#','+','\0')):
            raise ValueError('invalid concrete topic prefix')
        self.prefix, self.host, self.port = prefix, host, port
        self.ready, self.subscribed = threading.Event(), threading.Event()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='pccc-tools-'+uuid.uuid4().hex[:12])
        self.client.connect_timeout=5
        self.client.max_queued_messages_set(16)
        self.client.reconnect_delay_set(1,30)
        if os.getenv('PCCC_MQTT_USERNAME'):
            self.client.username_pw_set(os.environ['PCCC_MQTT_USERNAME'], os.getenv('PCCC_MQTT_PASSWORD'))
        if setting('PCCC_MQTT_TLS','0')=='1': self.client.tls_set()
        self.watch_topic=None
        self.client.on_connect=self._connect
        self.client.on_disconnect=self._disconnect
        self.client.on_subscribe=self._subscribed
    def _connect(self,c,u,f,r,p):
        if not r.is_failure:
            self.ready.set()
            if self.watch_topic: c.subscribe(self.watch_topic,qos=1)
    def _disconnect(self,c,u,f,r,p):
        self.ready.clear(); self.subscribed.clear()
    def _subscribed(self,c,u,mid,reasons,p):
        if reasons and all(not r.is_failure for r in reasons): self.subscribed.set()
    def __enter__(self):
        self.client.connect_async(self.host,self.port,15); self.client.loop_start()
        if not self.ready.wait(15):
            self.close(); raise RuntimeError('broker connection timed out')
        return self
    def publish(self,body):
        info=self.client.publish(self.prefix+'/ai/result',body,qos=1,retain=False)
        info.wait_for_publish(timeout=5)
        if not info.is_published(): raise RuntimeError('PUBACK timed out')
    def publish_status(self,body):
        # Best effort monitoring metadata; never a device command or AI result.
        info=self.client.publish(self.prefix+'/ai/status',body,qos=0,retain=False)
        return info.rc==0

    def close(self):
        self.client.disconnect(); self.client.loop_stop()
    def __exit__(self,*args): self.close()

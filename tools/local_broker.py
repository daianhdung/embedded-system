#!/usr/bin/env python3
"""Loopback-only development broker. Ctrl+C stops it; messages stay in memory."""
import asyncio
import ipaddress
from runtime_config import MQTT_PORT, setting

async def serve():
    from amqtt.broker import Broker
    bind=setting('PCCC_BROKER_BIND','127.0.0.1')
    if not ipaddress.ip_address(bind).is_loopback:
        raise ValueError('Local anonymous broker must bind loopback; use a managed authenticated broker externally')
    broker=Broker({'listeners':{'default':{'type':'tcp','bind':f'{bind}:{MQTT_PORT}'}},
        'plugins':{'amqtt.plugins.authentication.AnonymousAuthPlugin':{'allow_anonymous':True}}})
    await broker.start()
    print(f'LOCAL MQTT ready: {bind}:{MQTT_PORT} | development only | Ctrl+C to stop',flush=True)
    try: await asyncio.Event().wait()
    finally: await broker.shutdown()

if __name__=='__main__':
    try: asyncio.run(serve())
    except KeyboardInterrupt: pass

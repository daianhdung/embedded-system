"""PlatformIO: stamp source/config identity without copying credentials into logs."""
from pathlib import Path
import hashlib
Import('env')
root=Path(env['PROJECT_DIR'])
import sys
import json
sys.path.insert(0,str(root/'tools'))
from runtime_config import setting
folder=root/'.pio/generated'
folder.mkdir(parents=True,exist_ok=True)
settings={
    'PCCC_MQTT_URI':setting('PCCC_ESP_MQTT_URI','mqtt://host.wokwi.internal:1883'),
    'PCCC_TOPIC_PREFIX':setting('PCCC_TOPIC_PREFIX','ptit/nhom07/lab-7c49e2'),
    'PCCC_MQTT_USERNAME':setting('PCCC_MQTT_USERNAME'),
    'PCCC_MQTT_PASSWORD':setting('PCCC_MQTT_PASSWORD'),
}
config='#pragma once\n'+''.join('#ifndef '+k+'\n#define '+k+' '+json.dumps(v)+'\n#endif\n' for k,v in settings.items())
config_header=folder/'pccc_runtime_config.h'
if not config_header.exists() or config_header.read_text()!=config: config_header.write_text(config)
files=[root/'platformio.ini' ,root/'scripts/build_identity.py']
files+=list((root/'src').glob('*.cpp'))
files+=[p for p in (root/'include').glob('*.h') if p.name!='secrets.h']
digest=hashlib.sha256()
# Fingerprint effective deployment config without exposing credential text.
digest.update(config.encode())
if (root/'include/secrets.h').exists(): digest.update((root/'include/secrets.h').read_bytes())
for p in sorted(files):
    digest.update(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes()+b'\0')
folder=root/'.pio/generated'
folder.mkdir(parents=True,exist_ok=True)
header=folder/'pccc_build_identity.h'
content='#pragma once\n#define PCCC_FIRMWARE_ID "R7-'+digest.hexdigest()[:16]+'"\n'
if not header.exists() or header.read_text()!=content:
    header.write_text(content)
env.Append(CPPPATH=[str(folder)])

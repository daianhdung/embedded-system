"""PlatformIO: stamp source/config identity without copying credentials into logs."""
from pathlib import Path
import hashlib
Import('env')
root=Path(env['PROJECT_DIR'])
files=[root/'platformio.ini',root/'scripts/build_identity.py']
files+=list((root/'src').glob('*.cpp'))
files+=[p for p in (root/'include').glob('*.h') if p.name!='secrets.h']
digest=hashlib.sha256()
for p in sorted(files):
    digest.update(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes()+b'\0')
folder=root/'.pio/generated'
folder.mkdir(parents=True,exist_ok=True)
header=folder/'pccc_build_identity.h'
content='#pragma once\n#define PCCC_FIRMWARE_ID "R7-'+digest.hexdigest()[:16]+'"\n'
if not header.exists() or header.read_text()!=content:
    header.write_text(content)
env.Append(CPPPATH=[str(folder)])

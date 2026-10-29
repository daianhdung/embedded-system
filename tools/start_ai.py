#!/usr/bin/env python3
"""Start the configured local AI for the current Wokwi build (or --hardware)."""
from pathlib import Path
import os
import re
import sys
from runtime_config import ROOT,setting

if __name__=='__main__':
    args=sys.argv[1:]
    if '--hardware' in args: args.remove('--hardware')
    else:
        identity=setting('PCCC_EXPECTED_FIRMWARE_ID')
        header=ROOT/'.pio/generated/pccc_build_identity.h'
        if not identity and header.exists():
            match=re.search(r'#define PCCC_FIRMWARE_ID "([^"]+)"',header.read_text())
            if match: identity=match[1]
        if not identity: raise SystemExit('Build firmware first, or configure PCCC_EXPECTED_FIRMWARE_ID. Hardware: --hardware')
        args=['--wokwi-clock','--expected-firmware-id',identity]+args
    os.execv(sys.executable,[sys.executable,str(ROOT/'tools/ai_publish.py')]+args)

#!/usr/bin/env python3
"""Run260 indexed synthetic regression entries, separate from acceptance ledger."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    build=ROOT/'.host-build';build.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build) as tmp:
        exe=str(Path(tmp)/'s8_host')
        subprocess.run(['clang++','-std=c++11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g',
                        '-DARDUINOJSON_USE_LONG_LONG=1','-I',str(ROOT/'include'),'-isystem',str(ROOT/'.pio/libdeps/esp32dev/ArduinoJson/src'),
                        str(ROOT/'test/host/test_s8_scenarios.cpp'),str(ROOT/'src/safety.cpp'),str(ROOT/'src/ai_contract.cpp'),'-o',exe],check=True)
        subprocess.run([exe,str(a.out.resolve())],check=True)
if __name__=='__main__': main()

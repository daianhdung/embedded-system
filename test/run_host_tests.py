"""Chạy test lõi an toàn thuần C++; không thay cho Wokwi runtime."""
from pathlib import Path
import subprocess
import sys
import tempfile

firmware = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(firmware / 'test/verify_wiring.py')], check=True)
build = firmware / '.host-build'
build.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=build) as temporary:
    executable = str(Path(temporary) / 'test_safety')
    subprocess.run([
        'clang++', '-std=c++11', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined', '-g', '-I', str(firmware / 'include'),
        str(firmware / 'test/host/test_safety.cpp'),
        str(firmware / 'src/safety.cpp'), '-o', executable,
    ], check=True)
    subprocess.run([executable], check=True)

json_include = firmware / '.pio/libdeps/esp32dev/ArduinoJson/src'
if not json_include.is_dir():
    raise SystemExit('Run pio pkg install first to install pinned ArduinoJson6.21.5')
with tempfile.TemporaryDirectory(dir=build) as temporary:
    executable = str(Path(temporary) / 'test_ai')
    subprocess.run([
        'clang++', '-std=c++11', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=address,undefined', '-g', '-DARDUINOJSON_USE_LONG_LONG=1',
        '-I', str(firmware / 'include'), '-isystem', str(json_include),
        str(firmware / 'test/host/test_ai.cpp'), str(firmware / 'src/ai_contract.cpp'),
        str(firmware / 'src/safety.cpp'), str(firmware / 'src/mqtt_payload.cpp'), '-o', executable,
    ], check=True)
    subprocess.run([executable], check=True)

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

"""Repository .env configuration; process environment and CLI take precedence.
Only KEY=value, quotes and comments are supported; no shell execution/expansion.
"""
import os
import re
import shlex
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read_env(path):
    values = {}
    if not Path(path).exists(): return values
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'): continue
        key, sep, raw = line.partition('=')
        key = key.strip()
        if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise ValueError(f'Invalid .env key at line {number}')
        parts = shlex.split(raw, comments=True)
        if len(parts) > 1: raise ValueError(f'Quote .env values containing spaces: line {number}')
        values[key] = parts[0] if parts else ''
    return values

for _key, _value in read_env(ROOT / '.env').items():
    os.environ.setdefault(_key, _value)

def setting(name, default=''): return os.getenv(name, default)
def local_path(name, default):
    path = Path(setting(name, default)).expanduser()
    return path if path.is_absolute() else ROOT / path
MQTT_HOST = setting('PCCC_MQTT_HOST', '127.0.0.1')
MQTT_PORT = int(setting('PCCC_MQTT_PORT', '1883'))
TOPIC_PREFIX = setting('PCCC_TOPIC_PREFIX', 'ptit/nhom07/lab-7c49e2')

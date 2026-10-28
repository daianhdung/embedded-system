"""Đối chiếu wiring/config với tên chân chính thức; không chạy MCU."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
diagram = json.loads((root / 'diagram.json').read_text())
parts = {p['id']: p for p in diagram['parts']}
assert len(parts) == len(diagram['parts'])
assert parts['esp']['type'] == 'wokwi-esp32-devkit-v1'
config = (root / 'include/config.h').read_text()
pins = {name: int(number) for name, number in re.findall(r'constexpr uint8_t (k\w+Pin) = (\d+);', config)}
assert len(set(pins.values())) == len(pins)
assert pins['kSmokePin'] in {32, 33, 34, 35, 36, 39}
assert pins['kLdrPin'] in {32, 33, 34, 35, 36, 39}
assert 'flame' not in parts
assert parts['ldr']['type'] == 'wokwi-photoresistor-sensor'
assert parts['door']['type'] == 'wokwi-servo'
links = {frozenset(wire[:2]) for wire in diagram['connections']}
for component, name in {
    'gas:AOUT': 'kSmokePin', 'dht:SDA': 'kDhtPin',
    'ldr:AO': 'kLdrPin', 'door:PWM': 'kDoorServoPin', 'ack:1.l': 'kAckPin',
    'lcd:SDA': 'kSdaPin', 'lcd:SCL': 'kSclPin',
    'pump:IN': 'kPumpRelayPin', 'valve:IN': 'kValveRelayPin',
    'buzzer:2': 'kBuzzerPin', 'r_red:1': 'kRedLedPin',
    'r_green:1': 'kGreenLedPin',
}.items():
    assert frozenset([component, f'esp:D{pins[name]}']) in links, component
board_pins = set(json.loads((root / 'test/fixtures/esp32-devkit-v1-pins.json').read_text())['pins'])
gas_pins = set(json.loads((root / 'test/fixtures/gas-sensor-pins.json').read_text())['pins'])
for component, names in {'ldr': {'VCC','GND','AO','DO'}, 'door': {'PWM','V+','GND'}}.items():
    for wire in diagram['connections']:
        for endpoint in wire[:2]:
            if endpoint.startswith(component + ':'):
                assert endpoint.split(':', 1)[1] in names, endpoint
for a,b in [('ldr:VCC','esp:3V3'),('ldr:GND','esp:GND.1'),('door:V+','esp:VIN'),('door:GND','esp:GND.1')]:
    assert frozenset([a,b]) in links
assert not any('ldr:DO' in w[:2] for w in diagram['connections'])
channels = {n:int(v) for n,v in re.findall(r'constexpr uint8_t (k\w+Channel) = (\d+);', config)}
assert channels['kServoChannel'] // 8 != channels['kBuzzerChannel'] // 8
for wire in diagram['connections']:
    for endpoint in wire[:2]:
        assert endpoint.startswith('$serialMonitor:') or endpoint.split(':')[0] in parts
        if endpoint.startswith('gas:'):
            assert endpoint.split(':', 1)[1] in gas_pins, endpoint
        if endpoint.startswith('esp:'):
            assert endpoint.split(':', 1)[1] in board_pins, f'Unknown DevKit V1 pin: {endpoint}'
assert parts['r_dht']['attrs']['value'] == '10000'
assert frozenset(['r_dht:1', 'esp:3V3']) in links
assert frozenset(['r_dht:2', 'dht:SDA']) in links
for relay in ['pump', 'valve']:
    assert parts[relay]['attrs']['transistor'] == 'npn'
    assert frozenset([relay + ':NO', relay + '_load_r:1']) in links
    assert frozenset([relay + ':COM', 'esp:3V3']) in links
for file in root.rglob('*'):
    if any(part in file.parts for part in ['.pio', '.git', '.host-build', '.venv', '.venv-ai', '__pycache__', 'models', 'datasets', 'runs']) or not file.is_file():
        continue
    # Screenshots/video/model files are legitimate binary evidence, not source.
    if file.suffix in {'.cpp', '.h', '.py', '.ini', '.toml', '.json', '.md', '.yaml', '.yml'}:
        assert b'\0' not in file.read_bytes(), file
print('PASS wiring: DevKit V1/MQ2/LDR/servo pins, ADC1, 3V3 LDR, independent PWM, DHT and relay loads')

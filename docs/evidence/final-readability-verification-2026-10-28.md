# Final readability pass — 2026-10-28

Baseline: [current diagram immediately before this pass](final-readability-before-2026-10-28.json). This includes the latest gas10ppm default, buzzer0.25 and all prior edits.

| Component | Original ESP32 pin | New diagram pin | Status |
|---|---|---|---|
| MQ-2 ADC | 35 | 35 | MATCH / unchanged |
| LDR ADC | 32 | 32 | MATCH / unchanged |
| DHT22 DATA | 4 | 4 | MATCH / unchanged |
| ACK | 19 | 19 | MATCH / unchanged |
| LCD SDA/SCL | 21/22 | 21/22 | MATCH / unchanged |
| Pump | 26 | 26 | MATCH / unchanged |
| Fan (source: VAN) | 25 | 25 | MATCH / unchanged |
| Servo | 33 | 33 | MATCH / unchanged |
| Buzzer | 27 | 27 | MATCH / unchanged |
| Red LED via resistor | 14 | 14 | MATCH / unchanged |
| Green LED via resistor | 13 | 13 | MATCH / unchanged |

## Electrical verification

All44 endpoint pairs, including Serial, resistors, relay contacts and loads, match the baseline. Every original component and electrical attribute matches, including gas10ppm, LDR100lux, DHT28°C/45%, buzzer0.25, resistor values and transistor configuration. Only positions, wire appearance/routes and text annotations changed; no firmware changes in this pass. All newly added parts are non-electrical `wokwi-text` labels. Static wiring validation PASS.

## Visual changes

DHT is entirely in the left input column. STATUS/ALARM groups buzzer and red/green LEDs below the controller; additional pin labels avoid tracing the entire canvas. Fan GPIO25 is a display alias only; the actual relay id and firmware valve role remain `valve`/VAN.

Long power links are hidden using Wokwi's documented empty wire color, and replaced visually by local explicit pin-to-net labels. The44 electrical endpoint pairs still exist: this is not a removal or replacement of electrical nets. Local labels identify each VCC/GND, relay COM/load cathode, DHT pull-up and controller supply. 5V/VIN, ESP3V3 and commonGND remain separate exactly as before. No unsupported global power symbols or implicit electrical junctions were introduced.

Visible signals use orthogonal routes; output control lines take a single horizontal run from their respective escape lanes instead of a down-across-up detour. Status control lanes spread30px apart to avoid the six-wire bundle immediately below the board. The legend is a compact multiline text box rather than a single canvas-wide line. Some crossings remain because output GPIOs are on the left edge of the fixed board orientation while actuators are on the right.

Approximate control-route lengths, using the same pin geometry model on both versions:

| Signal | Before | After |
|---|---:|---:|
| pump:IN | 654.0px | 484.0px |
| valve:IN | 623.7px | 583.7px |
| door:PWM | 782.3px | 722.3px |

Geometry preview found no visible signal crossing unrelated component interiors in the approximate bounding-box model. This is an internal routing preview, not a native Wokwi render. Reload the simulator to inspect actual labels and part geometry. No claim of a new MCU runtime test; behavior preservation is established by unchanged firmware/electrical data.

Format references: [hidden wire color and routes](https://docs.wokwi.com/diagram-format), [multiline text](https://docs.wokwi.com/parts/wokwi-text).

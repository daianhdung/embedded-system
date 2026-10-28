"""Model-independent adapter. No inference model is included."""
from dataclasses import dataclass
import math

LABELS = {'lua', 'khoi', 'binh_thuong'}

@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float

    def __post_init__(self):
        if self.label not in LABELS:
            raise ValueError('unknown label')
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError('confidence must be numeric')
        if not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1:
            raise ValueError('confidence outside[0,1]')

    def packet(self, captured_ms):
        if type(captured_ms) is not int or captured_ms < 1704067200000:
            raise ValueError('capture timestamp must be current UTC milliseconds')
        return dict(v=1, nhan=self.label, do_tin_cay=float(self.confidence), ts_ms=captured_ms)


def prediction_from(value):
    """None means unavailable/unknown, never fabricate a normal result."""
    if value is None:
        return None
    if isinstance(value, Prediction):
        return value
    if not isinstance(value, dict) or set(value) != {'label', 'confidence'}:
        raise ValueError('plugin/replay returns None or {label,confidence}')
    return Prediction(**value)


def detection_result(detections, threshold=0.8):
    """Future detector helper: confirmed fire outranks smoke. No box != normal."""
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('invalid detection threshold')
    selected = []
    for d in detections:
        label = {'fire': 'lua', 'smoke': 'khoi', 'lua': 'lua', 'khoi': 'khoi'}.get(str(d['label']).lower())
        if label is None:
            continue
        p = Prediction(label, d['confidence'])
        if p.confidence >= threshold:
            selected.append(p)
    return max(selected, key=lambda p: (p.label == 'lua', p.confidence)) if selected else None

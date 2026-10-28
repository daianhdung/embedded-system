"""Local YOLO fire/smoke plugin. Loading/inference never opens MQTT or a camera."""
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from ai_adapter import detection_result

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHTS = ROOT / 'models/fire-smoke-yolov8n.pt'
ACCEPT_CONFIDENCE = 0.8  # Matches current firmware; not a calibrated operating point.


def assess(detections, threshold=ACCEPT_CONFIDENCE, inference_ms=0):
    """Per-frame gate only; no temporal filter and no safe/normal fallback."""
    if not math.isfinite(inference_ms) or inference_ms < 0:
        raise ValueError('invalid inference duration')
    selected = detection_result(detections, threshold)
    if inference_ms >= 15000:
        return None, 'STALE'
    if selected is not None:
        return selected, 'ABOVE_THRESHOLD'
    return None, 'BELOW_THRESHOLD' if detections else 'NO_DETECTION'


@dataclass
class Observation:
    result: object
    detections: list
    inference_ms: float
    prediction: object
    status: str


class YoloDetector:
    def __init__(self, weights=DEFAULT_WEIGHTS, device='cpu', view_conf=0.25,
                 threshold=ACCEPT_CONFIDENCE):
        if not all(math.isfinite(x) for x in (view_conf, threshold)) or not 0 <= view_conf <= threshold <= 1:
            raise ValueError('require 0 <= view confidence <= acceptance threshold <= 1')
        self.weights = Path(weights).resolve()
        if not self.weights.is_file():
            raise FileNotFoundError(f'Missing weights: {self.weights}')
        self.sha256 = hashlib.sha256(self.weights.read_bytes()).hexdigest()
        from ultralytics import YOLO
        self.model = YOLO(str(self.weights))
        if self.model.task != 'detect' or set(self.model.names.values()) != {'fire', 'smoke'}:
            raise ValueError('Expected detector with exactly fire/smoke labels')
        self.device, self.view_conf, self.threshold = device, view_conf, threshold

    def observe(self, frame_bgr):
        import time
        start = time.perf_counter()
        result = self.model.predict(frame_bgr, conf=self.view_conf, imgsz=640,
                                    device=self.device, verbose=False)[0]
        elapsed = (time.perf_counter() - start) * 1000
        detections = [dict(label=result.names[int(box.cls.item())],
                           confidence=float(box.conf.item()),
                           xyxy=[float(v) for v in box.xyxy[0].tolist()])
                      for box in result.boxes]
        prediction, status = assess(detections, self.threshold, elapsed)
        return Observation(result, detections, elapsed, prediction, status)


_detector = None


def predict(frame_bgr):
    """Compatible with ai_publish.py --plugin yolo_plugin:predict (future MQTT use)."""
    global _detector
    if _detector is None:
        _detector = YoloDetector()
    return _detector.observe(frame_bgr).prediction


def transport_prediction(observation):
    """Connectivity diagnostic: preserve real confidence; ESP applies its gate.

    Eligible fire/smoke retains priority. With no eligible result, forward a
    visible low-confidence detection. None/stale never becomes normal.
    Low confidence has AI level 0 under the EXISTING firmware contract.
    """
    if observation.status == 'STALE':
        return None
    if observation.prediction is not None:
        return observation.prediction
    return detection_result(observation.detections, threshold=0.25)


def predict_raw(frame_bgr):
    """Opt-in diagnostic plugin; may send below-threshold observations to ESP."""
    global _detector
    if _detector is None:
        _detector = YoloDetector()
    return transport_prediction(_detector.observe(frame_bgr))

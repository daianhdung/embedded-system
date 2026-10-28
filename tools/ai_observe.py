#!/usr/bin/env python3
"""Observe local YOLO results and log frames. No MQTT imports/connections/publishing."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from yolo_plugin import DEFAULT_WEIGHTS, YoloDetector


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', default='0', help='Camera index, image or video path')
    p.add_argument('--weights', type=Path, default=DEFAULT_WEIGHTS)
    p.add_argument('--view-conf', type=float, default=0.25)
    p.add_argument('--threshold', type=float, default=0.8, help='Observation only; does not change firmware')
    p.add_argument('--device', default='cpu')
    p.add_argument('--duration', type=float, default=0, help='Seconds; 0 until Q/Ctrl+C or source ends')
    p.add_argument('--console-interval', type=float, default=1)
    p.add_argument('--headless', action='store_true', help='No window; useful for image/video checks')
    p.add_argument('--out', type=Path, help='New run directory; existing directory is rejected')
    a = p.parse_args()
    if not all(math.isfinite(x) for x in (a.duration, a.console_interval)) or a.duration < 0 or a.console_interval < 0.1:
        p.error('duration >= 0 and console interval >= 0.1')
    detector = YoloDetector(a.weights, a.device, a.view_conf, a.threshold)
    import cv2
    folder = a.out or Path('runs') / ('ai-observe-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(parents=True, exist_ok=False)
    source = int(a.source) if a.source.isdigit() else a.source
    image = None if isinstance(source, int) else cv2.imread(source) if Path(source).suffix.lower() in {'.jpg','.jpeg','.png','.webp','.bmp'} else None
    cap = None
    started = time.monotonic()
    count = 0
    last_console = float('-inf')
    window = 'AI OBSERVE ONLY | S: snapshot | Q: quit'
    print(f'OBSERVE ONLY | MQTT: OFF | view >= {a.view_conf} | gate >= {a.threshold}', flush=True)
    print(f'Log: {folder / "observations.jsonl"}', flush=True)
    with (folder / 'observations.jsonl').open('x') as log:
        def write(event, **fields):
            log.write(json.dumps(dict(event=event, utc=datetime.now(timezone.utc).isoformat(),
                                      mqtt_enabled=False, **fields), allow_nan=False) + '\n')
            log.flush()
        write('START', model_status='PRETRAINED_UNVERIFIED', weights=str(detector.weights),
              weights_sha256=detector.sha256, source=a.source, device=a.device,
              view_conf=a.view_conf, acceptance_threshold=a.threshold,
              temporal_filter=False, frame_time_meaning='after read; not camera exposure time')
        reason = 'source_ended'
        try:
            if image is None:
                cap = cv2.VideoCapture(source)
                if not cap.isOpened():
                    raise RuntimeError('Cannot open camera/video; check source and camera permission')
            while not a.duration or time.monotonic() - started < a.duration:
                if image is not None:
                    frame = image
                else:
                    ok, frame = cap.read()
                    if not ok:
                        if isinstance(source, int):
                            raise RuntimeError('Camera read failed; no safe/normal fallback')
                        break
                captured_ms = int(time.time() * 1000)
                read_monotonic = time.monotonic_ns()
                obs = detector.observe(frame)
                count += 1
                prediction = None if obs.prediction is None else dict(label=obs.prediction.label, confidence=obs.prediction.confidence)
                write('FRAME', frame_id=count, read_utc_ms=captured_ms, read_monotonic_ns=read_monotonic,
                      inference_ms=round(obs.inference_ms, 3), detections=obs.detections,
                      status=obs.status, selected=prediction)
                annotated = obs.result.plot() if not a.headless or image is not None else None
                if annotated is not None:
                    cv2.putText(annotated, f'MQTT OFF | {obs.status} | gate {a.threshold:.2f}',
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                now = time.monotonic()
                if now - last_console >= a.console_interval or image is not None:
                    values = ', '.join(f'{d["label"]}={d["confidence"]:.3f}' for d in obs.detections) or 'none'
                    print(f'[{count}] {obs.status} | {values} | inference {obs.inference_ms:.1f} ms | MQTT OFF', flush=True)
                    last_console = now
                if image is not None:
                    output = folder / 'image-result.jpg'
                    if not cv2.imwrite(str(output), annotated):
                        raise RuntimeError('Failed to save image result')
                    write('SNAPSHOT', frame_id=count, path=output.name)
                    reason = 'image_complete'
                    break
                if not a.headless:
                    cv2.imshow(window, annotated)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('s'):
                        output = folder / f'frame-{count:08}.jpg'
                        if not cv2.imwrite(str(output), annotated):
                            raise RuntimeError('Failed to save snapshot')
                        write('SNAPSHOT', frame_id=count, path=output.name)
                        print(f'Snapshot: {output}', flush=True)
                    if key == ord('q') or cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                        reason = 'operator'; break
            else:
                reason = 'duration'
        except KeyboardInterrupt:
            reason = 'operator'
        except Exception as error:
            reason = 'error'
            write('ERROR', message=str(error))
            raise
        finally:
            if cap is not None:
                cap.release()
            if not a.headless:
                cv2.destroyAllWindows()
            write('STOP', reason=reason, frames=count)
    print(f'Saved {count} frame observations to {folder}; no MQTT and no automatic acceptance PASS.', flush=True)


if __name__ == '__main__':
    main()

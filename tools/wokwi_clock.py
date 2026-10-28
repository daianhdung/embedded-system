"""Explicit simulation-clock mapping, never a hardware UTC synchronization source."""
import json
import threading
import time

MIN_UNIX_MS = 1704067200000


class WokwiClock:
    def __init__(self, expected_firmware_id, max_sample_age=5):
        if not expected_firmware_id:
            raise ValueError('Expected firmware identity is required')
        self.expected = expected_firmware_id
        self.max_sample_age = max_sample_age
        self.condition = threading.Condition()
        self.sample = None
        self.boot = None
        self.last_sent = 0
        self.fatal = None
        self.generation = 0

    def observe(self, body, retained=False, now=None):
        if retained:
            return False
        try:
            data = json.loads(body)
        except (ValueError, TypeError, UnicodeDecodeError):
            return False
        if not isinstance(data, dict):
            return False
        if (data.get('record_type') != 'TELEMETRY' or data.get('mode') != 'SIMULATION'
                or data.get('firmware_id') != self.expected
                or not isinstance(data.get('boot_id'), str) or not data['boot_id']
                or type(data.get('ts_ms')) is not int
                or not MIN_UNIX_MS <= data['ts_ms'] < 2**63
                or not all(data.get(k) is True for k in ('wifi', 'mqtt', 'subscribed', 'clock_synced'))):
            return False
        with self.condition:
            if self.boot is not None and data['boot_id'] != self.boot:
                self.fatal = 'ESP restarted: stop and restart publisher for the new boot'
                self.sample = None
                self.condition.notify_all()
                return False
            if self.sample and data['ts_ms'] <= self.sample['ts_ms']:
                return False
            self.boot = data['boot_id']
            self.sample = dict(ts_ms=data['ts_ms'], boot_id=self.boot,
                               received_monotonic=time.monotonic() if now is None else now,
                               generation=self.generation)
            self.condition.notify_all()
            return True

    def timestamp(self, captured_ms, utc_now_ms, monotonic_now, anchor=None):
        """Caller holds condition when used concurrently. None means wait; never fake normal."""
        if self.fatal:
            raise RuntimeError(self.fatal)
        age = utc_now_ms - captured_ms
        if age < -2000 or age >= 15000:
            raise ValueError('Source frame expired or PC clock changed; not publishing')
        sample = anchor or self.sample
        if not sample or self.sample is None or sample['generation'] != self.generation:
            return None
        sample_age = monotonic_now - sample['received_monotonic']
        if not 0 <= sample_age <= self.max_sample_age:
            return None
        # Anchor is obtained BEFORE reading the frame. No wall-time extrapolation.
        # ESP TTL therefore includes simulated time since that pre-capture anchor.
        stamp = sample['ts_ms']
        if stamp <= self.last_sent or stamp < MIN_UNIX_MS:
            return None
        self.last_sent = stamp
        return dict(timestamp_domain='WOKWI_SIMULATED_UTC', ts_ms=stamp,
                    source_utc_ms=captured_ms, source_age_ms=max(0, age),
                    telemetry_age_ms=round(sample_age * 1000), boot_id=self.boot,
                    firmware_id=self.expected)

    def invalidate(self):
        with self.condition:
            self.sample = None
            self.generation += 1
            self.condition.notify_all()

    def wait_anchor(self):
        deadline = time.monotonic() + 10
        with self.condition:
            while True:
                if self.fatal:
                    raise RuntimeError(self.fatal)
                if (self.sample and self.sample['ts_ms'] > self.last_sent
                        and 0 <= time.monotonic() - self.sample['received_monotonic'] <= self.max_sample_age):
                    return self.sample.copy()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError('No fresh matching Wokwi telemetry within 10s; no packet sent')
                self.condition.wait(min(remaining, .25))

#pragma once
#include <cstddef>
#include <cstdint>

namespace AiContract {
constexpr size_t kMaxPayload = 256;
constexpr uint32_t kTtlMs = 15000;
constexpr uint32_t kFutureToleranceMs = 2000;
constexpr double kConfidenceThreshold = 0.8;
constexpr int64_t kMinUnixMs = 1704067200000LL; // 2024-01-01, gate NTP.
}

struct AiSignal {
  bool received = false;
  uint8_t level = 0;
  double confidence = 0;
  int64_t timestampMs = 0;
  uint32_t receivedMs = 0;
  uint32_t remainingMs = 0;
  bool fresh(uint32_t now) const {
    return received && static_cast<uint32_t>(now - receivedMs) < remainingMs;
  }
};

enum class AiReject { None, Size, Retained, Clock, Json, Schema, Label,
                      Confidence, Timestamp, Replay };
const char* aiRejectName(AiReject error);

// One publisher stream per deployment. Strictly increasing UTC ts_ms is the
// replay watermark; it survives MQTT reconnects, but not a device reboot.
class AiTracker {
 public:
  AiReject accept(const char* payload, size_t length, bool retained,
                  int64_t utcMs, uint32_t receivedMs);
  void invalidate() { signal_.received = false; }
  const AiSignal& signal() const { return signal_; }
 private:
  AiSignal signal_;
  int64_t lastTimestampMs_ = 0;
};

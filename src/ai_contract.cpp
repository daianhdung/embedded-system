#include "ai_contract.h"
#include <ArduinoJson.h>
#include <cmath>
#include <cstring>

namespace {
// ArduinoJson6 accepts some relaxed JSON (single quotes/unquoted keys). The
// wire contract is strict, flat JSON; validate its small lexical grammar first.
class FlatJson {
 public:
  FlatJson(const char* p,size_t n):p_(p),end_(p+n) {}
  bool valid(size_t& fields) {
    ws(); if (!take('{')) return false; ws();
    if (take('}')) { ws(); return p_==end_; }
    for (;;) {
      if (!string()) return false;
      ws(); if (!take(':')) return false; ws();
      if (p_==end_) return false;
      if (*p_=='"') { if (!string()) return false; }
      else if (!literal("true") && !literal("false") && !literal("null") && !number()) return false;
      ++fields; ws();
      if (take('}')) { ws(); return p_==end_; }
      if (!take(',')) return false;
      ws();
    }
  }
 private:
  const char* p_; const char* end_;
  void ws() { while (p_!=end_ && (*p_==' ' || *p_=='\t' || *p_=='\r' || *p_=='\n')) ++p_; }
  bool take(char c) { if (p_==end_ || *p_!=c) return false; ++p_; return true; }
  static bool digit(char c) { return c>='0' && c<='9'; }
  bool string() {
    if (!take('"')) return false;
    while (p_!=end_) {
      const unsigned char c=static_cast<unsigned char>(*p_++);
      if (c=='"') return true;
      if (c<0x20) return false;
      if (c=='\\') {
        if (p_==end_) return false;
        const char e=*p_++;
        if (e=='u') {
          for (int i=0;i<4;++i) {
            if (p_==end_ || !((*p_>='0' && *p_<='9') || (*p_>='a' && *p_<='f') || (*p_>='A' && *p_<='F'))) return false;
            ++p_;
          }
        } else if (!std::strchr("\"\\/bfnrt",e)) return false;
      }
    }
    return false;
  }
  bool literal(const char* text) {
    const size_t n=std::strlen(text);
    if (static_cast<size_t>(end_-p_)<n || std::memcmp(p_,text,n)) return false;
    p_+=n; return true;
  }
  bool number() {
    take('-'); if (p_==end_) return false;
    if (!take('0')) {
      if (*p_<'1' || *p_>'9') return false;
      do { ++p_; } while (p_!=end_ && digit(*p_));
    }
    if (take('.')) {
      if (p_==end_ || !digit(*p_)) return false;
      do { ++p_; } while (p_!=end_ && digit(*p_));
    }
    if (take('e') || take('E')) {
      if (!take('+')) take('-');
      if (p_==end_ || !digit(*p_)) return false;
      do { ++p_; } while (p_!=end_ && digit(*p_));
    }
    return true;
  }
};
}

const char* aiRejectName(AiReject e) {
  switch (e) {
    case AiReject::None: return "OK";
    case AiReject::Size: return "SIZE";
    case AiReject::Retained: return "RETAINED";
    case AiReject::Clock: return "CLOCK_UNSYNCED";
    case AiReject::Json: return "JSON";
    case AiReject::Schema: return "SCHEMA";
    case AiReject::Label: return "LABEL";
    case AiReject::Confidence: return "CONFIDENCE";
    case AiReject::Timestamp: return "TIMESTAMP";
    case AiReject::Replay: return "REPLAY";
  }
  return "UNKNOWN";
}

AiReject AiTracker::accept(const char* payload, size_t length, bool retained,
                           int64_t utcMs, uint32_t receivedMs) {
  if (!payload || !length || length > AiContract::kMaxPayload) return AiReject::Size;
  if (retained) return AiReject::Retained;
  if (utcMs < AiContract::kMinUnixMs) return AiReject::Clock;
  size_t fields=0;
  if (std::memchr(payload,'\0',length) || !FlatJson(payload,length).valid(fields)) return AiReject::Json;
  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, payload, length, DeserializationOption::NestingLimit(2))) return AiReject::Json;
  if (!doc.is<JsonObject>() || doc.size()!=4 || !doc["v"].is<int>() || doc["v"].as<int>()!=1 ||
      !doc["nhan"].is<const char*>() || !doc["do_tin_cay"].is<double>() ||
      !doc["ts_ms"].is<int64_t>()) return AiReject::Schema;
  for (JsonPairConst member : doc.as<JsonObjectConst>()) {
    const JsonString key=member.key();
    if (std::strlen(key.c_str())!=key.size()) return AiReject::Schema;
  }
  if (fields!=4) return AiReject::Schema; // duplicate keys cannot overwrite silently
  const char* label=doc["nhan"];
  if (strlen(label)!=doc["nhan"].as<JsonString>().size()) return AiReject::Label;
  uint8_t level=0;
  if (!std::strcmp(label,"lua")) level=2;
  else if (!std::strcmp(label,"khoi")) level=1;
  else if (std::strcmp(label,"binh_thuong")) return AiReject::Label;
  const double confidence=doc["do_tin_cay"];
  if (!std::isfinite(confidence) || confidence<0 || confidence>1) return AiReject::Confidence;
  const int64_t ts=doc["ts_ms"];
  if (ts<AiContract::kMinUnixMs || ts>utcMs+AiContract::kFutureToleranceMs ||
      ts<=utcMs-static_cast<int64_t>(AiContract::kTtlMs)) return AiReject::Timestamp;
  if (ts<=lastTimestampMs_) return AiReject::Replay;
  AiSignal next;
  next.received=true; next.level=confidence>=AiContract::kConfidenceThreshold ? level : 0;
  next.confidence=confidence; next.timestampMs=ts; next.receivedMs=receivedMs;
  const uint32_t age=ts<utcMs ? static_cast<uint32_t>(utcMs-ts) : 0;
  next.remainingMs=AiContract::kTtlMs-age; // Old-but-acceptable packets get only remaining lifetime.
  signal_=next; lastTimestampMs_=ts;
  return AiReject::None;
}

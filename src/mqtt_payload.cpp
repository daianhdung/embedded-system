#include "mqtt_payload.h"
#include <ArduinoJson.h>
#include <cmath>
#include "firmware_identity.h"
namespace {
void numberOrNull(JsonObject doc,const char* key,float n,bool valid) {
  if (valid && std::isfinite(n)) doc[key]=n; else doc[key]=nullptr;
}
}
size_t encodeMqttSnapshot(const SensorSnapshot& sensors, const SafetySnapshot& safety,
                          const NetworkSnapshot& n, uint32_t uptimeMs,
                          uint32_t maxLoopGapMs, int64_t utcMs, uint32_t encodeMs,
                          bool event, char* buffer, size_t capacity) {
  if (!buffer || !capacity) return 0;
  StaticJsonDocument<2048> doc;
  doc["firmware_id"]=firmwareIdentity();
  doc["boot_id"]=n.bootId;
  doc["wifi"]=n.wifi; doc["mqtt"]=n.mqtt; doc["subscribed"]=n.subscribed; doc["clock_synced"]=n.clock;
  doc["buzzer_cmd"]=safety.buzzerOn; doc["red_led_cmd"]=safety.redLedOn; doc["green_led_cmd"]=safety.greenLedOn;
  doc["ack_raw"]=sensors.ackPressedRaw;
  doc["v"]=1; doc["record_type"]=event ? "EVENT" : "TELEMETRY";
  doc["uptime_ms"]=uptimeMs;
  doc["queue_age_ms"]=static_cast<uint32_t>(encodeMs-uptimeMs);
  doc["ts_ms"]=n.clock ? utcMs : 0;
  doc["mode"]="SIMULATION";
  doc["state"]=stateName(safety.state);
  doc["previous_state"]=stateName(safety.previousState);
  doc["transition_reason"]=safety.transitionReason;
  doc["source"]=triggerSource(safety.activeReasons);
  doc["latched_source"]=triggerSource(safety.latchedReasons);
  doc["local_level"]=safety.localLevel; doc["ai_level"]=safety.aiLevel;
  doc["merged_level"]=safety.dangerLevel;
  doc["active_mask"]=safety.activeReasons; doc["latched_mask"]=safety.latchedReasons;
  doc["smoke_adc"]=sensors.smokeAdc; doc["ldr_adc"]=sensors.ldrAdc;
  doc["flame_simulated"]=sensors.flameDetected;
  JsonObject obj=doc.as<JsonObject>();
  numberOrNull(obj,"temperature_c",sensors.temperatureC,sensors.dhtValid);
  numberOrNull(obj,"humidity_pct",sensors.humidityPct,sensors.dhtValid);
  numberOrNull(obj,"temp_rate_c_s",sensors.temperatureRateCps,sensors.dhtValid);
  doc["pump_cmd"]=safety.pumpOn; doc["valve_cmd"]=safety.valveOn;
  doc["door_open_cmd"]=safety.doorOpen; doc["suppression_locked"]=safety.suppressionLocked;
  doc["ack_ready"]=safety.ackReady;
  doc["ai_available"]=n.clock && n.subscribed && n.ai.fresh(encodeMs);
  doc["ai_confidence"]=n.ai.confidence;
  doc["ai_accepted"]=n.accepted; doc["ai_rejected"]=n.rejected;
  doc["rx_dropped"]=n.rxDropped; doc["events_dropped"]=n.eventsDropped;
  doc["publish_failed"]=n.publishFailed; doc["max_loop_gap_ms"]=maxLoopGapMs;
  if (doc.overflowed() || measureJson(doc)>=capacity) return 0;
  return serializeJson(doc,buffer,capacity);
}

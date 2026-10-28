#include "network.h"
#include "network_config.h"
#include <Arduino.h>
#include "mqtt_payload.h"
#include <WiFi.h>
#include <mqtt_client.h>
#include <freertos/event_groups.h>
#include <atomic>
#include <cstring>
#include <sys/time.h>

namespace {
constexpr EventBits_t kConnected=1, kSubscribed=2;
struct RawMessage {
  char payload[AiContract::kMaxPayload];
  uint16_t length;
  bool retained;
  uint32_t receivedMs;
  uint32_t session;
};
struct Outgoing {
  SensorSnapshot sensors;
  SafetySnapshot safety;
  uint32_t now;
  uint32_t maxLoopGapMs;
};
QueueHandle_t rxQueue=nullptr, telemetryQueue=nullptr, eventQueue=nullptr, viewQueue=nullptr;
EventGroupHandle_t connection=nullptr;
esp_mqtt_client_handle_t client=nullptr;
std::atomic<uint32_t> session{0}, rxDropped{0}, eventDropped{0};
NetworkSnapshot localView;
char bootId[17];
uint32_t localMaxLoopGapMs=0; // main-loop owned, readable even while offline
uint32_t publishFailures=0; // owned by network worker
char clientId[40];
int subscribeId=-1; // only accessed from MQTT event task

int64_t utcMillis() {
  timeval t; gettimeofday(&t,nullptr);
  return static_cast<int64_t>(t.tv_sec)*1000+t.tv_usec/1000;
}

void mqttEvent(void*, esp_event_base_t, int32_t id, void* data) {
  auto* e=static_cast<esp_mqtt_event_handle_t>(data);
  if (id==MQTT_EVENT_CONNECTED) {
    ++session;
    xEventGroupClearBits(connection,kSubscribed);
    xEventGroupSetBits(connection,kConnected);
    subscribeId=esp_mqtt_client_subscribe(client,NetworkConfig::kAiTopic,1);
  } else if (id==MQTT_EVENT_SUBSCRIBED && e->msg_id==subscribeId && subscribeId>=0) {
    if (e->data && e->data_len==1 && static_cast<uint8_t>(e->data[0])<=1)
      xEventGroupSetBits(connection,kSubscribed);
  } else if (id==MQTT_EVENT_DISCONNECTED) {
    ++session;
    xEventGroupClearBits(connection,kConnected|kSubscribed);
  } else if (id==MQTT_EVENT_DATA) {
    // With a 1024-byte MQTT buffer, our <=256-byte contract fits one chunk.
    // Oversized/fragmented inputs are deliberately not reassembled or allocated.
    if (e->current_data_offset || e->data_len!=e->total_data_len ||
        e->total_data_len<=0 || e->total_data_len>static_cast<int>(AiContract::kMaxPayload)) {
      ++rxDropped; return;
    }
    if (e->topic_len!=static_cast<int>(strlen(NetworkConfig::kAiTopic)) ||
        memcmp(e->topic,NetworkConfig::kAiTopic,e->topic_len)) return;
    RawMessage raw{};
    raw.length=e->data_len; raw.retained=e->retain; raw.receivedMs=millis(); raw.session=session.load();
    memcpy(raw.payload,e->data,raw.length);
    if (xQueueSend(rxQueue,&raw,0)!=pdTRUE) ++rxDropped;
  }
}

bool publish(const char* topic, const char* body, bool retained=false) {
  // May wait for a socket only in network worker, never in Arduino loop.
  // QoS0 has no unbounded retransmission outbox; loss is reported, not retried.
  return esp_mqtt_client_publish(client,topic,body,0,0,retained)>=0;
}
void publishSnapshot(const Outgoing& o, bool event, const NetworkSnapshot& n) {
  char buffer[2048];
  if (!encodeMqttSnapshot(o.sensors,o.safety,n,o.now,o.maxLoopGapMs,utcMillis(),millis(),
                          event,buffer,sizeof(buffer)) ||
      !publish(event ? NetworkConfig::kEventTopic : NetworkConfig::kTelemetryTopic,buffer)) ++publishFailures;
}

void networkTask(void*) {
  NetworkSnapshot view; view.enabled=true; view.taskStarted=true;
  memcpy(view.bootId,bootId,sizeof(bootId));
  esp_mqtt_client_config_t cfg{};
  uint32_t hash=2166136261u;
  for (const char* p=NetworkConfig::kAvailabilityTopic; *p; ++p) hash=(hash^static_cast<uint8_t>(*p))*16777619u;
  snprintf(clientId,sizeof(clientId),"pccc-%08lx-%08lx",static_cast<unsigned long>(hash),
           static_cast<unsigned long>(ESP.getEfuseMac()));
  cfg.client_id=clientId;
  cfg.uri=NetworkConfig::kUri;
  cfg.username=NetworkConfig::kUsername[0] ? NetworkConfig::kUsername : nullptr;
  cfg.password=NetworkConfig::kMqttPassword[0] ? NetworkConfig::kMqttPassword : nullptr;
  cfg.lwt_topic=NetworkConfig::kAvailabilityTopic; cfg.lwt_msg="offline";
  cfg.lwt_qos=1; cfg.lwt_retain=1; cfg.keepalive=15;
  cfg.disable_auto_reconnect=true; cfg.task_prio=1; cfg.task_stack=6144;
  cfg.buffer_size=1024; cfg.out_buffer_size=2048; cfg.network_timeout_ms=5000;
  client=esp_mqtt_client_init(&cfg);
  if (!client || esp_mqtt_client_register_event(client,static_cast<esp_mqtt_event_id_t>(ESP_EVENT_ANY_ID),mqttEvent,nullptr)!=ESP_OK) {
    view.taskStarted=false; xQueueOverwrite(viewQueue,&view); vTaskDelete(nullptr); return;
  }
  WiFi.mode(WIFI_STA); WiFi.setAutoReconnect(false);
  WiFi.begin(NetworkConfig::kSsid,NetworkConfig::kPassword);
  uint32_t lastWifi=millis(), lastAttempt=millis()-1000, attemptSince=0;
  uint32_t retryMs=1000, seenSession=session.load(), connectedSince=0;
  bool started=false, connecting=false, wasConnected=false, wasWifi=false;
  AiTracker tracker;
  for (;;) {
    const uint32_t now=millis();
    view.wifi=WiFi.status()==WL_CONNECTED;
    if (!view.wifi && static_cast<uint32_t>(now-lastWifi)>=30000) {
      WiFi.disconnect(false,false); WiFi.begin(NetworkConfig::kSsid,NetworkConfig::kPassword); lastWifi=now;
    }
    if (view.wifi && !wasWifi) configTime(0,0,NetworkConfig::kNtpServer,"time.google.com","time.cloudflare.com");
    wasWifi=view.wifi;
    const EventBits_t bits=xEventGroupGetBits(connection);
    view.mqtt=view.wifi && (bits&kConnected);
    view.subscribed=view.mqtt && (bits&kSubscribed);
    view.clock=utcMillis()>=AiContract::kMinUnixMs;
    const uint32_t epoch=session.load();
    if (epoch!=seenSession) {
      tracker.invalidate(); seenSession=epoch;
      if (!view.mqtt) { connecting=false; lastAttempt=now; retryMs=retryMs<15000 ? retryMs*2 : 30000; }
    }
    if (!view.wifi || !view.clock) tracker.invalidate();
    if (view.mqtt && !wasConnected) {
      connectedSince=now; connecting=false; retryMs=1000;
      if (!publish(NetworkConfig::kAvailabilityTopic,"online",true)) ++publishFailures;
    }
    if (!view.mqtt && wasConnected) lastAttempt=now;
    wasConnected=view.mqtt;
    if (view.wifi && !view.mqtt && !connecting && static_cast<uint32_t>(now-lastAttempt)>=retryMs) {
      const esp_err_t result=started ? esp_mqtt_client_reconnect(client) : esp_mqtt_client_start(client);
      if (result==ESP_OK) { started=true; connecting=true; attemptSince=now; }
      else { retryMs=retryMs<15000 ? retryMs*2 : 30000; }
      lastAttempt=now;
    }
    if ((connecting && static_cast<uint32_t>(now-attemptSince)>=12000) ||
        (view.mqtt && !view.subscribed && static_cast<uint32_t>(now-connectedSince)>=10000)) {
      esp_mqtt_client_disconnect(client);
      connecting=false; lastAttempt=now; retryMs=retryMs<15000 ? retryMs*2 : 30000;
    }
    RawMessage raw{};
    for (int i=0;i<4 && xQueueReceive(rxQueue,&raw,0)==pdTRUE;++i) {
      if (!view.subscribed || raw.session!=session.load()) { ++rxDropped; continue; }
      // A CONNECTED callback may arrive after this pass sampled the epoch.
      // Bind the accepted sample to its actual session, not the older loop tick.
      if (seenSession!=raw.session) { tracker.invalidate(); seenSession=raw.session; }
      view.lastReject=tracker.accept(raw.payload,raw.length,raw.retained,utcMillis(),raw.receivedMs);
      if (view.lastReject==AiReject::None) ++view.accepted; else ++view.rejected;
    }
    view.ai=tracker.signal(); view.rxDropped=rxDropped.load();
    view.eventsDropped=eventDropped.load(); view.publishFailed=publishFailures;
    xQueueOverwrite(viewQueue,&view);
    if (view.subscribed) {
      Outgoing msg;
      // At most one event plus latest telemetry per pass. All socket work is here.
      if (xQueueReceive(eventQueue,&msg,0)==pdTRUE) publishSnapshot(msg,true,view);
      if (xQueueReceive(telemetryQueue,&msg,0)==pdTRUE) publishSnapshot(msg,false,view);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}
}

void beginNetwork() {
  snprintf(bootId,sizeof(bootId),"%08lx%08lx",static_cast<unsigned long>(esp_random()),static_cast<unsigned long>(esp_random()));
  memcpy(localView.bootId,bootId,sizeof(bootId));
  localView.enabled=NetworkConfig::kEnabled;
  if (!NetworkConfig::kEnabled) return;
  rxQueue=xQueueCreate(4,sizeof(RawMessage));
  telemetryQueue=xQueueCreate(1,sizeof(Outgoing));
  eventQueue=xQueueCreate(8,sizeof(Outgoing));
  viewQueue=xQueueCreate(1,sizeof(NetworkSnapshot));
  connection=xEventGroupCreate();
  if (!rxQueue || !telemetryQueue || !eventQueue || !viewQueue || !connection) return;
  // DOIT ESP32 is dual-core; loopTask stays on core1. Networking waits on core0.
  localView.taskStarted=xTaskCreatePinnedToCore(networkTask,"pccc-network",10240,nullptr,1,nullptr,0)==pdPASS;
}
const NetworkSnapshot& pollNetwork() {
  if (viewQueue) xQueuePeek(viewQueue,&localView,0);
  return localView;
}
uint32_t maxObservedLocalLoopGap() { return localMaxLoopGapMs; }
void sendNetworkSnapshot(const SensorSnapshot& sensors,const SafetySnapshot& safety,
                         uint32_t now,uint32_t maxLoopGapMs,bool event) {
  localMaxLoopGapMs=maxLoopGapMs;
  if (!localView.taskStarted) return;
  Outgoing msg{sensors,safety,now,maxLoopGapMs};
  if (event) {
    if (xQueueSend(eventQueue,&msg,0)!=pdTRUE) ++eventDropped;
  } else xQueueOverwrite(telemetryQueue,&msg);
}

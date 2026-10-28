#include "ai_contract.h"
#include "safety.h"
#include "mqtt_payload.h"
#include <ArduinoJson.h>
#include <cassert>
#include <cstdio>
#include <string>
#include <cstring>

namespace {
constexpr int64_t epoch=1793152800000LL;
std::string packet(const char* label="lua", const char* confidence="0.93",int64_t ts=epoch) {
  return std::string("{\"v\":1,\"nhan\":\"")+label+"\",\"do_tin_cay\":"+confidence+",\"ts_ms\":"+std::to_string(ts)+"}";
}
AiReject accept(AiTracker& t,const std::string& p,int64_t utc=epoch,uint32_t mono=100,bool retained=false) {
  return t.accept(p.data(),p.size(),retained,utc,mono);
}
SensorSnapshot healthy(uint32_t now) {
  SensorSnapshot s;
  s.fastValid=s.ldrValid=s.dhtValid=s.dhtEverValid=true;
  s.fastSampleMs=s.ldrSampleMs=s.dhtSuccessMs=now;
  s.smokeAdc=1000; s.ldrAdc=2000; s.temperatureC=28; s.humidityPct=45;
  s.temperatureRateCps=0; s.dhtAttempts=1;
  return s;
}
void parserCases() {
  AiTracker t;
  assert(accept(t,packet())==AiReject::None);
  assert(t.signal().level==2 && t.signal().fresh(15099) && !t.signal().fresh(15100));
  const uint32_t receipt=t.signal().receivedMs;
  const std::string invalid[]={"", "{", "[]", "null", "{}", "{\"v\":true}",
    "{\"v\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.9}",
    "{\"v\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.9,\"ts_ms\":\"1793152800001\"}",
    "{\"v\":1,\"v\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.9,\"ts_ms\":1793152800001}",
    "{'v':1,'nhan':'lua','do_tin_cay':0.93,'ts_ms':1793152800000}",
    "{\"v\\u0000bad\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.93,\"ts_ms\":1793152800000}",
    "{v:1,nhan:\"lua\",do_tin_cay:0.93,ts_ms:1793152800000}",
    packet("lua","+0.93"),packet("lua","01"),packet("lua",".9"),packet("lua","1."),
    packet()+"{}", packet()+"garbage", packet("unknown"),packet("lua","\"0.9\""),
    packet("lua","true"),packet("lua","null"),packet("lua","-0.1"),packet("lua","1.1"),
    packet("lua","NaN"),packet("lua","1e999"),packet("lua\\u0000junk"),std::string(257,'x')};
  for(const auto& p:invalid) {
    assert(accept(t,p,epoch+1,200)!=AiReject::None);
    assert(t.signal().receivedMs==receipt && t.signal().level==2);
  }
  assert(accept(t,packet(),epoch,200,true)==AiReject::Retained);
  assert(accept(t,packet(),0,200)==AiReject::Clock);
  assert(accept(t,packet(),epoch,200)==AiReject::Replay);
  assert(accept(t,packet("lua","0.9",epoch-1))==AiReject::Replay);
  assert(accept(t,packet("lua","0.9",epoch-15000))==AiReject::Timestamp);
  assert(accept(t,packet("lua","0.9",epoch+2001))==AiReject::Timestamp);
  t.invalidate(); assert(!t.signal().fresh(100));
  assert(accept(t,packet())==AiReject::Replay); // reconnect does not reset watermark
  assert(accept(t,packet("khoi","0.8",epoch+1),epoch+1)==AiReject::None && t.signal().level==1);
  assert(accept(t,packet("lua","0.799",epoch+2),epoch+2)==AiReject::None && t.signal().level==0);
  assert(accept(t,packet("binh_thuong","1",epoch+3),epoch+3)==AiReject::None && t.signal().level==0);
  AiTracker old;
  assert(accept(old,packet("lua","1",epoch-14999))==AiReject::None);
  assert(old.signal().fresh(100) && !old.signal().fresh(101));
  AiTracker future;
  assert(accept(future,packet("lua","1",epoch+2000))==AiReject::None);
  assert(!future.signal().fresh(15100)); // future tolerance must not extend monotonic TTL
  AiTracker wrap;
  assert(accept(wrap,packet(),epoch,UINT32_MAX-10)==AiReject::None);
  assert(wrap.signal().fresh(5)); assert(!wrap.signal().fresh(15000));
  std::puts("PASS strict AI schema, malformed/type/range/size/duplicate/trailing/NUL, retained, replay, clock, age, TTL/rollover");
}
void telemetryJson() {
  SensorSnapshot sensors; SafetySnapshot safety; NetworkSnapshot net;
  char buffer[2048];
  assert(encodeMqttSnapshot(sensors,safety,net,100,23,0,100,false,buffer,sizeof(buffer))>0);
  StaticJsonDocument<3072> doc;
  assert(!deserializeJson(doc,buffer));
  assert(doc["temperature_c"].isNull() && doc["humidity_pct"].isNull() && doc["temp_rate_c_s"].isNull());
  assert(doc["v"].as<int>()==1 && doc["ts_ms"].as<int64_t>()==0);
  assert(!doc["ai_available"].as<bool>());
  sensors=healthy(100); net.clock=net.subscribed=true;
  net.ai.received=true; net.ai.receivedMs=100; net.ai.remainingMs=15000;
  safety.localLevel=2; safety.aiLevel=0; safety.dangerLevel=2;
  safety.activeReasons=REASON_SMOKE_DANGER; safety.state=SystemState::FIRE_SUPPRESSION;
  assert(encodeMqttSnapshot(sensors,safety,net,100,23,epoch,100,true,buffer,sizeof(buffer))>0);
  assert(!deserializeJson(doc,buffer));
  assert(doc["temperature_c"].as<float>()==28 && doc["local_level"].as<int>()==2);
  assert(doc["ai_available"].as<bool>() && doc["source"].as<std::string>()=="LOCAL");
  assert(doc["record_type"].as<std::string>()=="EVENT" && doc["max_loop_gap_ms"].as<int>()==23);
  assert(!encodeMqttSnapshot(sensors,safety,net,100,23,epoch,100,true,buffer,8));
  std::puts("PASS actual MQTT telemetry/event encoder, finite/null measurements, source/levels/status, buffer bound");
}
void fusion() {
  SafetyController c;
  auto s=healthy(100); c.update(s,100);
  AiTracker ai; assert(accept(ai,packet())==AiReject::None);
  c.update(s,100,ai.signal());
  assert(c.snapshot().pumpOn && c.snapshot().doorOpen && c.snapshot().localLevel==0);
  assert(c.snapshot().aiLevel==2 && !strcmp(triggerSource(c.snapshot().latchedReasons),"AI"));
  s=healthy(15100); c.update(s,15100,ai.signal());
  assert(c.snapshot().state==SystemState::RECOVERY && c.snapshot().doorOpen && !c.snapshot().pumpOn);
  c.update(healthy(18100),18100,ai.signal());
  s=healthy(18120); s.ackPressedRaw=true; c.update(s,18120,ai.signal());
  s=healthy(18170); s.ackPressedRaw=true; c.update(s,18170,ai.signal());
  assert(c.snapshot().state==SystemState::NORMAL && !c.snapshot().doorOpen);
  SafetyController local;
  s=healthy(100); s.smokeAdc=3000;
  AiSignal normal; normal.received=true; normal.receivedMs=100; normal.remainingMs=15000;
  local.update(s,100,normal);
  assert(local.snapshot().localLevel==2 && local.snapshot().dangerLevel==2 && local.snapshot().pumpOn);
  local.update(s,100,ai.signal());
  assert(!strcmp(triggerSource(local.snapshot().latchedReasons),"LOCAL+AI"));
  // A disconnect invalidates AI, never a concurrent local hazard.
  ai.invalidate(); local.update(s,100,ai.signal()); assert(local.snapshot().pumpOn);
  SafetyController timeout;
  for(uint32_t now=0;now<=61000;now+=1000) {
    AiSignal fire; fire.received=true; fire.level=2; fire.receivedMs=now; fire.remainingMs=15000;
    s=healthy(now); s.ackPressedRaw=now>=100; timeout.update(s,now,fire);
  }
  assert(timeout.snapshot().suppressionLocked && !timeout.snapshot().pumpOn && timeout.snapshot().doorOpen);
  assert(!timeout.snapshot().ackReady); // continuously renewed AI cannot bypass timeout or allow ACK
  for(uint32_t now=62000;now<=65000;now+=1000) {
    s=healthy(now); s.ackPressedRaw=true; timeout.update(s,now);
  }
  assert(timeout.snapshot().ackReady && timeout.snapshot().state==SystemState::RECOVERY); // held button insufficient
  s=healthy(65010); timeout.update(s,65010); s=healthy(65060); timeout.update(s,65060);
  s=healthy(65070); s.ackPressedRaw=true; timeout.update(s,65070);
  s=healthy(65120); s.ackPressedRaw=true; timeout.update(s,65120);
  assert(timeout.snapshot().state==SystemState::NORMAL && !timeout.snapshot().suppressionLocked);
  std::puts("PASS AI/local max fusion, source masks, expiry/disconnect, recovery/ACK, sustained AI timeout lock");
}
}
int main() { parserCases(); fusion(); telemetryJson(); }

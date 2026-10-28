// S8 regression scaffold: real C++ core, synthetic inputs/clock, no MCU/model.
#include "safety.h"
#include "ldr_detector.h"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
void require(bool ok,const char* message) { if (!ok) throw std::runtime_error(message); }
SensorSnapshot healthy(uint32_t now,int run) {
  SensorSnapshot s; s.fastValid=s.ldrValid=s.dhtValid=s.dhtEverValid=true;
  s.fastSampleMs=s.ldrSampleMs=s.dhtSuccessMs=now; s.dhtAttempts=1;
  s.smokeAdc=1000+run; s.ldrAdc=2000+run; s.temperatureC=28; s.humidityPct=45; s.temperatureRateCps=0;
  return s;
}
AiSignal ai(uint8_t level,uint32_t now) {
  AiSignal a; a.received=true;a.level=level;a.confidence=.93;a.receivedMs=now;a.remainingMs=15000;return a;
}
void scenario(int tc,int run) {
  const uint32_t start=run==20 ? UINT32_MAX-20000 : static_cast<uint32_t>(run*100000);
  auto input=[&](uint32_t elapsed) { return healthy(start+elapsed,run); };
  SafetyController c;
  auto s=input(0);c.update(s,start);
  switch(tc) {
    case 1:
      for(uint32_t t=100;t<=2000;t+=100) { c.update(input(t),start+t,ai(0,start+t));
        require(c.snapshot().state==SystemState::NORMAL && !c.snapshot().pumpOn && !c.snapshot().doorOpen,"normal outputs"); }
      break;
    case 2:
      s=input(100);s.smokeAdc=1800+run;c.update(s,start+100);
      require(c.snapshot().state==SystemState::WARNING && c.snapshot().buzzerOn && !c.snapshot().pumpOn,"smoke warning");
      s=input(200);s.smokeAdc=1699;c.update(s,start+200);
      require(c.snapshot().state==SystemState::RECOVERY,"warning clears to recovery");break;
    case 3:
      s=input(100);s.smokeAdc=2800+run;c.update(s,start+100);
      require(c.snapshot().pumpOn && c.snapshot().valveOn && c.snapshot().doorOpen,"smoke danger loads");break;
    case 4: {
      LdrDetector detector;require(!detector.update(750+run,true),"LDR baseline");
      s=input(100);s.flameDetected=detector.update(500-run,true);c.update(s,start+100);
      require(c.snapshot().pumpOn && (c.snapshot().activeReasons&REASON_FLAME),"LDR fire path");
      s=input(200);s.flameDetected=detector.update(600,true);c.update(s,start+200);
      require(c.snapshot().pumpOn,"LDR hysteresis hold");
      s=input(300);s.flameDetected=detector.update(750,true);c.update(s,start+300);
      require(!c.snapshot().pumpOn && c.snapshot().doorOpen,"LDR clear keeps door");break;
    }
    case 5:
      s=input(3000);s.temperatureRateCps=2.0f+run*.01f;c.update(s,start+3000);
      require(c.snapshot().pumpOn && (c.snapshot().activeReasons&REASON_TEMPERATURE_RATE),"rate danger rule");break;
    case 6: {
      AiTracker tracker;const int64_t utc=1793152800000LL+run;
      const std::string p="{\"v\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.93,\"ts_ms\":"+std::to_string(utc)+"}";
      require(tracker.accept(p.data(),p.size(),false,utc,start+100)==AiReject::None,"AI mock parser");
      c.update(input(100),start+100,tracker.signal());
      require(c.snapshot().localLevel==0 && c.snapshot().aiLevel==2 && c.snapshot().pumpOn,"AI mock fire fusion");break;
    }
    case 7:
      for(int adc : {1799,1800,1700,1699,2799,2800,2700,2699}) {
        s=input(100);s.smokeAdc=adc;c.update(s,start+100);
        if(adc==1799 || adc==1699) require(c.snapshot().dangerLevel==0,"warning lower boundary");
        if(adc==1800 || adc==1700 || adc==2799 || adc==2699) require(c.snapshot().dangerLevel==1,"warning hysteresis boundary");
        if(adc==2800 || adc==2700) require(c.snapshot().dangerLevel==2,"danger hysteresis boundary");
      }
      break;
    case 8: {
      const AiSignal fire=ai(2,start+100);c.update(input(100),start+100,fire);
      c.update(input(15100),start+15100,fire);
      require(c.snapshot().state==SystemState::RECOVERY && !c.snapshot().pumpOn && c.snapshot().doorOpen,"AI TTL expiry");
      s=input(15200);s.smokeAdc=3000;c.update(s,start+15200,fire);
      require(c.snapshot().localLevel==2 && c.snapshot().pumpOn,"expired AI cannot disable local");break;
    }
    case 9: {
      AiTracker tracker;const int64_t utc=1793152800000LL;
      const std::string good="{\"v\":1,\"nhan\":\"lua\",\"do_tin_cay\":0.93,\"ts_ms\":1793152800000}";
      require(tracker.accept(good.data(),good.size(),false,utc,start)==AiReject::None,"initial good message");
      const std::string cases[]={"{", "{}", "[]", "{'v':1}", std::string(257,'x')};
      const std::string& bad=cases[(run-1)%5];
      require(tracker.accept(bad.data(),bad.size(),false,utc+100,start+100)!=AiReject::None,"bad message rejected");
      require(tracker.signal().receivedMs==start,"bad message did not refresh");
      require(!tracker.signal().fresh(start+15000),"bad message cannot extend TTL");break;
    }
    case 10:
      s=input(100);
      if(run%3==0) s.smokeAdc=3000;else if(run%3==1) s.flameDetected=true;else s.temperatureC=60;
      c.update(s,start+100,ai(0,start+100));
      require(c.snapshot().localLevel==2 && c.snapshot().aiLevel==0 && c.snapshot().pumpOn,"normal AI cannot lower local danger");break;
    case 12:
      for(uint32_t t=0;t<=59000;t+=1000) c.update(input(t),start+t,ai(2,start+t));
      c.update(input(59999),start+59999,ai(2,start+59999));require(c.snapshot().pumpOn,"before timeout");
      for(uint32_t t=60000;t<=70000;t+=1000) {
        c.update(input(t),start+t,ai(2,start+t));
        require(c.snapshot().suppressionLocked && !c.snapshot().pumpOn && c.snapshot().doorOpen,"timeout and no reactivation");
      }break;
    case 13: {
      SafetyController held;
      for(uint32_t t : {0u,100u,200u,3500u}) {
        s=input(t);s.ackPressedRaw=true;s.flameDetected=t==100;held.update(s,start+t);
      }
      require(held.snapshot().state==SystemState::RECOVERY && held.snapshot().ackReady,"held ACK cannot auto reset");
      for(uint32_t t : {3510u,3560u,3570u,3620u}) {
        s=input(t);s.ackPressedRaw=t>=3570;held.update(s,start+t);
      }
      require(held.snapshot().state==SystemState::NORMAL && !held.snapshot().doorOpen && held.snapshot().latchedReasons==0,"fresh safe ACK closes door");break;
    }
    default:throw std::runtime_error("unknown host case");
  }
}
}
int main(int argc,char**argv) {
  if(argc!=2) { std::cerr<<"Usage: host_s8 output.csv\n";return 2; }
  std::ofstream out(argv[1]);if(!out) return 2;
  out<<"execution_domain,scenario_id,run,status,observed,model_id,clock\n";
  int passed=0,failed=0,deferred=0;
  for(int tc=1;tc<=13;++tc) for(int run=1;run<=20;++run) {
    const std::string id="TC"+std::string(tc<10 ? "0" : "")+std::to_string(tc);
    std::string status="PASS",message="C++ core assertions passed; synthetic input; no MCU/model";
    if(tc==11) { status="DEFERRED";message="Image confusion metrics require real model and labeled images";++deferred; }
    else try { scenario(tc,run);++passed; } catch(const std::exception& e) { status="FAIL";message=e.what();++failed; }
    out<<"HOST_SYNTHETIC,"<<id<<','<<run<<','<<status<<','<<message<<",MOCK_ONLY,VIRTUAL_MILLIS\n";
  }
  std::cout<<"HOST_SYNTHETIC: "<<passed<<" PASS / "<<failed<<" FAIL / "<<deferred<<" DEFERRED. Not260 Wokwi acceptance runs.\n";
  return failed ? 1 : 0;
}

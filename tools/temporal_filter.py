"""Opt-in confirmation. Does not invent normal or reuse an old prediction."""
import math

class TemporalGate:
    def __init__(self,seconds=0,frames=3,max_gap=5):
        if (not math.isfinite(seconds) or seconds<0 or type(frames) is not int or frames<1
                or not math.isfinite(max_gap) or max_gap<=0):raise ValueError('invalid temporal confirmation config')
        self.seconds,self.frames,self.max_gap=seconds,frames,max_gap
        self.label=None;self.started=None;self.last=None;self.count=0
    def update(self,prediction,now):
        if not math.isfinite(now):raise ValueError('invalid monotonic time')
        if not self.seconds:return prediction
        if prediction is None or prediction.label not in ('lua','khoi') or prediction.confidence<.8:
            self.label=None;self.started=None;self.last=None;self.count=0
            return None
        if self.label!=prediction.label or self.last is None or not 0<=now-self.last<=self.max_gap:
            self.label=prediction.label;self.started=now;self.count=0
        self.last=now;self.count+=1
        return prediction if self.count>=self.frames and now-self.started>=self.seconds else None

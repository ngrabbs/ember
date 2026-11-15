"""Overlapping bounded IQ windows; outer-frame identity for overlap suppression."""
from collections import OrderedDict
import hashlib
import numpy as np
from packet_radio import decode_iq, decode_iq_coherent

class WindowBuffer:
    def __init__(self, rate=40000, window_seconds=8, stride_seconds=4):
        self.window=int(rate*window_seconds);self.stride=int(rate*stride_seconds)
        if not 0<self.stride<self.window:raise ValueError('Invalid window/stride')
        self.buffer=np.empty(0,np.complex64);self.offset=0
    def push(self, samples):
        self.buffer=np.concatenate((self.buffer,np.asarray(samples,np.complex64)))
        while len(self.buffer)>=self.window:
            yield self.offset,self.buffer[:self.window].copy()
            self.buffer=self.buffer[self.stride:];self.offset+=self.stride
    def tail(self):
        return self.offset,self.buffer.copy()

class Decoder:
    def __init__(self, validator, rate=40000):
        self.validator=validator;self.rate=rate;self.seen=OrderedDict()
        self.overlap_duplicates=0;self.rejected=0
    def decode(self, offset, samples):
        # Run both detectors: one successful strong burst must not hide a weak one.
        rows=decode_iq(samples,self.rate)+decode_iq_coherent(samples,self.rate)
        accepted=[]
        for row in rows:
            payload=row.pop('payload')
            key=(row['sequence'],hashlib.sha256(payload).hexdigest())
            if key in self.seen:
                self.overlap_duplicates+=1;continue
            try:decoded=self.validator(payload)
            except (ValueError,KeyError):self.rejected+=1;continue
            self.seen[key]=None
            if len(self.seen)>4096:self.seen.popitem(last=False)
            accepted.append(dict(row,hex=payload.hex(),sha256=key[1],decoded=decoded,
                                 window_start_sample=offset))
        return accepted

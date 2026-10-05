"""Frames across decode-window boundaries and overlap suppression."""
import unittest
import numpy as np
from packet_radio import waveform,BASEBAND_OFFSET
from stream_decoder import WindowBuffer,Decoder

class StreamingTests(unittest.TestCase):
    def test_crossing_boundary_and_repeated_payload(self):
        rate=40000;payload=bytes(range(128));iq=np.zeros(rate*18,np.complex64)
        # First frame crosses the 8s window edge; second has identical inner bytes.
        for start,sequence in ((7.5,10),(12.5,11)):
            w=waveform(payload,sequence,rate);n=np.arange(len(w))
            w*=np.exp(-2j*np.pi*BASEBAND_OFFSET*n/rate)
            at=int(start*rate);iq[at:at+len(w)]+=w
        rng=np.random.default_rng(7);iq+=.001*(rng.normal(size=len(iq))+1j*rng.normal(size=len(iq)))
        b=WindowBuffer();d=Decoder(lambda p: {'valid':p==payload});rows=[]
        for at in range(0,len(iq),5000):
            for offset,w in b.push(iq[at:at+5000]):rows+=d.decode(offset,w)
        rows+=d.decode(*b.tail())
        self.assertEqual([x['sequence'] for x in rows],[10,11])
        self.assertEqual([bytes.fromhex(x['hex']) for x in rows],[payload,payload])
        self.assertGreater(d.overlap_duplicates,0)
    def test_invalid_native_payload_rejected(self):
        rate=40000;w=waveform(b'invalid',1,rate);n=np.arange(len(w))
        w*=np.exp(-2j*np.pi*BASEBAND_OFFSET*n/rate)
        iq=np.concatenate((np.zeros(rate),w,np.zeros(rate)))
        def reject(p):raise ValueError('invalid native packet')
        d=Decoder(reject);self.assertEqual(d.decode(0,iq),[]);self.assertGreater(d.rejected,0)

if __name__=='__main__':unittest.main()

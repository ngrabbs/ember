"""Software-only unknown carrier/timing and integrity checks."""
import unittest
import numpy as np
from packet_radio import waveform,frame,decode_iq,decode_iq_coherent,BASEBAND_OFFSET,BAUD,DEVIATION

class PacketRadioTests(unittest.TestCase):
    def setUp(self):
        self.payload=bytes(range(128));self.rate=40000
    def samples(self,cfo):
        w=waveform(self.payload,9,self.rate)
        n=np.arange(len(w));w=w*np.exp(-2j*np.pi*(BASEBAND_OFFSET-cfo)*n/self.rate)
        # Noninteger timing offset and deterministic receiver noise.
        t=np.arange(len(w))-3.4
        w=np.interp(t,n,w.real,left=0,right=0)+1j*np.interp(t,n,w.imag,left=0,right=0)
        a=np.concatenate((np.zeros(self.rate),w,np.zeros(self.rate)))
        rng=np.random.default_rng(14)
        return a+.001*(rng.normal(size=len(a))+1j*rng.normal(size=len(a)))
    def test_packet_carrier_and_fractional_timing(self):
        for cfo in (0,4500,-4500):
            with self.subTest(cfo=cfo):
                rows=decode_iq(self.samples(cfo),self.rate)
                self.assertEqual([(x['sequence'],x['payload']) for x in rows],[(9,self.payload)])
    def test_truncated_packet(self):
        self.assertEqual(decode_iq(self.samples(0)[:self.rate+8000],self.rate),[])
    def test_integral_symbol_waveform_preserves_frequency_and_phase(self):
        payload=b'\x00\xff\x55';bits=np.unpackbits(np.frombuffer(frame(payload,9),np.uint8))
        for rate in (307200,614400,750000):
            with self.subTest(rate=rate):
                sps=rate//BAUD;guard=int(rate*.03)
                signal=waveform(payload,9,rate)[guard:-guard]
                frequencies=np.repeat(BASEBAND_OFFSET+DEVIATION*(2*bits.astype(float)-1),sps)
                expected=.08*np.exp(2j*np.pi*np.cumsum(frequencies)/rate)
                np.testing.assert_allclose(signal,expected,rtol=2e-6,atol=2e-7)
                self.assertEqual(len(signal),len(bits)*sps)
    def test_noise_does_not_make_packet(self):
        rng=np.random.default_rng(15)
        noise=.001*(rng.normal(size=120000)+1j*rng.normal(size=120000))
        self.assertEqual(decode_iq(noise),[])
        self.assertEqual(decode_iq_coherent(noise),[])
    def test_weak_packet_two_tone_integration(self):
        w=waveform(self.payload,9,self.rate);n=np.arange(len(w))
        w=w*np.exp(-2j*np.pi*(BASEBAND_OFFSET-810)*n/self.rate)
        a=np.concatenate((np.zeros(self.rate),w,np.zeros(self.rate)))
        rng=np.random.default_rng(33)
        a+=.04*(rng.normal(size=len(a))+1j*rng.normal(size=len(a)))
        rows=decode_iq_coherent(a,self.rate)
        self.assertEqual([(x['sequence'],x['payload']) for x in rows],[(9,self.payload)])

if __name__=='__main__':unittest.main()

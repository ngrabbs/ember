import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from live import Windows, Decoder, RATE
from modem import frame
from codec import encode, DICTIONARY

class LiveTests(unittest.TestCase):
    def test_boundaries_and_duplicate_forwarding(self):
        message=next(m for m in DICTIONARY['messages'] if m['name']=='POWER_STATUS')
        packets=[encode('POWER_STATUS',sequence=i,source=2,target=1,source_boot_id=123,
                        uptime_ms=i*10000,payload={f['name']:0 for f in message['fields']}) for i in range(3)]
        raw=np.zeros(12*RATE,np.complex64)
        for packet,offset in zip(packets,[0.1,3.7,10.3]):
            bits=np.unpackbits(np.frombuffer(frame(packet,42),np.uint8))
            symbols=1-2*(np.cumsum(bits)%2).astype(float)
            waveform=np.repeat(symbols,160).astype(np.complex64)
            waveform*=np.exp(-2j*np.pi*7200*np.arange(len(waveform))/RATE)
            start=int(offset*RATE);raw[start:start+len(waveform)]=waveform
        with tempfile.TemporaryDirectory() as tmp, patch('live.socket.socket') as sock:
            d=Decoder(Path(tmp),True);w=Windows()
            for at in range(0,len(raw),8192):
                for job in w.feed(raw[at:at+8192]):d.process(*job)
            d.process(*w.finish())
            self.assertEqual([p['hex'] for p in d.packets],[p.hex() for p in packets])
            self.assertEqual(d.forwarded,3)
            self.assertEqual(sock.return_value.__enter__.return_value.sendto.call_count,3)
            self.assertEqual(len((Path(tmp)/'packets.jsonl').read_text().splitlines()),3)
    def test_window_bytes_and_arbitrary_chunk_boundaries(self):
        raw=np.arange(6*RATE+17,dtype=np.float32).astype(np.complex64)
        for chunk_size in [8192, 5*RATE, 13791]:
            w=Windows();jobs=[]
            for at in range(0,len(raw),chunk_size):jobs.extend(w.feed(raw[at:at+chunk_size]))
            jobs.append(w.finish())
            for start, samples in jobs:
                np.testing.assert_array_equal(samples,raw[start:start+len(samples)])
            self.assertEqual([start for start,_ in jobs],[0,RATE,2*RATE,3*RATE])
    def test_noise_not_forwarded(self):
        rng=np.random.default_rng(3)
        with tempfile.TemporaryDirectory() as tmp, patch('live.socket.socket') as sock:
            d=Decoder(Path(tmp),True)
            d.process(0,(rng.normal(size=4*RATE)+1j*rng.normal(size=4*RATE)).astype(np.complex64))
            self.assertFalse(d.packets);sock.assert_not_called()

if __name__=='__main__':unittest.main()

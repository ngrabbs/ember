import tempfile
import unittest
import json
import sys
import time
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from live import Windows, Decoder, RATE, run, FPGA_SHA
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
    def test_storage_backlog_stops_without_forwarding_or_hanging(self):
        # Simulate a stalled SD card while USB samples arrive faster than storage.
        radio=MagicMock();stream=MagicMock();radio.get_rx_stream.return_value=stream
        radio.get_rx_rate.return_value=RATE;radio.get_rx_freq.return_value=437e6
        radio.get_rx_gain.return_value=0
        def recv(buf,md,timeout):
            buf[:]=0;return 8192
        stream.recv.side_effect=recv
        fake=SimpleNamespace(usrp=SimpleNamespace(MultiUSRP=lambda _:radio,
            StreamArgs=lambda *_:SimpleNamespace()),types=SimpleNamespace(
            RXMetadata=lambda:SimpleNamespace(error_code=0),RXMetadataErrorCode=SimpleNamespace(none=0),
            TuneRequest=lambda x:x,StreamCMD=lambda x:SimpleNamespace(mode=x),
            StreamMode=SimpleNamespace(start_cont=1,stop_cont=2)))
        original=Windows.feed
        def slow(self,samples):
            time.sleep(.05);yield from original(self,samples)
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'usrp_b210_fpga.bin').write_bytes(b'test only')
            args=SimpleNamespace(images=d,output=d/'capture',frequency=437e6,channel=0,gain=0,seconds=1,forward=True)
            with patch.dict(sys.modules,uhd=fake),patch('live.hashlib.sha256') as sha,patch.object(Windows,'feed',slow),patch('live.socket.socket') as sock:
                sha.return_value.hexdigest.return_value=FPGA_SHA
                self.assertEqual(run(args),1)
                sock.assert_not_called()
            report=json.loads((args.output/'result.json').read_text())
            self.assertIn('storage backlog exceeded 64 chunks',report['errors'])
            self.assertEqual(report['forwarded'],0)
            self.assertEqual(stream.issue_stream_cmd.call_args[0][0].mode,2)
    def test_noise_not_forwarded(self):
        rng=np.random.default_rng(3)
        with tempfile.TemporaryDirectory() as tmp, patch('live.socket.socket') as sock:
            d=Decoder(Path(tmp),True)
            d.process(0,(rng.normal(size=4*RATE)+1j*rng.normal(size=4*RATE)).astype(np.complex64))
            self.assertFalse(d.packets);sock.assert_not_called()

if __name__=='__main__':unittest.main()

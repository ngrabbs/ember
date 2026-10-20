"""Cross-language packet vector, corruption rejection, and a real UDP socket."""
import importlib.util,json,socket,subprocess,sys,tempfile,time,unittest,zlib,struct
from pathlib import Path
root=Path(__file__).resolve().parents[3]
receiver=root/'ground/lte/scripts/direct-bench-receiver.py'
spec=importlib.util.spec_from_file_location('receiver',receiver);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class TestReceiver(unittest.TestCase):
 def test_cpp_vector_and_corruption(self):
  packet=Path('/tmp/ember-bench-golden.bin').read_bytes();p=bytearray(128)
  struct.pack_into('!4sBBHIIIHHII',p,0,b'ELTB',1,0,32,0x12345678,5,99,128,0,0,7)
  p[32:]=bytes((0x12345678+5+i)&255 for i in range(32,128));struct.pack_into('!I',p,24,zlib.crc32(p))
  self.assertEqual(packet,bytes(p));self.assertEqual(module.decode(packet)['seq'],5)
  for index in (0,4,6,8,20,24,28,32,127):
   bad=bytearray(packet);bad[index]^=1
   with self.assertRaises(ValueError):module.decode(bytes(bad))
 def test_socket(self):
  s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));port=s.getsockname()[1];s.close()
  p=subprocess.Popen([sys.executable,str(receiver),'--run',str(0x12345678),'--port',str(port),'--seconds','1'],stdout=subprocess.PIPE,text=True)
  try:
   self.assertEqual(json.loads(p.stdout.readline())['event'],'receiver_ready');packet=Path('/tmp/ember-bench-golden.bin').read_bytes()
   with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as tx:
    for data in (packet,packet,b'bad'):tx.sendto(data,('127.0.0.1',port))
   rows=[json.loads(x)for x in p.communicate(timeout=3)[0].splitlines()]
   self.assertEqual(p.returncode,0);self.assertEqual(rows[-1]['unique'],1);self.assertEqual(rows[-1]['duplicates'],1);self.assertEqual(rows[-1]['bad'],1)
  finally:
   if p.poll()is None:p.kill();p.wait()
class TestSummary(unittest.TestCase):
 def test_skips_are_not_losses_and_unknown_is_held(self):
  spec=importlib.util.spec_from_file_location('summary',root/'ground/lte/scripts/direct-bench-summary.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  tx=[dict(event='run_start',run=1,boot=7,bytes=128,seconds=1),dict(event='attempt',run=1,seq=0),dict(event='attempt',run=1,seq=5),dict(event='accepted',run=1,seq=0),dict(event='accepted',run=1,seq=5),dict(event='run_done',run=1,reason='duration',slots=10,offered=2,accepted=2,rejected=0,unknown=0,skipped=8,unreached=0)]
  rx=[dict(event='received',run=1,boot=7,bytes=128,seq=0,monotonic_ns=100),dict(event='received',run=1,boot=7,bytes=128,seq=5,monotonic_ns=500000100)]
  rx.append(dict(event='receiver_done',run=1,ended_monotonic_ns=2000000100))
  r=m.summarize(tx,rx,1);self.assertEqual(r['accepted_missing'],[]);self.assertEqual(r['skipped'],8);self.assertEqual(r['received_kbps'],2.048)
  tx[-2]['event']='unknown';tx[-1].update(accepted=1,unknown=1);r=m.summarize(tx,rx,1);self.assertFalse(r['measurement_complete']);self.assertIsNone(r['received_kbps']);self.assertEqual(r['unknown_received'],[5])
  with self.assertRaises(ValueError):m.summarize(tx+[dict(log_drops=1)],rx,1)
if __name__=='__main__':unittest.main()

"""Queue, expiry, idempotent submission and private IPC checks; no RF hardware."""
import tempfile,threading,unittest
from pathlib import Path
from binary_injector import PacketQueue
from radio_control import request
from radio_service import ControlServer

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.now=0;self.events=[]
        self.q=PacketQueue(prepare=lambda p,s:bytes(8*len(p)),clock=lambda:self.now,event=lambda **r:self.events.append(r))
    def test_duplicate_and_conflicting_identity(self):
        first=self.q.enqueue('0102','same')
        self.assertEqual(self.q.enqueue('0102','same')['sequence'],first['sequence'])
        self.assertEqual(self.q.pending.qsize(),1)
        with self.assertRaises(ValueError):self.q.enqueue('03','same')
    def test_capacity_and_expiry(self):
        self.q.enqueue('01','a');self.q.enqueue('02','b')
        with self.assertRaises(ValueError):self.q.enqueue('03','c')
        self.now=16;self.assertIsNone(self.q.take());self.assertEqual(self.q.expired,2)
        self.assertEqual(self.q.enqueue('03','c')['sequence'],3)
    def test_invalid_and_stopping(self):
        for value in ('', '00'*241,'zz'):
            with self.assertRaises(ValueError):self.q.enqueue(value,'test')
        self.q.accepting=False
        with self.assertRaises(ValueError):self.q.enqueue('01','test')
    def test_private_socket_and_duplicate_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'control.sock';stop=threading.Event()
            class FakeInjector:pass
            injector=FakeInjector();injector.queue=self.q
            server=ControlServer(path,injector,lambda:dict(accepted=self.q.sequence),stop)
            try:
                with self.assertRaises(RuntimeError):ControlServer(path,injector,lambda:{},stop)
                self.assertFalse(request(path,{'command':'status'})['ready'])
                with self.assertRaises(RuntimeError):request(path,{'command':'enqueue','hex':'01','request_id':'a'})
                server.ready=True
                self.assertEqual(request(path,{'command':'enqueue','hex':'01','request_id':'a'})['sequence'],1)
                self.assertEqual(request(path,{'command':'stop'})['state'],'stop_requested');self.assertTrue(stop.is_set())
            finally:server.close()
            self.assertFalse(path.exists())
if __name__=='__main__':unittest.main()

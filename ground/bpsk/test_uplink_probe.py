import unittest
from uplink_probe import waveform, RATE
from codec import decode

class UplinkProbeTests(unittest.TestCase):
    def test_ping_and_repeat(self):
        a,p=waveform('ping',.05,1921)
        b,q=waveform('ping',.05,1922)
        first,second=decode(p),decode(q)
        self.assertEqual(first['name'],'PING')
        self.assertEqual(first['header']['source'],1)
        self.assertEqual(first['header']['target'],2)
        self.assertEqual(first['header']['transaction_id'],second['header']['transaction_id'])
        self.assertEqual(first['header']['transaction_epoch'],second['header']['transaction_epoch'])
        self.assertNotEqual(p,q)
        self.assertLess(len(a),RATE)
        self.assertEqual(len(a),len(b))
        for kind in ('ping-bad-crc','ping-wrong-target'):
            _,bad=waveform(kind,.05,1923)
            with self.assertRaises(ValueError):decode(bad)
    def test_limits(self):
        for args in [('ping',.1,1),('arbitrary',.01,1),('ping',.01,-1)]:
            with self.assertRaises(ValueError):waveform(*args)

if __name__=='__main__': unittest.main()

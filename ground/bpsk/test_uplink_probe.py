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


class RoundtripTests(unittest.TestCase):
    def test_response_correlation(self):
        from roundtrip import matches_response
        from codec import encode
        _,command=waveform('ping',.05,2000,20)
        def response(transaction=20,boot=123):
            return {'hex':encode('COMMAND_RESPONSE',sequence=1,source=2,target=1,
                transaction_epoch=0x52585031,transaction_id=transaction,
                source_boot_id=boot,uptime_ms=10,
                payload=dict(command_id=1,stage=2,reason=0,parameter_id=0,value=0)).hex()}
        self.assertTrue(matches_response(response(),command,123))
        self.assertFalse(matches_response(response(21),command,123))
        self.assertFalse(matches_response(response(boot=124),command,123))
        self.assertFalse(matches_response({'hex':command.hex()},command,123))

if __name__=='__main__': unittest.main()

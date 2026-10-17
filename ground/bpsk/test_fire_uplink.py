import unittest
from codec import encode
from fire_uplink import valid_command,matches
class FireUplink(unittest.TestCase):
    def test_only_correlated_real_rf_results_complete(self):
        tc=encode('PAYLOAD_FIRE_CHECK',sequence=1,source=1,target=2,source_boot_id=7,uptime_ms=0,
                  transaction_epoch=7,transaction_id=8,payload={})
        self.assertTrue(valid_command(tc))
        self.assertFalse(valid_command(encode('PING',sequence=1,source=1,target=2,source_boot_id=7,
                  uptime_ms=0,transaction_epoch=7,transaction_id=8,payload={})))
        p=dict(payload_version=1,transport=2,result=0,execution_mode=1,bridge_session_id=0,
               reported_boot_id=42,reported_uptime_ms=100,check_id=1)
        def tm(transaction=8):return encode('PAYLOAD_FIRE_RESULT',sequence=1,source=2,target=1,
                    source_boot_id=9,uptime_ms=1,transaction_epoch=7,transaction_id=transaction,payload=p)
        self.assertTrue(matches(tm(),tc));self.assertFalse(matches(tm(9),tc))
        p['transport']=1;self.assertFalse(matches(tm(),tc))
        p['transport']=2;p['check_id']=0;self.assertFalse(matches(tm(),tc))
if __name__=='__main__':unittest.main()

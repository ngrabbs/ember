import unittest
from codec import encode
from fire_uplink import valid_command,matches
class FireUplink(unittest.TestCase):
    def test_only_correlated_real_rf_results_complete(self):
        tc=encode('PAYLOAD_FIRE_CHECK',sequence=1,source=1,target=2,source_boot_id=7,uptime_ms=0,
                  transaction_epoch=7,transaction_id=8,payload={})
        self.assertTrue(valid_command(tc))
        self.assertTrue(valid_command(encode('PING',sequence=1,source=1,target=2,source_boot_id=7,
                  uptime_ms=0,transaction_epoch=7,transaction_id=8,payload={})))
        p=dict(payload_version=1,transport=2,result=0,execution_mode=1,bridge_session_id=0,
               reported_boot_id=42,reported_uptime_ms=100,check_id=1)
        def tm(transaction=8):return encode('PAYLOAD_FIRE_RESULT',sequence=1,source=2,target=1,
                    source_boot_id=9,uptime_ms=1,transaction_epoch=7,transaction_id=transaction,payload=p)
        self.assertTrue(matches(tm(),tc));self.assertFalse(matches(tm(9),tc))
        p['transport']=1;self.assertFalse(matches(tm(),tc))
        p['transport']=2;p['check_id']=0;self.assertFalse(matches(tm(),tc))
        p['check_id']=1;p['payload_version']=2;p['result']=2;p['execution_mode']=2
        self.assertTrue(matches(tm(),tc))
        p['payload_version']=1;self.assertFalse(matches(tm(),tc))
        p['payload_version']=2;p['execution_mode']=1;self.assertFalse(matches(tm(),tc))
    def test_analysis_unavailable_is_correlated_failure_not_fire(self):
        tc=encode('PAYLOAD_FIRE_CHECK',sequence=1,source=1,target=2,source_boot_id=7,
                  uptime_ms=0,transaction_epoch=7,transaction_id=8,payload={})
        p=dict(command_id=1028,stage=3,reason=7,parameter_id=0,value=11)
        def response(transaction=8):return encode('COMMAND_RESPONSE',sequence=2,source=2,target=1,
            source_boot_id=9,uptime_ms=10,transaction_epoch=7,transaction_id=transaction,payload=p)
        self.assertTrue(matches(response(),tc))
        self.assertFalse(matches(response(9),tc))
        p['stage']=2;p['reason']=0;self.assertFalse(matches(response(),tc))
        p['stage']=3;p['reason']=7;p['command_id']=1;self.assertFalse(matches(response(),tc))
    def test_ping_completes_only_on_exact_ping_response(self):
        tc=encode('PING',sequence=1,source=1,target=2,source_boot_id=7,
                  uptime_ms=0,transaction_epoch=7,transaction_id=8,payload={})
        p=dict(command_id=1,stage=2,reason=0,parameter_id=0,value=0)
        def response():return encode('COMMAND_RESPONSE',sequence=2,source=2,target=1,
            source_boot_id=9,uptime_ms=10,transaction_epoch=7,transaction_id=8,payload=p)
        self.assertTrue(matches(response(),tc))
        p['command_id']=1028;self.assertFalse(matches(response(),tc))
        p['command_id']=1;p['value']=11;self.assertFalse(matches(response(),tc))
    def test_status_is_correlated_live_snapshot_not_a_ping(self):
        kw=dict(sequence=1,source_boot_id=7,uptime_ms=0,transaction_epoch=7,transaction_id=8)
        tc=encode('REQUEST_STATUS',source=1,target=2,payload={},**kw)
        self.assertTrue(valid_command(tc))
        p=dict(payload_version=1,mode=3,configuration=1,outputs=0,boot_ready_ms=42,
            can_ready=1,can_eflg=0,eps_attempted=1,eps_valid=0,eps_age_ms=4294967295,
            battery_mv=-2147483648,comms_state=1,payload_state=1,lte_state=0,health_gate_implemented=0)
        def packet(): return encode('IHU_STATUS',source=2,target=1,payload=p,**kw)
        self.assertTrue(matches(packet(),tc))
        p['health_gate_implemented']=1;self.assertFalse(matches(packet(),tc))
        p['health_gate_implemented']=0;p['mode']=5;self.assertFalse(matches(packet(),tc))
        p['mode']=3
        other=encode('REQUEST_STATUS',source=1,target=2,payload={},**dict(kw,transaction_id=9))
        self.assertFalse(matches(packet(),other))
if __name__=='__main__':unittest.main()

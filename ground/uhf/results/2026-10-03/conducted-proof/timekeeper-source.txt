import json,time
from pathlib import Path
import uhd
u=uhd.usrp.MultiUSRP('type=sdrb,mgmt_addr=127.0.0.1')
u.set_tx_gain(0,1);u.set_rx_rate(614400,1);u.set_tx_rate(614400,1)
start=time.monotonic();t0=u.get_time_now().get_real_secs();time.sleep(1);t1=u.get_time_now().get_real_secs();end=time.monotonic()
r=dict(hardware_start=t0,hardware_end=t1,hardware_elapsed=t1-t0,wall_elapsed=end-start,ratio=(t1-t0)/(end-start),rx_rate=u.get_rx_rate(1),tx_rate=u.get_tx_rate(1),clock=u.get_master_clock_rate())
(Path.home()/'ember-timekeeper-check-01.json').write_text(json.dumps(r,indent=2)+'\n');print('TIMEKEEPER_CHECK '+json.dumps(r),flush=True)

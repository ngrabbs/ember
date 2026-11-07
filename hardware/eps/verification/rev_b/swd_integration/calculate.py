"""Current-stage screen supersedes package-only omitted-internal-pull assumptions."""
from common import *
import math
err=.001+25e-6*65
lo=lambda r:r*(1-err)
hi=lambda r:r*(1+err)
par=lambda a,b:a*b/(a+b)
rs=hi(330)+4.5;vmin=3.2328;vmax=3.3244
pu=par(lo(10000),25000);pd=par(lo(47000),25000)
low=.4+(vmax-.4)*rs/(pu+rs)+10e-6*rs
vh=.7*vmax*(1+rs/pd)+10e-6*rs
result={'status':'CONDITIONAL DEVELOPMENT SCREEN; not measured probe or dynamic/PVT qualification','supersedes':'swd_interface_candidate .49849V omitted-internal-pull calculation; historical files unchanged','ST_source':'https://www.st.com/resource/en/datasheet/stm32g0b1ke.pdf','ST_identity':'DS13560 Rev6 tables55 pp93–94 and60 pp98–99; root inspected primary web text; no local PDF inspection claimed','assumptions':{'internal_pull_min_ohm':25000,'internal_pull_max_ohm':55000,'external_R_tolerance_plus_TCR_fraction':err,'probe_VOL_max_V':.4,'probe_VOH_min_V':2.4,'digital_load_guard_A':10e-6,'TMUX_Ron_max_ohm':4.5,'load_F':56e-12,'reset_C_nominal_F':100e-9,'internal_pull_state':'worst enabled bounded pull; do not infer actual option/debug reset configuration'},'external_plus_internal_pullup_min_ohm':pu,'external_plus_internal_clock_pulldown_min_ohm':pd,'target_SWDIO_and_NRST_low_guard_V':low,'MCU_NRST_VIL_max_guard_V':.3*vmin,'clock_probe_high_required_V':vh,'clock_probe_high_requirement_margin_V':2.4-vh,'NRST_discharge_tau_nominal100n_s':par(rs,pu)*100e-9,'NRST_release_tau_internal55k_s':par(hi(10000),55000)*100e-9,'NRST_release_tau_internal_off_s':hi(10000)*100e-9,'proposed_assert_hold_s':.010,'ST_NRST_not_filtered_pulse_min_s':350e-9,'VTref_loaded_min_V':vmin-4.5*(.001+vmax/lo(10000)),'SEL_max_load_A':4*2e-6+vmax/lo(10000),'SEL_high_margin_V':vmin-.4-1.2,'SEL_low_margin_V':.45-.4,'series_RC_10_90_s':math.log(9)*rs*56e-12,'limits':['25..55k internal pulls are separately included;10uA is an additional imposed leakage/load guard.','Pull state/configuration and simultaneous whole-product leakage require actual MCU/probe validation.','Reset RC uses nominal100n only; actual tolerance/effective C and probe open-drain timing remain open.','TPS maximum collapse assertion delay is not specified; low-VDD .6V valid reset row only1uA load.','IPOFF2uA applies atVDD=0, not floating/brownout equilibrium.','Initial100kHz/10ms reset hold do not establish cable or turnaround acceptance.']}
assert low<.3*vmin and vh<2.4 and result['SEL_max_load_A']<.0005
(H/'calculated.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

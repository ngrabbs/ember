#!/usr/bin/env python3
"""Conditional SWD loading/RC screen; no brownout or probe qualification model."""
import json,math,xml.etree.ElementTree as E
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
x=E.parse(ROOT/'hardware/eps/verification/rev_b/uart_integration/eps_rev_b.xml').getroot()
r=next(c for c in x.findall('components/comp') if c.get('ref')=='R800')
assert next(f.text for f in r.findall('fields/field') if f.get('name')=='MFG P/N')=='TNPW0603330RBEEA'
e=.001+25e-6*65
lo=lambda r:r*(1-e)
hi=lambda r:r*(1+e)
vmin=3.2328;vmax=3.3244;ron=4.5;rs=hi(330)+ron;cap=56e-12
# Probe VOL .4 V is an explicit screening requirement, not established probe evidence.
low=.4+(vmax-.4)*rs/(lo(10000)+rs)+10e-6*rs
# Input high needed at the probe to reach .7*VDD on the 47k-down clock.
high_required=.7*vmax*(1+rs/lo(47000))+10e-6*rs
vtref_min=vmin-ron*(.001+vmax/lo(10000))
# TPS published drive row; four II max plus 10k sink, no typical 6M required.
sel_load=4*2e-6+vmax/lo(10000)
sel_high=vmin-.4
# NRST low approach has series+on resistance in parallel with target 10k pullup.
tau_low=rs*hi(10000)/(rs+hi(10000))*100e-9
out={'status':'CONDITIONAL DEVELOPMENT SCREEN; actual debugger and dynamic/PVT gates open','resistor_MPN_verified_from_frozen_R800':'TNPW0603330RBEEA','R_fraction_tolerance_plus_65C_TCR':e,'R330_max_ohm':hi(330),'series_plus_Ron_max_ohm':rs,'assumed_rail_V':[vmin,vmax],'probe_requirements':{'VOL_screen_max_V':.4,'VOH_clock_min_required_V':high_required,'digital_load_guard_A':10e-6,'VTref_load_max_A':.001,'capacitance_F':cap},'SWDIO_target_low_guard_V':low,'MCU_fractional_VIL_guard_V':.3*vmin,'VTref_loaded_min_V':vtref_min,'MCU_to_probe_series_drop_10uA_V':rs*10e-6,'SEL_load_max_A':sel_load,'TPS_drive_row_max_A':.0005,'SEL_high_min_V':sel_high,'SEL_high_margin_V':sel_high-1.2,'SEL_low_margin_V':.45-.4,'series_RC_tau_s':rs*cap,'series_RC_10_90_s':math.log(9)*rs*cap,'10k_pullup_RC_10_90_s':math.log(9)*hi(10000)*cap,'NRST_100n_discharge_tau_s':tau_low,'NRST_100n_release_tau_s':hi(10000)*100e-9,'NRST_hold_recommendation_s':.010,'off_held_zero_conditional':{'each_10k_node_V':2e-6*hi(10000),'47k_node_V':2e-6*hi(47000),'4path_rail_10k_V':8e-6*hi(10000)},'limitations':['330 ohm is not a complete external fault current limiter.','MCU .3/.7 VDD screen is not a replacement for exact NRST threshold/pulse/probe checks.','10ms reset hold is a service condition proposal, not a measured probe guarantee.','TPS assertion 20us and hysteresis29mV are typical only; no max collapse guarantee.','IPOFF2uA is at VDD=0, not a floating rail or continuous brownout guarantee.','RC excludes active-driver slew, cable transmission, MCU input C and turnaround.','Actual probe VOH/VOL/VTref/clock and capacitance must be verified.']}
assert low<.3*vmin and high_required<2.4 and sel_load<.0005 and sel_high>1.2 and vtref_min>3
(H/'calculated.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

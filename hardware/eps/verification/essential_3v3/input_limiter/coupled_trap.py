"""Typical unmodified LTC4231-2 input + LTC4368-1 output barrier experiment.
A behavioral pre-fault buck proxy supplies the raw rail and draws constant
input power. It is disconnected when the failed-high-side inductor path closes.
No real regulator loop, qualified saturated inductance, PVT or SOA proof.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ti-model-archive',type=Path,required=True);a=ap.parse_args();a.output.mkdir(exist_ok=False)
lib=Path.home()/'Library/Application Support/LTspice/lib';model=a.output/'CSD18543Q3A.LIB';model.write_bytes(zipfile.ZipFile(a.ti_model_archive).read('CSD18543Q3A.LIB'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'scope':'TYPICAL_COUPLED_MODELS_WITH_BEHAVIORAL_BUCK_PROXY;NO_INTEGRATION_OR_SOA_ACCEPTANCE','hashes':{'LTC4231-2':sha(lib/'sub/LTC4231-2.sub'),'LTC4368-1':sha(lib/'sub/LTC4368-1.sub'),'TI_CSD18543':sha(model)},'cases':{}}
for name,lb,load in [('L0p1_load2',.1,2),('L0p5_load2',.5,2),('L3p136_load2',3.136,2),('L0p1_noload',.1,0)]:
 d=f'''* Coupled development experiment {name}
.lib "${{LTSPICE_LIBRARY}}/sub/LTC4231-2.sub"
.lib "${{LTSPICE_LIBRARY}}/sub/LTC4368-1.sub"
.lib "${{TI_MODEL}}"
Vinput drive 0 PWL(0 0 1m 0 2m 35 .34 35)
Rfeed drive in .05
Cfeed in 0 650u Rser=.005
Rinshunt in insense .015
Vinmos insense indrain 0
Xin indrain ingate ips csd18543q3a
Ringate igate ingate 10
Cingate igate 0 1n
Cin ips 0 5.6925u Rser=.005
Ristat in istatus 100k
Vuvl uvl 0 2
Vuvh uvh 0 2
Vshdn shdn 0 5
Ctimer timer 0 1n
Xinput insense in shdn uvl uvh 0 gndsw 0 istatus timer ips igate LTC4231-2
* Pre-fault converter proxy: intentionally separate power/load equations.
Bgood good 0 V=min(3.324392156862745,max(V(ips)*.74,0))
Binput ips 0 I=if(time<.3,if(V(istatus)>2,min(max(V(ips),0)/.1,{load*3.324392156862745/.85}/max(V(ips),.1)),0),0)
Vnormal ncmd 0 PWL(0 5 .3 5 .30000001 0 .34 0)
Vfailed fcmd 0 PWL(0 0 .3 0 .30000001 5 .34 5)
Snormal good raw ncmd 0 sw
Sfailed ips wire fcmd 0 sw
.model sw SW(Ron=.001 Roff=1e12 Vt=2)
* Establish the actual pre-fault buck inductor current, removed at fault.
Bprebias raw wire I=if(time<.3,{load},0)
Lfailed wire raw {lb}u Rser=.0159
Craw raw 0 96u Rser=.01
Lguard raw pin 2.2u Rser=.009
Cpin pin 0 100n Rser=.01
Vq1 pin d1 0
Vq2 d2 sense 0
XQ1 d1 gate common csd18543q3a
XQ2 d2 gate common csd18543q3a
Rsense sense out .015
Rgs gate common 10meg
Cgate gate gc 100n
Rgc gc 0 22k
Rov raw ov 58.8k
Rovb ov 0 10k
Ruv raw uv 47.5k
Ruvb uv 0 10k
Cretry retry 0 22n
Rfault raw fault 47k
Cout out 0 640u Rser=.0225
Bload out 0 I=min(max(V(out),0)/.1,{load})
Xoutput raw uv ov retry 0 raw fault out sense gate LTC4368-1
Dclamp 0 pin tv36
.model tv36 D(Bv=44.2 Ibv=1m Rs=1.35 Cjo=500p)
Dgate 0 gate gateclamp
.model gateclamp D(Is=1n N=1.7 Rs=1 Cjo=2p Bv=85 Ibv=.1u)
.options plotwinsize=0
.tran 0 .34 0 1u
.save V(in) V(insense) V(ips) V(igate) V(ingate) V(istatus) V(timer) V(raw) V(pin) V(out) V(common) V(gate) V(sense) I(Rinshunt) I(Lfailed) I(Lguard) I(Vinmos) I(Vq1) I(Vq2)
.end
'''
 p=a.output/(name+'.cir');(a.output/(name+'.portable.cir')).write_text(d);p.write_text(d.replace('${LTSPICE_LIBRARY}',str(lib)).replace('${TI_MODEL}',str(model)));c={'buck_imposed_L_uH':lb,'load_A':load,'status':'not_run','portable_deck_sha256':sha(a.output/(name+'.portable.cir'))}
 try:
  proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(p)],capture_output=True,timeout=50);c['returncode']=proc.returncode;log=p.with_suffix('.log');raw=p.with_suffix('.raw')
  if proc.returncode==0 and log.exists() and raw.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
   t,v=read_raw(raw);assert np.isclose(t[-1],.34);fault=t>=.3;normal=(t>=.29)&(t<.299)
   c.update(status='completed',end_s=float(t[-1]),points=len(t),normal_out_min_V=float(v['v(out)'][normal].min()),fault_out_max_V=float(v['v(out)'][fault].max()),fault_raw_max_V=float(v['v(raw)'][fault].max()),fault_input_node_min_V=float(v['v(ips)'][fault].min()),input_current_peak_A=float(abs(v['i(rinshunt)'][fault]).max()),buck_current_peak_A=float(abs(v['i(lfailed)'][fault]).max()),input_MOS_Vds_abs_max_V=float(abs(v['v(insense)']-v['v(ips)'])[fault].max()),output_Q1_Vds_abs_max_V=float(abs(v['v(pin)']-v['v(common)'])[fault].max()),output_Q2_Vds_abs_max_V=float(abs(v['v(sense)']-v['v(common)'])[fault].max()),raw_sha256=sha(raw))
  else:c['status']='incomplete'
  if log.exists():c['log_sha256']=sha(log)
 except subprocess.TimeoutExpired:c['status']='timeout_terminated'
 r['cases'][name]=c;(a.output/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(name,json.dumps(c),flush=True)

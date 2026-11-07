"""Connected typical-model filter experiments, not hardware acceptance.
Vendor semiconductor models are used unchanged outside Git.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
CASES={
 'bulk640_esr_hot':dict(Lu=2.64,Cu=640,guard_r=.012,temp=85,gate_clamp=True,esr=.0225),
 'bulk640_esr_cold':dict(Lu=2.64,Cu=640,guard_r=.012,temp=-40,gate_clamp=True,esr=.0225),
 'bulk640_source50m':dict(Lu=2.64,Cu=640,guard_r=.012,source_r=.05,gate_clamp=True,esr=.0225),
 'fault_bulk640_repeat':dict(Lu=2.2,Cu=640,guard_r=.009,gate_clamp=True,fault=True,step_us=1),
 'bulk2p2_640':dict(Lu=2.2,Cu=640,guard_r=.009,gate_clamp=True),
 'bulk2p64_640_hot':dict(Lu=2.64,Cu=640,guard_r=.012,temp=85,gate_clamp=True),
 'fault_bulk2p2_640_clamped':dict(Lu=2.2,Cu=640,guard_r=.009,gate_clamp=True,fault=True),
 'fault_bulk2p2_640_clamped_noload':dict(Lu=2.2,Cu=640,guard_r=.009,gate_clamp=True,fault=True,no_load=True),
 'fault_guard4p7_384_clamped':dict(Lu=4.7,Cu=384,gate_clamp=True,fault=True),
 'fault_base10_192_clamped':dict(Lu=10,Cu=192,gate_clamp=True,fault=True),
 'base10_192':dict(Lu=10,Cu=192),
 'guard4p7_192':dict(Lu=4.7,Cu=192),
 'guard2p2_192':dict(Lu=2.2,Cu=192),
 'guard4p7_384':dict(Lu=4.7,Cu=384),
 'guard2p2_384':dict(Lu=2.2,Cu=384),
 'base10_768':dict(Lu=10,Cu=768),
 'damped10_192':dict(Lu=10,Cu=192,damper=True),
 'guard4p7_384_source50m':dict(Lu=4.7,Cu=384,source_r=.05),
 'fault_base10_192':dict(Lu=10,Cu=192,fault=True),
 'fault_guard4p7_384':dict(Lu=4.7,Cu=384,fault=True),
 'fault_guard2p2_384':dict(Lu=2.2,Cu=384,fault=True),
 'fault_damped10_192':dict(Lu=10,Cu=192,damper=True,fault=True),
}
def deck(c):
 fault=c.get('fault',False);normal=3.324392156862745 if fault else 3.232799137558028
 source=f'''Vsource drive 0 PWL(0 0 1m 0 2m {normal} .4 {normal})
Rsource drive vin {c.get('source_r',.001)}'''
 if fault:
  # Separate finite high-voltage reservoir; the ideal source selector is explicit.
  # This is not an LMR51635 control-loop model or guaranteed source/magnetic bound.
  source=f'''Vgood good 0 PWL(0 0 1m 0 2m {normal} .4 {normal})
Vselect select 0 PWL(0 0 .3 0 .30000001 5 .4 5)
Vnotselect notselect 0 PWL(0 5 .3 5 .30000001 0 .4 0)
Sgood good vin notselect 0 sw
Rgood vin 0 10meg
Sfault high wire select 0 sw
.model sw SW(Ron=.001 Roff=1e12 Vt=2)
Bfeed 0 high I=limit((35-V(high))/.1,0,1)
Cenergy high 0 650u Rser=.005 IC=35
Lfailed wire vin .5u Rser=.0159
Rwire wire 0 10meg'''
 return f'''* {c}; TYPICAL MODELS / IMPOSED PASSIVES, NO CIRCUIT ACCEPTANCE
.lib "${{LTSPICE_LIBRARY}}/sub/LTC4368-1.sub"
.lib "${{TI_MODEL}}"
{source}
Cpre vin 0 96u Rser=.01
Lguard vin pin {c['Lu']}u Rser={c.get('guard_r',.02)}
Cpin pin 0 100n Rser=.01
Vd1 pin drain1 0
Vd2 drain2 sense 0
XQ1 drain1 gate common csd18543q3a
XQ2 drain2 gate common csd18543q3a
Rsense sense out .015
Rgs gate common 10meg
Cgate gate gc 100n
Rgc gc 0 22k
Rov vin ov 58.8k
Rovb ov 0 10k
Ruv vin uv 47.5k
Ruvb uv 0 10k
Cretry retry 0 22n
Rfault vin fault 47k
Cout out 0 {c['Cu']}u Rser={c.get('esr',.01)}
''' + ('Dgate 0 gate gate_negative_clamp\n.model gate_negative_clamp D(Is=1n N=1.7 Rs=1 Cjo=2p Bv=85 Ibv=.1u)\n' if c.get('gate_clamp') else '') + ('Rdamp out damp .22\nCdamp damp 0 470u Rser=.01\n' if c.get('damper') else '') + f'''Bload out 0 I=min(max(V(out),0)/.1,if(time<.25,.2,if(time>.29,{0 if c.get('no_load') else 2},2)))
Xcontroller vin uv ov retry 0 vin fault out sense gate LTC4368-1
''' + ('''Dclamp 0 pin tv36
.model tv36 D(Bv=44.2 Ibv=1m Rs=1.35 Cjo=500p)
''' if fault else '')+f'''.temp {c.get('temp',27)}
.options plotwinsize=0
.tran 0 .4 0 {c.get('step_us',2)}u
.save V(vin) V(pin) V(out) V(common) V(gate) V(retry) V(uv) V(ov) V(fault) V(gc) I(Rsense) I(Lguard) I(Vd1) I(Vd2) {'I(Dgate)' if c.get('gate_clamp') else ''} {'I(Lfailed)' if fault else ''}
.end
'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ti-model-archive',type=Path,required=True);ap.add_argument('--cases',nargs='+',choices=list(CASES),default=list(CASES));a=ap.parse_args()
 a.output.mkdir(exist_ok=False,parents=True);lib=Path.home()/'Library/Application Support/LTspice/lib'
 model=a.output/'CSD18543Q3A.LIB';model.write_bytes(zipfile.ZipFile(a.ti_model_archive).read('CSD18543Q3A.LIB'))
 hashes={'TI_archive_sha256':sha(a.ti_model_archive),'TI_model_sha256':sha(model),'controller_sha256':sha(lib/'sub/LTC4368-1.sub')}
 assert hashes['TI_model_sha256']=='fa4ef72177bc7691b956ef047985e6fc0a490ae1e12d41295c787e6e51dba170'
 assert hashes['controller_sha256']=='d02c1dc157882e68619668ee8b843971984874514a0bb07bf5e0f9f4ebe3410f'
 results={'scope':'TYPICAL_CONNECTED_EXPERIMENTS_NO_PVT_OR_FAULT_ACCEPTANCE','model_hashes':hashes,'cases':{}}
 for name in a.cases:
  c=CASES[name];portable=deck(c);p=a.output/(name+'.cir');p.write_text(portable.replace('${LTSPICE_LIBRARY}',str(lib)).replace('${TI_MODEL}',str(model)));(a.output/(name+'.portable.cir')).write_text(portable)
  r={'parameters':c,'status':'not_run','portable_deck_sha256':sha(a.output/(name+'.portable.cir'))}
  try:
   proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(p)],capture_output=True,timeout=45);r['returncode']=proc.returncode;log=p.with_suffix('.log');raw=p.with_suffix('.raw')
   if proc.returncode==0 and log.exists() and raw.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
    t,v=read_raw(raw);assert np.isclose(t[-1],.4);step=(t>=.25)&(t<.3);late=(t>=.29)&(t<.3);fault=t>=.3
    r.update(status='completed',end_s=float(t[-1]),points=len(t),normal_step_min_V=float(v['v(out)'][step].min()),normal_step_max_V=float(v['v(out)'][step].max()),normal_late_min_V=float(v['v(out)'][late].min()),normal_vgs_late_min_V=float((v['v(gate)']-v['v(common)'])[late].min()),shunt_peak_abs_A=float(abs(v['i(rsense)']).max()),raw_sha256=sha(raw))
    if c.get('fault'):
     r.update(fault_out_max_V=float(v['v(out)'][fault].max()),fault_pin_max_V=float(v['v(pin)'][fault].max()),fault_raw_max_V=float(v['v(vin)'][fault].max()),fault_guard_peak_A=float(abs(v['i(lguard)'][fault]).max()),Q1_Vds_abs_max_V=float(abs(v['v(pin)']-v['v(common)'])[fault].max()),Q2_Vds_abs_max_V=float(abs(v['v(out)']+v['i(rsense)']*.015-v['v(common)'])[fault].max()))
   else:r['status']='incomplete'
   if log.exists():r['log_sha256']=sha(log)
  except subprocess.TimeoutExpired:r['status']='timeout_terminated'
  results['cases'][name]=r;(a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,json.dumps(r),flush=True)
if __name__=='__main__':main()

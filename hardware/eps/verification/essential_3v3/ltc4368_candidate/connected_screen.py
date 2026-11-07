"""Unmodified TI CSD18543Q3A + installed LTC4368 nominal connected experiment."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ti-model-archive',type=Path,required=True);ap.add_argument('--source-r',type=float,default=.05);ap.add_argument('--load-step',type=float,default=.08);ap.add_argument('--stop',type=float,default=.12);a=ap.parse_args();assert 0<a.load_step<a.stop;a.output.mkdir(exist_ok=False)
lib=Path.home()/'Library/Application Support/LTspice/lib';model=a.output/'CSD18543Q3A.LIB';b=zipfile.ZipFile(a.ti_model_archive).read('CSD18543Q3A.LIB');model.write_bytes(b)
deck='''* NOMINAL CONNECTED DEVELOPMENT EXPERIMENT, NOT A SELECTED CIRCUIT
.lib "${LTSPICE_LIBRARY}/sub/LTC4368-1.sub"
.lib "${TI_MODEL}"
Vsource drive 0 PWL(0 0 1m 0 2m 3.2328 .12 3.2328)
Rsource drive vin .05
Cpre vin 0 96u Rser=.01
Lguard vin pin 10u Rser=.02
Cpin pin 0 100n Rser=.01
XQ1 pin gate common csd18543q3a
XQ2 sense gate common csd18543q3a
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
Cout out 0 192u Rser=.01
Bload out 0 I=min(max(V(out),0)/.1,if(time<80m,.2,2))
Xcontroller vin uv ov retry 0 vin fault out sense gate LTC4368-1
.options plotwinsize=0
.tran 0 .12 0 2u
.save V(vin) V(pin) V(out) V(common) V(gate) V(retry) V(uv) V(ov) I(Rsense) I(Vsource)
.end
'''
deck=deck.replace('.12 3.2328',f'{a.stop} 3.2328').replace('time<80m',f'time<{a.load_step}').replace('.tran 0 .12',f'.tran 0 {a.stop}')
deck=deck.replace('Rsource drive vin .05',f'Rsource drive vin {a.source_r}')
(a.output/'nominal.portable.cir').write_text(deck)
p=a.output/'nominal.cir';p.write_text(deck.replace('${LTSPICE_LIBRARY}',str(lib)).replace('${TI_MODEL}',str(model)))
r={'source_resistance_ohm':a.source_r,'load_step_s':a.load_step,'stop_s':a.stop,'status':'not_run','scope':'NOMINAL_MODEL_ONLY_NO_FAULT_OR_QUALIFICATION','TI_archive_sha256':hashlib.sha256(a.ti_model_archive.read_bytes()).hexdigest(),'TI_unmodified_model_sha256':hashlib.sha256(b).hexdigest(),'controller_model_sha256':hashlib.sha256((lib/'sub/LTC4368-1.sub').read_bytes()).hexdigest()}
try:
 proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(p)],capture_output=True,timeout=45);r['returncode']=proc.returncode;log=p.with_suffix('.log');raw=p.with_suffix('.raw')
 r['status']='incomplete'
 if proc.returncode==0 and log.exists() and raw.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
  t,v=read_raw(raw);assert np.isclose(t[-1],a.stop);late=t>=a.stop-.01;step=(t>=a.load_step)&(t<=a.stop)
  r.update(status='completed',end_s=float(t[-1]),points=len(t),out_late_min_V=float(v['v(out)'][late].min()),vgs_late_min_V=float((v['v(gate)']-v['v(common)'])[late].min()),load_step_window_s=[a.load_step,a.stop],load_step_window_out_min_V=float(v['v(out)'][step].min()),load_step_window_out_max_V=float(v['v(out)'][step].max()),observed_below3V_after_step=bool(np.any(v['v(out)'][step]<3)),shunt_peak_abs_A=float(abs(v['i(rsense)']).max()),raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
 if log.exists():r['log_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
except subprocess.TimeoutExpired:r['status']='timeout_terminated'
(a.output/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

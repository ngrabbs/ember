"""Unmodified installed LTC4231-2 model / TI single pass FET experiment.
A vendor-model alternative to the encrypted PSpice-only TPS26630 package.
This is an input-switch function test, not the complete EPS or qualified SOA.
"""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys,zipfile
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'hardware/eps/verification/protection'))
from run_protection import read_raw
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--ti-model-archive',type=Path,required=True);a=ap.parse_args();a.output.mkdir(exist_ok=False)
lib=Path.home()/'Library/Application Support/LTspice/lib';model=a.output/'CSD18543Q3A.LIB';model.write_bytes(zipfile.ZipFile(a.ti_model_archive).read('CSD18543Q3A.LIB'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# SpiceOrder comes from the plain installed ASY interface, not the opaque model body.
symbol=(lib/'sym/PowerProducts/LTC4231-2.asy').read_text(errors='replace');pairs=re.findall(r'PINATTR PinName (\S+)\s+PINATTR SpiceOrder (\d+)',symbol)
assert {int(n):name for name,n in pairs}=={1:'SENSE',2:'IN',3:'_SHDN',4:'UVL',5:'UVH',6:'OV',7:'GNDSW',8:'GND',9:'STATUS',10:'TIMER',11:'SOURCE',12:'GATE'}
results={'scope':'UNMODIFIED_TYPICAL_VENDOR_MODELS;NO_CIRCUIT_OR_SOA_ACCEPTANCE','model_hashes':{'LTC4231_2':sha(lib/'sub/LTC4231-2.sub'),'LTC4231_ASY':sha(lib/'sym/PowerProducts/LTC4231-2.asy'),'TI_CSD18543':sha(model)},'cases':{}}
for name,vin,stop,short in [('low',4.5,.1,False),('battery',8.5,.1,False),('high_short',35,.1,True),('low_retry',4.5,.7,True)]:
 d=f'''* Input-switch function experiment {name}; UV/OV forced to test state
.lib "${{LTSPICE_LIBRARY}}/sub/LTC4231-2.sub"
.lib "${{TI_MODEL}}"
Vsource command 0 PWL(0 0 1m 0 2m {vin} {stop} {vin})
Rsource command in .05
Csource in 0 650u Rser=.005
Rsense in sense .015
Vdrain sense drain 0
Xpass drain mg source csd18543q3a
Rgate gate mg 10
Cgate gate 0 1n
Cinput source 0 5.6925u Rser=.005
Rstatus in status 100k
Vuvl uvl 0 2
Vuvh uvh 0 2
Vshdn shdn 0 5
Ctimer timer 0 1n
Xcontroller sense in shdn uvl uvh 0 gndsw 0 status timer source gate LTC4231-2
Bload source 0 I=if(V(status)>2,min(max(V(source),0)/.1,7.8235/max(V(source),.1)),0)
''' + ('''Vshort shortcmd 0 PWL(0 0 80m 0 80.00001m 5 80.2m 5 80.20001m 0)
Sshort source short shortcmd 0 sw
Rshort short 0 .01
.model sw SW(Ron=.001 Roff=1e12 Vt=2)
''' if short else '')+f'''.options plotwinsize=0
.tran 0 {stop} 0 2u
.save V(in) V(sense) V(source) V(gate) V(mg) V(status) V(timer) I(Rsense) I(Vdrain)
.end
'''
 p=a.output/(name+'.cir');(a.output/(name+'.portable.cir')).write_text(d);p.write_text(d.replace('${LTSPICE_LIBRARY}',str(lib)).replace('${TI_MODEL}',str(model)));rec={'vin_V':vin,'stop_s':stop,'short':short,'status':'not_run','portable_deck_sha256':sha(a.output/(name+'.portable.cir'))}
 try:
  proc=subprocess.run(['/Applications/LTspice.app/Contents/MacOS/LTspice','-b',str(p)],capture_output=True,timeout=45);rec['returncode']=proc.returncode;raw=p.with_suffix('.raw');log=p.with_suffix('.log')
  if proc.returncode==0 and raw.exists() and log.exists() and 'Total elapsed time:' in log.read_text(errors='replace'):
   t,v=read_raw(raw);assert np.isclose(t[-1],stop);normal=(t>=.07)&(t<.079);late=t>=stop-.01
   rec.update(status='completed',points=len(t),end_s=float(t[-1]),normal_out_min_V=float(v['v(source)'][normal].min()),normal_gate_source_min_V=float((v['v(gate)']-v['v(source)'])[normal].min()),normal_input_max_A=float(v['i(rsense)'][normal].max()),input_peak_A=float(v['i(rsense)'].max()),late_out_min_V=float(v['v(source)'][late].min()),raw_sha256=sha(raw))
   if short:
    m=(t>=.08)&(t<=.081);pw=(v['v(sense)']-v['v(source)'])*v['i(vdrain)'];rec.update(short_MOS_peak_port_W=float(pw[m].max()),short_MOS_positive_port_energy_J=float(np.trapezoid(np.maximum(pw[m],0),t[m])),short_source_min_V=float(v['v(source)'][m].min()))
  else:rec['status']='incomplete'
  if log.exists():rec['log_sha256']=sha(log)
 except subprocess.TimeoutExpired:rec['status']='timeout_terminated'
 results['cases'][name]=rec;(a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,json.dumps(rec),flush=True)

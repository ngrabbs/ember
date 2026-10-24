#!/usr/bin/env python3
"""Exact passive selection and bounded DC stress, not circuit/assembly release."""
from pathlib import Path
from itertools import product
import json,csv,hashlib,math
H=Path(__file__).resolve().parent;ROOT=H.parents[4]
E=.001+25e-6*65
# Canonical ref allocation follows the managed-feed contract; no native writes.
values={1400:4020,1401:41200,1402:10000,1403:68100,1404:10000,1405:36500,1406:10000,1407:18000,1408:1000,1409:20000,1410:10000,1411:10000,1412:10000,1420:10000,1421:1000,1422:10000,1423:1000,1424:1000000,1425:10000,1426:169000,1427:10000,1428:226000,1429:10000}
codes={1000:'1K00',4020:'4K02',10000:'10K0',18000:'18K0',20000:'20K0',36500:'36K5',41200:'41K2',68100:'68K1',169000:'169K',226000:'226K',1000000:'1M00'}
rules={'0603':dict(max_R=332000,p70=.110,vmax=100,foot='R_0603_1608Metric'),'0805':dict(max_R=1000000,p70=.140,vmax=150,foot='R_0805_2012Metric'),'1210':dict(max_R=2130000,p70=.330,vmax=200,foot='R_1210_3225Metric')}
parts=[];stress=[]
for n,r in values.items():
 size='1210' if n==1412 else '0805' if n==1424 else '0603';rule=rules[size]
 assert 3.5<=r<=rule['max_R']
 mpn='TNPW'+size+codes[r]+'BEEA'
 # Independent decoder guards value/package/code mistakes in the sourcing table.
 code=mpn[8:12];assert math.isclose(float(code.replace('K','.').replace('M','.'))*({'K':1e3,'M':1e6}[next(c for c in code if c in 'KM')]),r,rel_tol=1e-12)
 if n in [1401,1403,1405,1412,1426,1428]:v=35.;premise='Full imposed 35 V across source-connected resistor, conservative DC bound'
 elif n in [1402,1404,1406,1427,1429]:
  top={1402:41200,1404:68100,1406:36500,1427:169000,1429:226000}[n]
  v=max(35*rb/(rt+rb) for rt,rb in product([top*(1-E),top*(1+E)],[r*(1-E),r*(1+E)]));premise='35 V ideal-source divider, independent initial/TCR corners; no clamp credit'
 elif n in [1400,1407]:v=5.5;premise='Imposed 5.5 V low-voltage pin bound for resistor stress, not pin-operation acceptance'
 else:v=3.6;premise='Essential/control supply bounded to 3.6 V; no alternate-source injection'
 p=v*v/(r*(1-E));allow=rule['p70']*(125-85)/(125-70)
 assert p<.6*allow and v<rule['vmax']
 parts.append(dict(reference='R'+str(n),value=str(r)+' ohm',MPN=mpn,Manufacturer='Vishay',PackageSize=size,Tolerance='0.1%',TCR='25 ppm/K',Power=f"{rule['p70']:.3f} W P70 General; thermally derated",Voltage=str(rule['vmax'])+' V',Dielectric='',Footprint='Resistor_SMD:'+rule['foot'],sourcing_basis='Manufacturer family/order-code table; order/lot confirmation pending'))
 stress.append(dict(reference='R'+str(n),applied_voltage_screen_V=v,power_screen_W=p,allowed_85C_general_curve_W=allow,utilization=p/allow,configured_power_fraction=.6,configured_allowed_W=.6*allow,premise=premise))
for n in [1400,1401,1402,1403,1404,1405,1406,*range(1410,1417)]:
 if n in [1400,1402]:mpn='GRM32ER72A225KA35L';value='2.2 uF';size='1210';tol='10%';volts='100 V';diel='X7R';mfr='Murata'
 elif n==1404:mpn='GRM31C5C1H104JA01L';value='100 nF';size='1206';tol='5%';volts='50 V';diel='C0G';mfr='Murata'
 elif n in [1405,1406]:mpn='CGA3E2C0G1H102J080AA';value='1 nF';size='0603';tol='5%';volts='50 V';diel='C0G';mfr='TDK'
 else:mpn='GRM188R72A104KA35D';value='100 nF';size='0603';tol='10%';volts='100 V';diel='X7R';mfr='Murata'
 dim={'0603':'1608','1206':'3216','1210':'3225'}[size]
 parts.append(dict(reference='C'+str(n),value=value,MPN=mpn,Manufacturer=mfr,PackageSize=size,Tolerance=tol,TCR='',Power='',Voltage=volts,Dielectric=diel,Footprint=f'Capacitor_SMD:C_{size}_{dim}Metric',sourcing_basis='TDK exact product page' if mfr=='TDK' else 'Previously screened exact part retained; effective capacitance/assembly checks conditional'))
assert len(parts)==37 and len(stress)==23 and len({p['reference'] for p in parts})==37
for p in parts:
 p['FootprintStatus']='Existing stock candidate; assembly acceptance open'
 if p['reference'] in ['C1405','C1406']:
  p['Footprint']='Ember_Charger_BMS_Review:C_0603_TDK_CGA3_PA0.70_PB0.70_PC0.70_REVIEW'
  p['FootprintStatus']='Constructed and query/render verified in tdk_filter_package; custom review and assembly qualification remain'
with (H/'parts.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=parts[0],lineterminator='\n');w.writeheader();w.writerows(parts)
# Compare queried stock pads to manufacturer's representative reflow patterns.
land=[]
recommended=[(.7,.9,1.),(1.,.9,1.45),(1.75,1.15,2.65)]
for i in range(4):
 q=json.loads((H/f'stock_{i}.json').read_text());d=json.loads(q['result']['content'][0]['text']);ps=d['pads'];assert len(ps)==2 and sorted(p['number'] for p in ps)==['1','2']
 a,b=sorted(ps,key=lambda p:p['x']);gap=b['x']-b['width']/2-a['x']-a['width']/2
 assert all(p['type']=='smd' and p['drill']==[] for p in ps)
 row=dict(footprint=q['id'],pad_length_mm=a['width'],pad_width_mm=a['height'],inner_gap_mm=gap,raw_pad_count=2)
 if i<3:row['Vishay_IPC_representative_G_Y_X_mm']=recommended[i];row['exact_match_to_representative_pattern']=False
 else:row['TDK_product_reflow_ranges_mm']={'PA':[.6,.8],'PB':[.6,.8],'PC':[.6,.8]};row['within_all_recommended_ranges']=False
 land.append(row)
base=json.loads((H.parent/'helper_package/frozen_baseline.json').read_text())
for name,expected in base['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
result=dict(status='37_PASSIVES_SELECTED_DC_SCREEN_ONLY',resistors=23,capacitors=14,all_resistor_DC_screens_within_conditional_derated_power=True,temperature_screen_C=[-40,85],resistor_error_fraction=E,stress=stress,land_comparison=land,prior_native_preserved=len(base['files']),native_mutation=False,assembly_acceptance=False,qualification=False,limits=['35 V imposed source ceiling; valid 3.6 V control supply assumed','Thermal board/film behavior and long-term resistance drift not proven','No resistor open/short single-fault or transient-pulse acceptance','X7R nominal values do not prove effective capacitance','TDK project filter footprint is constructed with disposable mask verification; review/assembly and real-board settings remain open','Ordering availability, lot and assembly process are not confirmed'])
(H/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['stress','land_comparison']},indent=2))
print('highest power utilization',max(stress,key=lambda x:x['utilization']))

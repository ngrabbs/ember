"""TDK reference data with explicit screening derates; not guaranteed limits."""
from pathlib import Path
import csv,json,hashlib
HERE=Path(__file__).resolve().parent;SRC=HERE/'capacitor_sources'
def points(name):
 rows=list(csv.reader((SRC/name).read_text(encoding='utf-8-sig').splitlines()))
 # First numeric two-column dataset only; temperature file also includes25V data.
 data=[]
 for r in rows:
  try:a,b=float(r[0]),float(r[1])
  except (ValueError,IndexError):
   if data:break
   continue
  data.append((a,b))
 return data
def interpolate(data,x):
 for (a,b),(c,d) in zip(data,data[1:]):
  if a<=x<=c:return b+(d-b)*(x-a)/(c-a)
 raise ValueError(x)
bias=points('CGA5L1X7R1H106K160AC_bias.csv');esr=points('CGA5L1X7R1H106K160AC_esr.csv')
tol=.1;temp=.15;aging=.1
vpoints={'primary':3.3244,'isolated_5V':5.2,'LDO_output':3.401}
banks={}
for name,n in [('primary',8),('isolated_5V',3),('LDO_output',1)]:
 v=vpoints[name];ref=interpolate(bias,v)
 banks[name]={'quantity':n,'nominal_uF':10*n,'voltage_screen_V':v,'reference_bias_cap_each_uF':ref*1e6,'conditional_low_uF':ref*n*(1-tol)*(1-temp)*(1-aging)*1e6,'zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF':10*n*(1+tol)*(1+temp)*max(y for x,y in bias)/1e-5,'reference_ESR_each_at250kHz_ohm_linear_interpolation':interpolate(esr,250000),'reference_ESR_parallel_at250kHz_ohm':interpolate(esr,250000)/n}
r=.001+25e-6*65
limits={}
for k in [210,120,115,110,100]:
 limits[str(k)+'kohm']={'min_A':25230/(k*(1+r))**1.016/1000,'max_A':22980/(k*(1-r))**.94/1000}
capmax=banks['primary']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']
charges={k:capmax*1e-6*3.3244/(v['min_A']-.05)*1000 for k,v in limits.items()}
result={'exact_part':'CGA5L1X7R1H106K160AC','source_url':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA5L1X7R1H106K160AC','source_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in SRC.glob('*.csv')},'method':'linear interpolation of manufacturer reference curves; independent tolerance/temp/aging factors are conditional assumptions','tolerance_fraction':tol,'X7R_temperature_guard_fraction':temp,'aging_guard_fraction_assumed_not_qualified':aging,'banks':banks,'RILIM_bounds':limits,'ideal_charge_time_ms_at50mA_simultaneous_load':charges,'remaining':['Reference curves not manufacturer guarantees','Aging10% is an assumed allocation; mission life and actual aging specification open','Combined bias/temperature/aging behavior not proven multiplicative','ESR reference25C only; cold/ripple/inductance and current sharing need review','No selected RILIM/circuit acceptance; startup/source/fault/reset gates remain']}
assert banks['primary']['conditional_low_uF']>=47
assert banks['LDO_output']['conditional_low_uF']>=4.7
(HERE/'capacitors.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'banks':banks,'limits115k':limits['115kohm'],'charge_time_ms':charges},indent=2))
if __name__=='__main__':pass

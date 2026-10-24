"""Average-load sensitivity around the54uF conditional bank floor."""
import json
from pathlib import Path
import screen
HERE=Path(__file__).resolve().parent
rows=[]
for average in [.050,.075,.100]:
 period=screen.WIDTH*(screen.HIGH-screen.LOW)/(average-screen.LOW)
 for limit in [.110,.20281099648418788]:
  v=screen.VS-screen.R*screen.LOW;mins=[]
  for k in range(1000):
   v,a,b=screen.advance(v,screen.HIGH,screen.WIDTH,54e-6,limit)
   v,a2,b2=screen.advance(v,screen.LOW,period-screen.WIDTH,54e-6,limit)
   if k>=900:mins.extend([a,a2])
  rows.append({'average_A':average,'minimum_limit_A':limit,'period_us':period*1e6,'input_min_V':min(mins),'margin_to3V_V':min(mins)-3})
cp=json.loads((HERE/'capacitors.json').read_text())
cap=cp['banks']['primary']['zero_bias_upper_tolerance_temperature_and_reference_bias_peak_uF']
charge=[{'average_A':a,'ideal_charge_ms_at115k_minimum':cap*1e-6*3.3244/(.20281099648418788-a)*1000} for a in [.05,.075,.1]]
r={'status':'same imposed ideal-clamp/stiff-source assumptions as screen.py; average loads are scenarios, not guaranteed UCC maxima','effective_C_uF':54,'periodic_cases':rows,'charge_balance':charge}
(HERE/'average_load.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))

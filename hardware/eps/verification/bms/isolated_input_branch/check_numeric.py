"""Independent midpoint integration check of the imposed RC sensitivity."""
import json
from pathlib import Path
import screen
HERE=Path(__file__).resolve().parent
cases=[]
for cu,limit in [(10,.110),(47,.110),(100,.200)]:
 c=cu*1e-6;v=screen.VS-screen.R*screen.LOW;mn=10;mx=-10
 def current(vc,load):return min(limit,(screen.VS-vc+screen.ESR*load)/(screen.R+screen.ESR))
 def pin(vc,load):return vc+screen.ESR*(current(vc,load)-load)
 for cycle in range(100):
  if cycle==99:mn=10;mx=-10
  for load,span in [(screen.HIGH,screen.WIDTH),(screen.LOW,screen.PERIOD-screen.WIDTH)]:
   n=int(span/20e-9)+1;dt=span/n
   if cycle==99:mn=min(mn,pin(v,load));mx=max(mx,pin(v,load))
   for k in range(n):
    slope=(current(v,load)-load)/c
    half=v+dt*slope/2
    v+=dt*(current(half,load)-load)/c
    if cycle==99:mn=min(mn,pin(v,load));mx=max(mx,pin(v,load))
 old=json.loads((HERE/'calculated.json').read_text())
 ref=next(x for x in old['periodic_cases'] if x['limit_A']==limit and x['effective_C_uF']==cu)
 err=max(abs(mn-ref['periodic_input_min_V']),abs(mx-ref['periodic_input_max_V']))
 assert err<1e-6,err
 cases.append({'C_uF':cu,'limit_A':limit,'independent_min_V':mn,'independent_max_V':mx,'max_difference_V':err})
(HERE/'numeric_check.json').write_text(json.dumps({'method':'Independent midpoint ODE integration, timestep <=20ns,100 periods; compares last-cycle extrema to analytical1000-period solution','cases':cases},indent=2)+'\n')
print(json.dumps(cases,indent=2))

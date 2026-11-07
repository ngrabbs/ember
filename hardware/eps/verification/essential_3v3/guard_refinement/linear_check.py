"""Independent linear load-step sanity model, not MOSFET/PVT acceptance.
Rpath=.059 ohm is rounded from the nominal connected late voltage drop.
The stiff source approximation omits the upstream96uF and source1mohm pole.
"""
from pathlib import Path
import argparse,json
import numpy as np
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=H/'linear_results.json');a=ap.parse_args()
rows=[]
for Lu,Cu,damped in [(10,192,False),(4.7,192,False),(2.2,192,False),(4.7,384,False),(2.2,384,False),(10,768,False),(10,192,True)]:
 L=Lu*1e-6;C=Cu*1e-6;R=.059;rc=.01;Vs=3.232799137558028;load=2.;initial=.2
 if damped:
  rd=.23;cd=470e-6
  def vout(x):return (x[0]-load+x[1]/rc+x[2]/rd)/(1/rc+1/rd)
  def f(x):
   vo=vout(x);return np.array([(Vs-R*x[0]-vo)/L,(vo-x[1])/(rc*C),(vo-x[2])/(rd*cd)])
  x0=np.array([initial,Vs-R*initial,Vs-R*initial]);xf=np.array([load,Vs-R*load,Vs-R*load])
 else:
  def vout(x):return x[1]+rc*(x[0]-load)
  def f(x):return np.array([(Vs-R*x[0]-vout(x))/L,(x[0]-load)/C])
  x0=np.array([initial,Vs-R*initial]);xf=np.array([load,Vs-R*load])
 z=np.zeros(len(x0));b=f(z);A=np.column_stack([f(e)-b for e in np.eye(len(z))]);ev,P=np.linalg.eig(A);q=np.linalg.solve(P,x0-xf)
 times=np.linspace(0,.004,32001);exact=(xf[:,None]+P@(q[:,None]*np.exp(ev[:,None]*times))).real
 vo=np.array([vout(x) for x in exact.T]);pk=float(vo.min());min_t=float(times[np.argmin(vo)])
 x=x0.copy();dt=.125e-6;mx=0.
 for i in range(len(times)):
  mx=max(mx,float(np.max(abs(x-exact[:,i]))))
  k1=f(x);k2=f(x+dt*k1/2);k3=f(x+dt*k2/2);k4=f(x+dt*k3);x+=dt*(k1+2*k2+2*k3+k4)/6
 assert mx<1e-7,mx
 rows.append(dict(guard_uH=Lu,protected_uF=Cu,damper=damped,linear_min_V=pk,minimum_time_s=min_t,rk4_matrix_exp_max_state_difference=mx))
a.output.write_text(json.dumps({'scope':'LINEAR_SANITY_MODEL_WITH_FITTED_NOMINAL_PATH_R;NOT_GUARANTEED_DESIGN','path_R_ohm':.059,'rows':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))

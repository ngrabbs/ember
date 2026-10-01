import sys,pathlib
output_dir=pathlib.Path(sys.argv[1]);output_dir.mkdir(parents=True,exist_ok=True)
import numpy as np,json
f=np.linspace(100e6,1400e6,13001);w=2*np.pi*f

def calc(l=10e-9,c=9.1e-12,io=3.9e-12,cc=1.6e-12,q=None):
 out=[]
 for freq in f:
  s=2j*np.pi*freq
  Z= s*l+(2*np.pi*435e6*l/q if q else 0)
  y=s*c+1/Z
  se=lambda z:np.array([[1,z],[0,1]],complex)
  sh=lambda y:np.array([[1,0],[y,1]],complex)
  a=se(1/(s*io))@sh(y)@se(1/(s*cc))@sh(y)@se(1/(s*io))
  den=a[0,0]+a[0,1]/50+a[1,0]*50+a[1,1]
  out.append([20*np.log10(abs(2/den)),20*np.log10(max(1e-15,abs((a[0,0]+a[0,1]/50-a[1,0]*50-a[1,1])/den)))])
 return np.array(out)
r={}
for name,kw in [('ideal',{}),('Q40',{'q':40}),('Q60',{'q':60}),('shunt_plus_0p3',{'c':9.4e-12}),('L_plus_5pct',{'l':10.5e-9})]:
 a=calc(**kw);pk=np.argmax(a[:,0]);band=f[a[:,0]>=a[pk,0]-3]/1e6
 r[name]={'peak_MHz':float(f[pk]/1e6),'peak_S21_dB':float(a[pk,0]),'relative_3dB_band_MHz':[float(band[0]),float(band[-1])],'points':{str(ff):{'S21_dB':float(a[round((ff-100)*10),0]),'S11_dB':float(a[round((ff-100)*10),1])} for ff in [145,435,437,870,1305]}}
np.savetxt(output_dir/'comms-filter-ideal.csv',np.c_[f/1e6,calc()],delimiter=',',header='MHz,S21_dB,S11_dB',comments='')
json.dump(r,open(output_dir/'ideal-results.json','w'),indent=2);print(json.dumps(r,indent=2))

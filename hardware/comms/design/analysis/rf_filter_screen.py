import sys,pathlib
input_file=sys.argv[1];output_dir=pathlib.Path(sys.argv[2]);output_dir.mkdir(parents=True,exist_ok=True)
import numpy as np,json,math
j=json.load(open(input_file));comps={c['ref']:c for c in j['components']}
groups={'RX':['C55','L12','C56','C60','L13','C64','C67'],'TX_output':['C84','L19','C87','C89','L21','C92','C94'],'TX_preselector':['C93','L23','C96','C98','L24','C100','C101'],'LO':['C86','L20','C90','C91','L22','C95','C97']}
f=np.arange(350,501,.25)*1e6;result={}
for name,refs in groups.items():
 cs=[comps[r] for r in refs];internal={p['net'] for c in cs[1:-1] for p in c['pads'] if p['net']!='GND'}
 ts=[t for t in j['tracks'] if t['net'] in internal and not t['via'] and t['layer'] in [0,'F.Cu','Top Layer']]
 pts=[];nets=[]
 def node(xy,net):
  if net=='GND':return -1
  for i,(p,n) in enumerate(zip(pts,nets)):
   if n==net and math.dist(p,xy)<.002:return i
  pts.append(xy);nets.append(net);return len(pts)-1
 edges=[]
 for t in ts:edges.append([node(t['a'],t['net']),node(t['b'],t['net'])])
 # Attach component terminal to a nearby track endpoint inside its pad; include short residual lead where needed.
 elements=[];pads={}
 for c in cs:
  ns=[]
  for p in c['pads']:
   n=p['net'];xy=p['xy']
   if n=='GND':idx=-1
   else:
    cand=[i for i,v in enumerate(nets) if v==n]
    idx=min(cand,key=lambda i:math.dist(pts[i],xy)) if cand else node(xy,n)
    d=math.dist(pts[idx],xy)
    assert d<.7,(name,c['ref'],d)
   ns.append(idx);pads[(c['ref'],p['num'])]=idx
  v=float(c['value'][:-1])*({'p':1e-12,'n':1e-9}[c['value'][-1]])
  elements.append((c['ref'][0],v,*ns))
 # Split traces at any same-net intermediate endpoint to retain tee junctions.
 split=[]
 for a,b in edges:
  dx=pts[b][0]-pts[a][0];dy=pts[b][1]-pts[a][1];l2=dx*dx+dy*dy
  if l2<1e-8:continue
  nn=[(0,a),(1,b)]
  for k in range(len(pts)):
   if k in [a,b] or nets[k]!=nets[a]:continue
   u=((pts[k][0]-pts[a][0])*dx+(pts[k][1]-pts[a][1])*dy)/l2
   if 0<u<1 and math.dist(pts[k],[pts[a][0]+u*dx,pts[a][1]+u*dy])<.002:nn.append((u,k))
  nn.sort()
  split.extend((nn[i][1],nn[i+1][1]) for i in range(len(nn)-1))
 edges=list(set(tuple(sorted(e)) for e in split));inp=pads[(refs[0],'1')];out=pads[(refs[-1],'2')]
 vals=[]
 for ff in f:
  w=2*np.pi*ff;Y=np.zeros((len(pts),len(pts)),complex)
  def stamp(a,b,y):
   if a>=0:Y[a,a]+=y
   if b>=0:Y[b,b]+=y
   if a>=0 and b>=0:Y[a,b]-=y;Y[b,a]-=y
  for typ,v,a,b in elements:stamp(a,b,1j*w*v if typ=='C' else 1/(1j*w*v))
  for a,b in edges:
   theta=w*math.sqrt(3.3)/299792458*math.dist(pts[a],pts[b])/1000
   yy=-1j/(50*np.tan(theta));cross=1j/(50*np.sin(theta));Y[a,a]+=yy;Y[b,b]+=yy;Y[a,b]+=cross;Y[b,a]+=cross
  Y[inp,inp]+=.02;Y[out,out]+=.02;I=np.zeros(len(pts),complex);I[inp]=.02
  V=np.linalg.solve(Y,I);vals.append([20*np.log10(abs(2*V[out])),20*np.log10(max(1e-15,abs(2*V[inp]-1)))])
 vals=np.array(vals);pk=np.argmax(vals[:,0]);result[name]={'internal_trace_mm':sum(math.dist(pts[a],pts[b]) for a,b in edges),'nodes':len(pts),'edges':len(edges),'peak_MHz':float(f[pk]/1e6),'peak_S21_dB':float(vals[pk,0]),'435MHz':vals[340].tolist(),'437MHz':vals[348].tolist()}
 np.savetxt(output_dir/('comms-filter-'+name+'.csv'),np.c_[f/1e6,vals],delimiter=',',header='MHz,S21_dB,S11_dB',comments='')
print(json.dumps(result,indent=2));json.dump(result,open(output_dir/'results.json','w'),indent=2)

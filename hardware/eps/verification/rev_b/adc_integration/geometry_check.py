def dirs(p,w):
 x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
 if b==d==y and min(a,c)<=x<=max(a,c):
  if x>min(a,c):out.add('L')
  if x<max(a,c):out.add('R')
 if a==c==x and min(b,d)<=y<=max(b,d):
  if y>min(b,d):out.add('U')
  if y<max(b,d):out.add('D')
 return out
geometry={}
for name,d in rb['layout'].items():
 wires=d['wires'];ends=set();points=set();segs=[]
 for w in wires:
  assert w['x1']==w['x2'] or w['y1']==w['y2']
  assert all(abs(w[k]/1.27-round(w[k]/1.27))<1e-5 for k in ['x1','y1','x2','y2'])
  a=round(w['x1'],4),round(w['y1'],4);b=round(w['x2'],4),round(w['y2'],4);assert a!=b
  ends.update([a,b]);points.update([a,b]);segs.append(tuple(sorted([a,b])))
 assert len(segs)==len(set(segs))
 for a in wires:
  for b in wires:
   p=round(a['x1'],4),round(b['y1'],4)
   if a['x1']==a['x2'] and b['y1']==b['y2'] and min(a['y1'],a['y2'])<=p[1]<=max(a['y1'],a['y2']) and min(b['x1'],b['x2'])<=p[0]<=max(b['x1'],b['x2']):points.add(p)
 doc=parse((P/(name+'.kicad_sch')).read_text())
 placed={(props(s)['Reference'],int(one(s,'unit')[1])):one(s,'at') for s in kids(doc,'symbol')}
 queried=set()
 for c in rb['pins'][name]['components']:
  for unit in c['units']:
   key=(c['reference'],unit['unit']);queried.add(key)
   at=placed[key]
   assert abs(float(at[1])-unit['x'])<1e-5 and abs(float(at[2])-unit['y'])<1e-5
   assert abs(float(at[3])-unit['rotation'])<1e-5
 assert queried==set(placed),name
 native_segments=[tuple(sorted([tuple(map(float,p[1][1:])),tuple(map(float,p[2][1:]))])) for w in kids(doc,'wire') for p in [one(w,'pts')]]
 assert Counter(native_segments)==Counter(segs),name
 native_labels={(l[1],float(one(l,'at')[1]),float(one(l,'at')[2])) for typ in ['label','global_label','hierarchical_label'] for l in kids(doc,typ)}
 assert native_labels=={(l['net'],l['x'],l['y']) for l in d['labels']},name
 junctions={tuple(map(float,one(j,'at')[1:3])) for j in kids(doc,'junction')}
 four={p for p in points if len(set().union(*(dirs(p,w) for w in wires)))==4}
 assert not four&(ends|junctions),(name,four&(ends|junctions))
 assert not any((round(l['x'],4),round(l['y'],4)) in four for l in d['labels'])
 count=0
 for c in rb['pins'][name]['components']:
  for pin in c['pins']:
   p=round(pin['x'],4),round(pin['y'],4)
   assert all(abs(v/1.27-round(v/1.27))<1e-5 for v in p)
   assert len(set().union(*(dirs(p,w) for w in wires)))<3,(name,c['reference'],pin)
   count+=1
 geometry[name]={'segments':len(wires),'connected_fourways':0,'unconnected_crossings':sorted(four),'queried_pin_anchors_including_power_flags':count,'pin_branch_anchors':0}

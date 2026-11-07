#!/usr/bin/env python3
"""Exact UART graph union, metadata, annotation, source-scope and geometry gate."""
from check_common import *
from collections import Counter
import csv,fnmatch,subprocess,sys
BASE='5dfbb932445e03774a2081e0edb8163a7d95ca79'
def descendants(n,key):
    out=[]
    for x in n:
        if isinstance(x,list):
            if x and x[0]==key:out.append(x)
            out.extend(descendants(x,key))
    return out
old,on=graph(H/'before.xml');new,nn=graph(H/'eps_rev_b.xml')
assert (len(old),len(on),len(new),len(nn))==(233,133,243,137)
def meta(c):return {k:c.findtext(k) or '' for k in ['value','footprint','datasheet','tstamps']}|{'libsource':c.find('libsource').attrib,'fields':{x.get('name'):x.text or '' for x in c.findall('fields/field')}}
for r,c in old.items():assert meta(c)==meta(new[r]),r
adds={
 '+3V3':{('U800','5'),('C800','1'),('R804','1'),('R806','1')},
 'GND':{('U800','2'),('C800','2'),('J800','1'),('R802','2'),('R803','2'),('R805','2'),('R806','2')},
 'EPS_UART_TX':{('U100','9'),('U800','1'),('R804','2')},
 'EPS_UART_RX':{('U100','10'),('U800','4'),('R803','1')},
 '/UART debug/UART_TX_BUF':{('U800','6'),('R800','1'),('R802','1')},
 '/UART debug/UART_TX_CONN':{('R800','2'),('J800','2')},
 '/UART debug/UART_RX_CONN':{('J800','3'),('R801','1')},
 '/UART debug/UART_RX_BUF':{('R801','2'),('U800','3'),('R805','1')},
}
expected={k:set(v) for k,v in on.items()};moved={('U100','9'),('U100','10')}
removed={k for k,v in expected.items() if v and v<=moved};assert len(removed)==2
for k in removed:assert k.startswith('unconnected-');del expected[k]
for k,v in adds.items():expected.setdefault(k,set()).update(v)
assert nn==expected,{k:(v,nn.get(k)) for k,v in expected.items() if v!=nn.get(k)}
assert sum(map(len,nn.values()))==673
newrefs={'U800','J800','C800',*[f'R{i}' for i in range(800,807)]};assert set(new)-set(old)==newrefs
assert {p for v in adds.values() for p in v if p[0] in newrefs}=={p for v in nn.values() for p in v if p[0] in newrefs}
mpns={'U800':'74LVC2G34GW,125','J800':'BM03B-GHS-TBT(LF)(SN)','C800':'GRM188R72A104KA35D'}|{f'R{800+i}':'TNPW0603'+code+'BEEA' for i,code in enumerate(['330R','47R0','68K0','68K0','100K','100K','68K0'])}
for r,m in mpns.items():
    f=meta(new[r])['fields'];assert f['MFG P/N']==m and new[r].findtext('footprint')
    if r.startswith('R'):assert (f['Tolerance'],f['Power'],f['PackageSize'],f['TemperatureCoefficient'])==('0.1%','0.110 W general P70','0603','25 ppm/K')
assert all(meta(new['C800'])['fields'][k]==v for k,v in {'Tolerance':'10%','Voltage':'100 V','PackageSize':'0603','Dielectric':'X7R'}.items())
assert new['U800'].findtext('datasheet')=='https://assets.nexperia.com/documents/data-sheet/74LVC2G34.pdf'
rb=json.loads((H/'readback.json').read_text());oldsyms={};current={};ids=[];refunits=[];crosswalk=[]
for path in sorted(P.glob('*.kicad_sch')):
    d=parse(path.read_text());assert one(d,'paper')[1]=='B'
    if path.name!='uart_debug.kicad_sch':
        b=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True)
        for s in kids(parse(b),'symbol'):oldsyms[one(s,'uuid')[1]]=s
    for s in kids(d,'symbol'):
        u=one(s,'uuid')[1];r=props(s)['Reference'];unit=int(one(s,'unit')[1]);ids.append(u);refunits.append((r,unit));current[u]=s
        refs=[x[1] for item in kids(s,'instances') for x in descendants(item,'reference')]
        assert refs and all(v==r for v in refs) and '?' not in r
        crosswalk.append({'reference':r,'unit':unit,'uuid':u,'sheet':path.name,'baseline_retained':u in oldsyms})
assert len(ids)==len(set(ids))==len(refunits)==len(set(refunits))==472
assert len(oldsyms)==451 and all(current[u]==s for u,s in oldsyms.items())
for r in {x[0] for x in refunits}:
    units={n for a,n in refunits if a==r};assert units==({1,2,3} if r=='U800' else {1})
u800=[props(s) for s in current.values() if props(s)['Reference']=='U800'];assert len(u800)==3 and all(p==u800[0] for p in u800)
baseline=json.loads((H/'baseline_sha256.json').read_text());assert baseline['commit']==BASE
allowed={'hardware/eps/rev_b/'+n for n in ['eps_rev_b.kicad_sch','eps_rev_b.kicad_pro','controller.kicad_sch']}
newpaths={'hardware/eps/rev_b/uart_debug.kicad_sch'}|{str((H/'parts_disposable'/('uart_parts_check'+ext)).relative_to(ROOT)) for ext in ['.kicad_sch','.kicad_pro','.kicad_pcb']}
changed={p for p,h in baseline['protected'].items() if sha(ROOT/p)!=h};assert changed==allowed,changed
for p,h in baseline['protected'].items():assert hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)).hexdigest()==h
for p,h in baseline['frozen_bms_evidence'].items():assert sha(ROOT/p)==h,p
protected=lambda p:p.endswith(('.kicad_sch','.kicad_pro','.kicad_pcb','.kicad_sym','.kicad_mod','sym-lib-table','fp-lib-table'))
delta={}
for line in subprocess.check_output(['git','diff','--name-status',BASE,'--','hardware/eps'],cwd=ROOT,text=True).splitlines():
    status,path=line.split('\t')
    if protected(path):delta[path]=status
for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','hardware/eps'],cwd=ROOT,text=True).splitlines():
    if protected(p):delta[p]='A'
assert delta=={**{p:'M' for p in allowed},**{p:'A' for p in newpaths}},delta
manifest=json.loads((H/'native_source_sha256.json').read_text());assert set(manifest)==allowed|newpaths
for p,h in manifest.items():assert sha(ROOT/p)==h,p
cli=json.loads((H/'cli_checks.json').read_text())
for p,h in cli['hierarchy_source_sha256'].items():assert sha(ROOT/p)==h,p
proj=json.loads((P/'eps_rev_b.kicad_pro').read_text());bp=json.loads(subprocess.check_output(['git','show',BASE+':hardware/eps/rev_b/eps_rev_b.kicad_pro'],cwd=ROOT))
assert {k:v for k,v in proj.items() if k!='net_settings'}=={k:v for k,v in bp.items() if k!='net_settings'}
classes=proj['net_settings']['classes'];assert [c for c in classes if c['name']!='UART']==bp['net_settings']['classes']
assert len([c for c in classes if c['name']=='UART'])==1
patterns=proj['net_settings']['netclass_patterns'];assert all(x in patterns for x in bp['net_settings']['netclass_patterns'])
members={n:[p['netclass'] for p in patterns if fnmatch.fnmatchcase(n,p['pattern'])] for n in nn if not n.startswith('unconnected-')}
assert len(members)==121 and all(len(v)==1 for v in members.values())
assert {n for n,v in members.items() if v==['UART']}==set(adds)-{'+3V3','GND'}
geometry={}
def dirs(p,w):
    x,y=p;a,b,c,d=[round(w[k],4) for k in ['x1','y1','x2','y2']];out=set()
    if b==d==y and min(a,c)<=x<=max(a,c):
        if x>min(a,c):out.add('L')
        if x<max(a,c):out.add('R')
    if a==c==x and min(b,d)<=y<=max(b,d):
        if y>min(b,d):out.add('U')
        if y<max(b,d):out.add('D')
    return out
for name,d in rb['layout'].items():
    wires=d['wires'];ends=set();points=set();segs=[]
    for w in wires:
        assert w['x1']==w['x2'] or w['y1']==w['y2']
        assert all(abs(w[k]/1.27-round(w[k]/1.27))<1e-5 for k in ['x1','y1','x2','y2'])
        a=round(w['x1'],4),round(w['y1'],4);b=round(w['x2'],4),round(w['y2'],4);assert a!=b;ends.update([a,b]);points.update([a,b]);segs.append(tuple(sorted([a,b])))
    assert len(segs)==len(set(segs))
    for a in wires:
        for b in wires:
            p=round(a['x1'],4),round(b['y1'],4)
            if a['x1']==a['x2'] and b['y1']==b['y2'] and min(a['y1'],a['y2'])<=p[1]<=max(a['y1'],a['y2']) and min(b['x1'],b['x2'])<=p[0]<=max(b['x1'],b['x2']):points.add(p)
    junctions={tuple(map(float,one(j,'at')[1:3])) for j in kids(parse((P/(name+'.kicad_sch')).read_text()),'junction')}
    four={p for p in points if len(set().union(*(dirs(p,w) for w in wires)))==4};assert not four&(ends|junctions)
    assert not any((round(l['x'],4),round(l['y'],4)) in four for l in d['labels'])
    count=0
    for c in rb['pins'][name]['components']:
        for pin in c['pins']:
            p=round(pin['x'],4),round(pin['y'],4);assert all(abs(v/1.27-round(v/1.27))<1e-5 for v in p)
            assert len(set().union(*(dirs(p,w) for w in wires)))<3,(name,c['reference'],pin);count+=1
    geometry[name]={'segments':len(wires),'connected_fourways':0,'unconnected_crossings':sorted(four),'queried_pin_anchors':count,'pin_branch_anchors':0}
erc=json.loads((H/'erc.json').read_text());v=[v for s in erc['sheets'] for v in s['violations']]
assert Counter((x['severity'],x['type']) for x in v)=={('error','pin_not_connected'):9,('error','pin_to_pin'):3}
subprocess.run([sys.executable,str(H/'verify_parts.py')],check=True,capture_output=True,text=True)
for filename,value in [('reference_UUID_crosswalk.json',crosswalk),('geometry.json',geometry),('class_membership.json',members),('fields_readback.json',{r:meta(new[r]) for r in sorted(newrefs)})]:(H/filename).write_text(json.dumps(value,indent=2)+'\n')
with (H/'endpoint_contract.csv').open('w') as f:
    rows=[{'reference':r,'pin':p,'net':n,'whole_net_endpoints':';'.join(a+'.'+b for a,b in sorted(nn[n]))} for n,v in adds.items() for r,p in sorted(v)];w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
result={'basis':BASE,'status':'DEVELOPMENT UART GRAPH / METADATA / PHYSICAL MAP PASS; BENCH/INHIBIT/POLICY GATES OPEN','parts':243,'nets':137,'functional_nets':121,'physical_pin_endpoints':673,'previous_parts_preserved':233,'previous_symbol_objects_preserved':451,'current_symbol_objects':472,'added_parts':10,'ERC_errors':12,'ERC_warnings':0,'frozen_tracked_BMS_files':len(baseline['frozen_bms_evidence']),'geometry':geometry,'protected_delta':delta}
(H/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

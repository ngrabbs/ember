#!/usr/bin/env python3
"""Independent full-root SWD topology/preservation check against the authored contract."""
import argparse,fnmatch,hashlib,json,xml.etree.ElementTree as E
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--netlist',type=Path,required=True)
parser.add_argument('--classes',type=Path,required=True)
parser.add_argument('--erc',type=Path,required=True)
args=parser.parse_args()
old_path=ROOT/'hardware/eps/verification/rev_b/can_branch_integration/eps_rev_b.xml'
def graph(path):
 r=E.parse(path).getroot();cs={c.get('ref'):c for c in r.findall('./components/comp')};nets={};pn={}
 for n in r.findall('./nets/net'):
  name=n.get('name');nodes={(p.get('ref'),p.get('pin')) for p in n.findall('node')}
  assert name not in nets
  nets[name]=nodes
  for k in nodes:assert k not in pn;pn[k]=name
 return cs,nets,pn
oldc,oldnets,oldpn=graph(old_path)
c,nets,pn=graph(args.netlist)
assert len(oldc)==305 and len(c)==318
assert set(c)==set(oldc)|{'U1200','U1201','C1200','C1201'}|{f'R{i}' for i in range(1200,1209)}
def canonical(el):
 q=E.fromstring(E.tostring(el,encoding='unicode'));q.tail=None
 return E.tostring(q,encoding='unicode')
for ref in oldc:
 if ref!='J100':assert canonical(c[ref])==canonical(oldc[ref]),f'Old component metadata/UUID changed: {ref}'
rename={'/Controller/EPS_SWDIO':'EPS_SWDIO','/Controller/EPS_SWCLK':'EPS_SWCLK','/Controller/EPS_NRST':'EPS_NRST'}
for k,n in oldpn.items():
 if k[0]!='J100':assert pn[k]==rename.get(n,n),(k,n,pn[k])
expected={rename.get(n,n):{p for p in nodes if p[0]!='J100'} for n,nodes in oldnets.items()}
def add(n,*nodes):expected[n].update(nodes)
add('+3V3',('U1200','14'),('U1200','12'),('U1201','3'),('C1200','1'),('C1201','1'),('R1203','1'),('R1204','1'),('R1207','1'))
add('GND',('U1200','7'),('U1201','1'),('C1200','2'),('C1201','2'),('R1205','2'),('R1206','2'),('R1207','2'),('R1208','2'),('J100','5'))
add('EPS_SWDIO',('R1200','1'),('R1203','2'))
add('EPS_SWCLK',('R1201','1'),('R1205','1'))
add('EPS_NRST',('R1202','1'),('R1204','2'))
for members in [
 {('R1200','2'),('U1200','2')},
 {('U1200','3'),('J100','2')},
 {('R1201','2'),('U1200','5')},
 {('U1200','6'),('J100','4')},
 {('R1202','2'),('U1200','9')},
 {('U1200','8'),('J100','3')},
 {('U1200','1'),('U1200','4'),('U1200','10'),('U1200','13'),('U1201','2'),('R1206','1')},
 {('U1200','11'),('J100','1'),('R1208','1')},
 {('J100','6')},
]:
 name=pn[next(iter(members))];assert name not in expected,(name,members)
 expected[name]=members
assert nets==expected,{'missing':sorted(set(expected)-set(nets)),'extra':sorted(set(nets)-set(expected)),'different':[n for n in nets.keys()&expected.keys() if nets[n]!=expected[n]]}
assert len(nets)==175 and sum(map(len,nets.values()))==866
assert 'SWD_SUPPLY_OK' in pn[('U1201','2')]
assert pn[('J100','1')]=='3V3_SWD_VTREF'
assert pn[('J100','6')].startswith('unconnected-')
mpns={'U1200':'TMUX1511PWR','U1201':'TPS3839K33DBZR','J100':'TC2030-CTX-NL','C1200':'GRM188R72A104KA35D','C1201':'GRM188R72A104KA35D'}
mpns.update({f'R{i}':'TNPW0603330RBEEA' for i in range(1200,1203)})
mpns.update({f'R{i}':'TNPW060310K0BEEA' for i in [1203,1204,1206,1207,1208]});mpns['R1205']='TNPW060347K0BEEA'
for ref,mpn in mpns.items():
 f={p.get('name'):p.text for p in c[ref].findall('fields/field')}
 assert f['MFG P/N']==mpn,(ref,f.get('MFG P/N'))
 assert c[ref].findtext('footprint'),ref
 assert set(p.get('num') for p in c[ref].findall('units/unit/pins/pin'))=={p for rr,p in pn if rr==ref},ref
classes=json.loads(args.classes.read_text())
functional={n for n in nets if not n.startswith('unconnected-')}
assert len(functional)==158
membership={n:[cl['name'] for cl in classes['netclasses'] if any(fnmatch.fnmatchcase(n,pattern) for pattern in cl.get('patterns',[]))] for n in sorted(functional)}
assert all(len(m)==1 for m in membership.values()),{n:m for n,m in membership.items() if len(m)!=1}
assert membership['3V3_SWD_VTREF']==['POWER']
assert membership[pn[('U1201','2')]]==['CONTROL']
for ref,pin in [('J100','2'),('J100','3'),('J100','4'),('R1200','2'),('R1201','2'),('R1202','2'),('U100','24'),('U100','25'),('U100','6')]:assert membership[pn[(ref,pin)]]==['DEBUG']
orphans=[{'class':cl['name'],'pattern':pattern} for cl in classes['netclasses'] for pattern in cl.get('patterns',[]) if not any(fnmatch.fnmatchcase(n,pattern) for n in functional)]
def ercsig(path):
 d=json.loads(path.read_text());out=[]
 for sh in d['sheets']:
  for v in sh['violations']:out.append((sh['path'],v['type'],v['severity'],v['description'],tuple(sorted(i['description'] for i in v['items']))))
 return sorted(out),d['ignored_checks']
current_erc=ercsig(args.erc);old_erc=ercsig(ROOT/'hardware/eps/verification/controller_rev_b/branch_control_screen/root_erc.json')
assert current_erc[1]==old_erc[1], 'Ignored checks changed'
extra=[v for v in current_erc[0] if v not in old_erc[0]]
assert [v for v in current_erc[0] if v not in extra]==old_erc[0], 'Prior ERC findings changed'
expected_warning_pairs={
 ('Symbol #FLG0402 Pin 1 [Power output, Line]', 'Symbol U1200 Pin 12 [S4, Bidirectional, Line]'),
 ('Symbol #FLG1200 Pin 1 [Power output, Line]', 'Symbol U1200 Pin 11 [D4, Bidirectional, Line]'),
}
assert len(extra)==2 and {v[4] for v in extra}==expected_warning_pairs
assert all(v[:4]==('/SWD Service/','pin_to_pin','warning','Pins of type Bidirectional and Power output are connected') for v in extra)
assert len(current_erc[0])==12 and sum(v[2]=='error' for v in current_erc[0])==10
report={'status':'INDEPENDENT_COMPLETE_GRAPH_PASS','physical_parts':len(c),'nets':len(nets),'endpoints':sum(map(len,nets.values())),'functional_nets':158,'functional_net_classes':membership,'orphan_class_patterns':orphans,'unchanged_ERC_errors':10,'ERC_warnings':2,'additional_exact_supply_join_warnings':extra,'erc_sha256':hashlib.sha256(args.erc.read_bytes()).hexdigest(),'preserved_old_physical_metadata_and_UUIDs':304,'explicit_logical_J100_replacement':{'old_uuid':oldc['J100'].findtext('tstamps'),'new_uuid':c['J100'].findtext('tstamps')},'intended_internal_signal_scope_migrations':rename,'new_parts_MPN':mpns,'netlist_sha256':hashlib.sha256(args.netlist.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(old_path.read_bytes()).hexdigest(),'limits':'Native connectivity and metadata only; ERC/classes/render inspection and electrical qualification are separate.'}
(HERE/'integrated_graph_verified.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:318parts/175nets/866endpoints;304oldparts metadata/UUIDs preserved;entire root matches SWD topology contract.')

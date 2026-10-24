#!/usr/bin/env python3
"""Read-only all-symbol reference and instance-annotation gate, including power flags."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[4];P=ROOT/'hardware/eps/rev_b'
def parse(text):
    stack=[];root=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',text):
        if t=='(':
            n=[]
            if stack:stack[-1].append(n)
            else:root=n
            stack.append(n)
        elif t==')':stack.pop()
        else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
    assert not stack;return root
def children(n,k):return [v for v in n if isinstance(v,list) and v and v[0]==k]
def descendants(n,k):
    out=[]
    for x in n:
        if isinstance(x,list):
            if x and x[0]==k:out.append(x)
            out.extend(descendants(x,k))
    return out
def collect(files,baseline=False):
    rows=[]
    for name in files:
        rel='hardware/eps/rev_b/'+name+'.kicad_sch'
        text=subprocess.check_output(['git','show','8d03a76:'+rel],cwd=ROOT,text=True) if baseline else (ROOT/rel).read_text()
        for sym in children(parse(text),'symbol'):
            props={x[1]:x[2] for x in children(sym,'property')};ref=props['Reference'];assert '?' not in ref and ref
            instance_refs=[x[1] for x in descendants(sym,'reference')];assert instance_refs and all(x==ref for x in instance_refs),(name,ref,instance_refs)
            uuid=children(sym,'uuid')[0][1];at=children(sym,'at')[0]
            rows.append({'sheet':name,'reference':ref,'uuid':uuid,'x':float(at[1]),'y':float(at[2]),'instance_references':instance_refs})
    uuids=[r['uuid'] for r in rows];assert len(uuids)==len(set(uuids)),Counter(uuids)
    refs=[r['reference'] for r in rows];assert len(refs)==len(set(refs)),[(r,n) for r,n in Counter(refs).items() if n>1]
    normalized=[(re.sub(r'\d+$','',r),int(re.search(r'\d+$',r)[0])) if re.match(r'^#(?:PWR|FLG)\d+$',r) else r for r in refs]
    assert len(normalized)==len(set(normalized)),Counter(normalized)
    return rows
files=['eps_rev_b','controller','can_interfaces','essential_3v3','recovery_5v','source_protection','rail_protection']
old=collect(files,True);new=collect(files+['charger']);oldids={r['uuid']:r for r in old};newids={r['uuid']:r for r in new}
assert all(newids[u]==r for u,r in oldids.items())
queries=json.loads((H/'all_symbol_readback.json').read_text());q={(name,c['reference']) for name,d in queries.items() for c in d['components']}
assert q=={(r['sheet'],r['reference']) for r in new}
fixed=next(r for r in new if r['uuid']=='5f89cd56-0068-489c-83b7-a26ef5b519f7');assert fixed['reference']=='#PWR0322' and fixed['sheet']=='charger' and (fixed['x'],fixed['y'])==(335.28,191.77)
assert len([r for r in new if r['reference']=='#PWR001'])==1
cli=json.loads((H/'cli_annotation_check.json').read_text());assert cli['exit_code']==0 and not cli['annotation_warning']
assert cli['netlist_sha256']==hashlib.sha256((H/'eps_rev_b.xml').read_bytes()).hexdigest()
assert cli['charger_source_sha256']==hashlib.sha256((P/'charger.kicad_sch').read_bytes()).hexdigest()
result={'status':'ALL SYMBOL / INSTANCE ANNOTATION PASS; FRESH CLI WARNING ABSENT','baseline_all_symbols':len(old),'current_all_symbols':len(new),'physical_symbols':len([r for r in new if not r['reference'].startswith('#')]),'power_or_flag_symbols':len([r for r in new if r['reference'].startswith('#')]),'all_refs_unique':True,'normalized_power_numbers_unique':True,'all_prior_symbol_UUID_reference_position_instances_preserved':len(old),'introduced_defect':'New automatic #PWR001 was duplicated on controller +3V3 and charger NTC return; physical-only XML did not expose it','repair':'Only new charger GND renamed #PWR0322 via Konnect; UUID/position/connectivity unchanged','fixed_symbol':fixed,'CLI_annotation_warning':False,'symbols':new}
(H/'annotation_verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='symbols'},indent=2))

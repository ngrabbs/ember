#!/usr/bin/env python3
"""Read-only saved pad geometry omitted by Konnect's live pad-position API."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
BOARD = HERE/'disposable/charger_bms_check.kicad_pcb'

def parse(text):
    stack=[]
    root=None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',text):
        if token=='(':
            node=[]
            if stack: stack[-1].append(node)
            else: root=node
            stack.append(node)
        elif token==')': stack.pop()
        else: stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and root[0]=='kicad_pcb'
    return root

def children(node,key): return [n for n in node if isinstance(n,list) and n and n[0]==key]
def child(node,key):
    ns=children(node,key)
    assert len(ns)==1,(key,len(ns))
    return ns[0]

root=parse(BOARD.read_text())
result={'source':'read_only_saved_native_geometry; API omits shape/type/size/drill',
        'board_sha256':hashlib.sha256(BOARD.read_bytes()).hexdigest(),'instances':{}}
for fp in children(root,'footprint'):
    props={v[1]:v[2] for v in children(fp,'property')}
    pads=[]
    for p in children(fp,'pad'):
        at=child(p,'at');size=child(p,'size');rr=children(p,'roundrect_rratio')
        pads.append({'number':p[1],'type':p[2],'shape':p[3],
                     'x':float(at[1]),'y':float(at[2]),'rotation':float(at[3]) if len(at)>3 else 0,
                     'width':float(size[1]),'height':float(size[2]),
                     'layers':child(p,'layers')[1:],'drill':children(p,'drill'),
                     'roundrect_rratio':float(rr[0][1]) if rr else None})
    at=child(fp,'at')
    result['instances'][props['Reference']]={'library_id':fp[1],'uuid':child(fp,'uuid')[1],
        'x':float(at[1]),'y':float(at[2]),'rotation':float(at[3]) if len(at)>3 else 0,
        'layer':child(fp,'layer')[1],'properties':props,'pads':pads}
result['other_board_items']={key:len(children(root,key)) for key in ('segment','via','zone','gr_line','gr_rect','gr_poly','gr_arc','gr_text')}
(HERE/'board_saved_geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print('Read',sum(len(v['pads']) for v in result['instances'].values()),'saved pads; no native writes')

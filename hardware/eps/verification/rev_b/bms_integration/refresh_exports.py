#!/usr/bin/env python3
"""Read-only KiCad CLI electrical/PDF exports; never writes native design files."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[4];P=ROOT/'hardware/eps/rev_b'
cli='/opt/homebrew/bin/kicad-cli';sch=str(P/'eps_rev_b.kicad_sch')
commands={
 'netlist':[cli,'sch','export','netlist','--format','kicadxml','--output',str(H/'eps_rev_b.xml'),sch],
 'ERC':[cli,'sch','erc','--format','json','--output',str(H/'erc.json'),sch],
 'PDF':[cli,'sch','export','pdf','--output',str(H/'eps_rev_b.pdf'),sch],
 'fixture_netlist':[cli,'sch','export','netlist','--format','kicadxml','--output',str(H/'parts_disposable.xml'),str(H/'parts_disposable/bms_parts_check.kicad_sch')],
 'fixture_ERC':[cli,'sch','erc','--format','json','--output',str(H/'parts_disposable_erc.json'),str(H/'parts_disposable/bms_parts_check.kicad_sch')],
}
out={}
for name,cmd in commands.items():
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,(name,r.stdout,r.stderr)
 out[name]={'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,
            'annotation_warning':'annotation error' in (r.stderr+r.stdout).lower()}
 assert not out[name]['annotation_warning'],name
out['version']=subprocess.check_output([cli,'version'],text=True).strip()
out['netlist_sha256']=hashlib.sha256((H/'eps_rev_b.xml').read_bytes()).hexdigest()
out['hierarchy_source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.glob('*.kicad_sch'))}
(H/'cli_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print('Fresh full-root XML/ERC/PDF and disposable electrical exports saved; no annotation warning.')

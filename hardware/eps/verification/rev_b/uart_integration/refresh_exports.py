#!/usr/bin/env python3
"""Read-only KiCad exports; no native files are modified."""
from check_common import *
import subprocess
cli='/opt/homebrew/bin/kicad-cli'
commands={
 'netlist':[cli,'sch','export','netlist','--format','kicadxml','--output',str(H/'eps_rev_b.xml'),str(P/'eps_rev_b.kicad_sch')],
 'ERC':[cli,'sch','erc','--format','json','--output',str(H/'erc.json'),str(P/'eps_rev_b.kicad_sch')],
 'PDF':[cli,'sch','export','pdf','--output',str(H/'eps_rev_b.pdf'),str(P/'eps_rev_b.kicad_sch')],
 'fixture_netlist':[cli,'sch','export','netlist','--format','kicadxml','--output',str(H/'parts_disposable.xml'),str(H/'parts_disposable/uart_parts_check.kicad_sch')],
 'fixture_ERC':[cli,'sch','erc','--format','json','--output',str(H/'parts_disposable_erc.json'),str(H/'parts_disposable/uart_parts_check.kicad_sch')],
}
out={}
for name,cmd in commands.items():
    r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,(name,r.stdout,r.stderr)
    out[name]={'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    assert 'annotation error' not in (r.stdout+r.stderr).lower(),name
out['version']=subprocess.check_output([cli,'version'],text=True).strip()
out['hierarchy_source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in sorted(P.glob('*.kicad_sch'))}
(H/'cli_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print('Fresh XML/ERC/ten-page PDF and disposable electrical checks saved.')

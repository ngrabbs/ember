from common import *
import hashlib,subprocess
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=ROOT/'hardware/eps/rev_b'
initial={str(p.relative_to(ROOT)):sha(p) for p in [P/'eps_rev_b.kicad_sch',P/'controller.kicad_sch',P/'eps_rev_b.kicad_pro']}
frozen={}
for base in [ROOT/'hardware/eps/rev_b',ROOT/'hardware/eps/studies',ROOT/'hardware/eps/verification']:
 for p in base.rglob('*'):
  s=str(p.relative_to(ROOT))
  if p.is_file() and portable(p) and not p.is_relative_to(H) and s not in initial:frozen[s]=sha(p)
protected=[p for p in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines() if p.endswith(('.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym','.kicad_mod')) or Path(p).name in {'sym-lib-table','fp-lib-table'}]
(H/'baseline.json').write_text(json.dumps({'basis':'0660ad3','initial':initial,'frozen':frozen,'tracked_protected':protected},indent=2)+'\n')
for f in ['eps_rev_b.kicad_sch','controller.kicad_sch','eps_rev_b.kicad_pro']:(H/('project_before.json' if f.endswith('.kicad_pro') else f.split('.')[0]+'_before.txt')).write_bytes((P/f).read_bytes())
cmd=['/opt/homebrew/bin/kicad-cli','sch','export','netlist','--format','kicadxml','--output',str(H/'before.xml'),str(P/'eps_rev_b.kicad_sch')]
r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0 and 'annotation errors' not in r.stderr+r.stdout
(H/'before_cli.json').write_text(json.dumps({'command':cmd,'stdout':r.stdout,'stderr':r.stderr})+'\n')
for f in ['eps_rev_b','controller']:
 doc=parse((P/(f+'.kicad_sch')).read_text())
 if f=='eps_rev_b':print('SHEETS',[(props(s),one(s,'at'),one(s,'size')) for s in kids(doc,'sheet')]);print('TEXT',[(t[1],one(t,'at')) for t in kids(doc,'text')])
 else:print('LABELS',[(l[1],one(l,'at'),one(l,'uuid')) for l in kids(doc,'label')]);print('TEXT',[(t[1],one(t,'at'),one(t,'uuid')) for t in kids(doc,'text')])
print('Frozen',len(frozen),'initial',len(initial))

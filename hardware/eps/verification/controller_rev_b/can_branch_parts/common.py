from pathlib import Path
import re,json,hashlib
H=Path(__file__).resolve().parent
ROOT=H.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def portable(p):
 q=Path(p)
 return not (any(x in {'.history','.git','__pycache__','.cache','.pytest_cache'} or x.endswith('-backups') for x in q.parts) or q.name in {'.DS_Store','fp-info-cache'} or q.suffix in {'.kicad_prl','.lck','.pyc'} or q.name.endswith('~'))
def parse(s):
 stack=[];root=None
 for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',s):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   else:root=n
   stack.append(n)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 assert not stack
 return root
def kids(n,k):return [x for x in n if isinstance(x,list) and x and x[0]==k]
def one(n,k):return kids(n,k)[0]
def props(n):return {p[1]:p[2] for p in kids(n,'property')}
def unwrap(r):return json.loads(r['content'][0]['text'])

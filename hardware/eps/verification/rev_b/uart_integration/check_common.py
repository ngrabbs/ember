from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
H=Path(__file__).resolve().parent
ROOT=H.parents[4]
P=ROOT/'hardware/eps/rev_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
    assert not stack
    return root
def kids(n,k):return [x for x in n if isinstance(x,list) and x and x[0]==k]
def one(n,k):return kids(n,k)[0]
def graph(p):
    r=E.parse(p).getroot();cs=r.findall('components/comp');refs=[c.get('ref') for c in cs]
    assert len(refs)==len(set(refs))
    nodes=[(p.get('ref'),p.get('pin')) for n in r.findall('nets/net') for p in n.findall('node')]
    assert len(nodes)==len(set(nodes))
    return {c.get('ref'):c for c in cs},{n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in r.findall('nets/net')}
def props(n):return {p[1]:p[2] for p in kids(n,'property')}

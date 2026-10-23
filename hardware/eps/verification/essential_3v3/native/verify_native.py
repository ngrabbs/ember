#!/usr/bin/env python3
"""Read-only verification of the saved KiCad export and Konnect readbacks."""
from pathlib import Path
import collections,csv,hashlib,json,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent
P=H.parents[4]/"hardware/eps/studies/essential_3v3"
def read(n):return json.loads((H/n).read_text())
root=ET.parse(H/"essential_3v3.xml").getroot()
comps={c.attrib["ref"]:c for c in root.find("components")}
nets={n.attrib["name"]:sorted(c.attrib["ref"]+"."+c.attrib["pin"] for c in n) for n in root.find("nets")}
caps=["C"+str(i) for i in range(5,13)]
expected={"SYS_PWR_PERMITTED":["U1.2","U1.3","C1.1","C2.1","C3.1"],"GND":["U1.4","C1.2","C2.2","C3.2","R2.2"]+[c+".2" for c in caps],"/BUCK33_SW":["U1.5","C4.2","L1.1"],"/BUCK33_CB":["U1.6","C4.1"],"/BUCK33_FB":["U1.1","R1.2","R2.1"],"+3V3":["L1.2","R1.1"]+[c+".1" for c in caps]}
assert nets=={n:sorted(ep) for n,ep in expected.items()},nets
assert len(comps)==16
fields={}
for plan in read("planned_metadata.json"):
 r=plan["reference"];c=comps[r];f={e.attrib["name"]:e.text or "" for e in c.find("fields")}
 assert c.findtext("value")==plan["value"]
 assert c.findtext("footprint")==plan["footprint"]
 assert all(f.get(k)==v for k,v in plan["fields"].items()),r
 required=["MFG P/N"]
 if r.startswith("C"):required+=["PackageSize","Tolerance","Voltage","Dielectric","EffectiveCapacitance"]
 if r.startswith("R"):required+=["PackageSize","Tolerance","Power"]
 if r=="L1":required+=["RatedCurrent","SaturationCurrent","DCR"]
 assert all(f.get(k) for k in required),r
 fields[r]={"value":c.findtext("value"),"footprint":c.findtext("footprint"),"fields":f}
assert all(fields[c]["fields"]["MFG P/N"]=="GRM32ER71E226KE15L" for c in caps)
assert fields["L1"]["fields"]["MFG P/N"]=="XAL6060-562MEC"
symbol=read("ic_symbol.json")
assert {p["number"]:p["name"] for p in symbol["pins"]}=={"1":"FB","2":"EN","3":"VIN","4":"GND","5":"SW","6":"CB"}
pads=read("ic_footprint.json")["pads"]
assert len(pads)==6 and sorted(int(p["number"]) for p in pads)==list(range(1,7))
assert all(not p["drill"] for p in pads)
for pad in read("inductor_footprint.json")["pads"]:
 assert abs(pad["height"]-5.5)<1e-8 and abs(pad["width"]-1.43)<1e-8 and abs(abs(pad["x"])-2.02)<1e-8 and pad["y"]==0
g=read("geometry.json");wires=g["wires"]
def pt(x,y):return round(x,4),round(y,4)
def rays(p,w):
 x,y=p; ax,ay,bx,by=[round(w[k],4) for k in ("x1","y1","x2","y2")];s=set()
 if ay==by==y and min(ax,bx)<=x<=max(ax,bx):
  if x>min(ax,bx):s.add("L")
  if x<max(ax,bx):s.add("R")
 if ax==bx==x and min(ay,by)<=y<=max(ay,by):
  if y>min(ay,by):s.add("U")
  if y<max(ay,by):s.add("D")
 return s
def degree(p):return set().union(*(rays(p,w) for w in wires))
points=set()
for w in wires:
 assert w["x1"]==w["x2"] or w["y1"]==w["y2"]
 for k in ("x1","y1","x2","y2"):assert abs(w[k]/1.27-round(w[k]/1.27))<1e-6
 points|={pt(w["x1"],w["y1"]),pt(w["x2"],w["y2"])}
for a in wires:
 for b in wires:
  q=pt(a["x1"],b["y1"])
  if a["x1"]==a["x2"] and b["y1"]==b["y2"] and rays(q,a) and rays(q,b):points.add(q)
assert not [p for p in points if len(degree(p))>=4]
for c in read("pins.json")["components"]:
 for p in c["pins"]:assert len(degree(pt(p["x"],p["y"])))==1,(c["reference"],p["number"])
for c in g["components"]:
 if c["reference"].startswith("#"):assert len(degree(pt(c["x"],c["y"])))==1,c["reference"]
assert all(l["type"]=="NetLabel" and l["net"] not in {"GND","+3V3","SYS_PWR_PERMITTED"} for l in g["labels"])
erc=read("erc.json");assert sum(len(s["violations"]) for s in erc["sheets"])==0
assert "four_way_junction" in {x["key"] for x in erc["ignored_checks"]}
project=json.loads((P/"essential_3v3.kicad_pro").read_text())
classes={p["pattern"]:p["netclass"] for p in project["net_settings"]["netclass_patterns"]}
assert classes=={"SYS_PWR_PERMITTED":"POWER","GND":"POWER","+3V3":"POWER","/BUCK33_SW":"SWITCHING","/BUCK33_CB":"SWITCHING","/BUCK33_FB":"ANALOG"}
for table in ["sym-lib-table","fp-lib-table"]:
 s=(P/table).read_text();assert "${KIPRJMOD}/../../libraries/" in s and "/Users/" not in s
result={"status":"NATIVE_ENDPOINT_METADATA_AND_GEOMETRY_CHECKS_PASS; DEVELOPMENT_QUALIFICATION_OPEN","physical_parts":16,"endpoint_sets":nets,"erc_errors":0,"erc_warnings":0,"wire_segments":len(wires),"four_way_intersections":0,"pin_anchors_at_branch":0,"netclass_members":6,"power_flags":{"input":"external permitted power interface","ground":"external return","output":"actual buck output after passive inductor"},"unverified":["effective capacitance/current/temperature bounds","hot inductance and fault survival","internal-loop/PFM startup and real load transients","weak-source chatter","thermal physical fit","autonomous3V3 output fault containment","S03 native severity","S11 visible ratings","S08 reused custom review marker coverage"],"sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.iterdir() if p.name.endswith((".kicad_sch",".kicad_pro")) or p.name in {"sym-lib-table","fp-lib-table"}}}
(H/"verified.json").write_text(json.dumps(result,indent=2)+"\n")
(H/"fields_readback.json").write_text(json.dumps(fields,indent=2)+"\n")
with (H/"endpoint_sets.csv").open("w") as f:
 wr=csv.writer(f,lineterminator="\n");wr.writerow(["Net","Endpoints"])
 for n,e in nets.items():wr.writerow([n,"; ".join(e)])
print(json.dumps(result,indent=2))

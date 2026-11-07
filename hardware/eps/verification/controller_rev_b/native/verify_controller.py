#!/usr/bin/env python3
"""Verify saved KiCad CLI exports and Konnect readbacks for the bounded controller study."""
from pathlib import Path
import collections, csv, hashlib, json, math, xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
PROJECT = REPO / "hardware/eps/studies/controller_rev_b"
def read(name): return json.loads((HERE / name).read_text())
def nets(path):
    root = ET.parse(path).getroot()
    return {n.attrib["name"]: sorted(x.attrib["ref"]+"."+x.attrib["pin"] for x in n) for n in root.find("nets")}
def canonical(data):
    return {name.rsplit("/",1)[-1]: ep for name,ep in data.items() if not name.startswith("unconnected-")}
old, new = nets(HERE/"scratch_before.xml"), nets(HERE/"controller.xml")
oldc, newc = canonical(old), canonical(new)
assert len(oldc) == 17
for name, endpoints in oldc.items(): assert newc[name] == endpoints, (name, endpoints, newc.get(name))
assert set(newc)-set(oldc) == {"REC5_RESET","REC5_FAULT","SRC_FAULT"}
assert newc["REC5_RESET"] == ["U1.13"]
assert newc["REC5_FAULT"] == ["U1.14"]
assert newc["SRC_FAULT"] == ["U1.3"]
assert len(newc) == 20
unfinished = {7,8,9,10,11,12,17,18,19,21,26,28,29,30,31,32}
assert sorted(ep for n,eps in new.items() if n.startswith("unconnected-") for ep in eps) == sorted("U1."+str(p) for p in unfinished)
xml = ET.parse(HERE/"controller.xml").getroot()
comps = {c.attrib["ref"]: c for c in xml.find("components")}
assert len(comps) == 27
assert set(comps) == {c.attrib["ref"] for c in ET.parse(HERE/"scratch_before.xml").getroot().find("components")}
planned = read("planned_metadata.json")
field_readback = {}
for item in planned:
    ref = item["reference"]; c = comps[ref]
    assert c.findtext("value") == item["value"], ref
    assert (c.findtext("footprint") or "") == item["footprint"], ref
    f = {e.attrib["name"]:e.text or "" for e in c.find("fields")}
    for k,v in item["fields"].items(): assert f[k] == v, (ref,k)
    required = ["MFG P/N"]
    if ref.startswith("C"): required += ["PackageSize","Tolerance","Voltage","Dielectric"]
    if ref.startswith("R"): required += ["PackageSize","Tolerance","Power"]
    assert all(f.get(k) for k in required), (ref,required)
    field_readback[ref] = {"value":c.findtext("value"),"footprint":c.findtext("footprint") or "", "fields":f}
assert comps["U1"].find("libsource").attrib == {"lib":"MCU_ST_STM32G0", "part":"STM32G0B1KETxN", "description":comps["U1"].find("libsource").attrib["description"]}
assert field_readback["U1"]["fields"]["MFG P/N"] == "STM32G0B1KET6N"
assert comps["C4"].findtext("value") == "4.7uF"
assert all(field_readback[r]["fields"]["Population"] == "DNP" for r in ["R7","R8"])
unselected = ["J1","J2","J3","R7","R8"]
assert all(not field_readback[r]["footprint"] and "UNSELECTED" in field_readback[r]["fields"]["MFG P/N"] for r in unselected)
expected = {1:"PB9",2:"PC14",3:"PC15",4:"VDD",5:"VSS",6:"PF2",7:"PA0",8:"PA1",9:"PA2",10:"PA3",11:"PA4",12:"PA5",13:"PA6",14:"PA7",15:"PB0",16:"PB1",17:"PB15",18:"PA8",19:"PA9/UCPD1_DBCC1",20:"VDD",21:"PA10/UCPD1_DBCC2",22:"PA9/PA11",23:"PA10/PA12",24:"PA13",25:"PA14",26:"PD0",27:"PD1",28:"PD2",29:"PD3",30:"PB6",31:"PB7",32:"PB8"}
symbol = read("stock_n_symbol.json")
assert {int(p["number"]):p["name"] for p in symbol["pins"]} == expected
padmap = read("mcu_n_footprint.json")["pads"]
assert len(padmap) == 32 and sorted(int(p["number"]) for p in padmap) == list(range(1,33))
assert all(not p["drill"] and p["type"]=="smd" for p in padmap)
project = json.loads((PROJECT/"controller_rev_b.kicad_pro").read_text())
classes = project["net_settings"]
actual_classes = {p["pattern"]:p["netclass"] for p in classes["netclass_patterns"]}
for cls,names in read("netclass_intent.json").items():
    for name in names: assert actual_classes[name] == cls and name in new, (cls,name)
assert len(actual_classes) == 20
# Geometric evidence is separate from ERC, whose four-way rule is currently ignored.
def pt(x,y): return round(x,4),round(y,4)
def directions(p,w):
    x,y=p;x1,y1,x2,y2=(round(w[k],4) for k in ("x1","y1","x2","y2"))
    out=set()
    if y1==y2==y and min(x1,x2)<=x<=max(x1,x2):
        if x>min(x1,x2):out.add("L")
        if x<max(x1,x2):out.add("R")
    if x1==x2==x and min(y1,y2)<=y<=max(y1,y2):
        if y>min(y1,y2):out.add("U")
        if y<max(y1,y2):out.add("D")
    return out
geometry = {}
for filename,pinfile in [("root_geometry.json","root_pins.json"),("can_geometry.json","can_pins.json")]:
    g=read(filename); wires=g["wires"]; points=set()
    for w in wires:
        assert w["x1"]==w["x2"] or w["y1"]==w["y2"]
        for k in ("x1","y1","x2","y2"): assert abs(w[k]/1.27-round(w[k]/1.27)) < 1e-6, (filename,k,w)
        points |= {pt(w["x1"],w["y1"]),pt(w["x2"],w["y2"])}
    def deg(p):return set().union(*(directions(p,w) for w in wires))
    for a in wires:
        for b in wires:
            if a["x1"]==a["x2"] and b["y1"]==b["y2"]:
                q=pt(a["x1"],b["y1"])
                if directions(q,a) and directions(q,b):points.add(q)
    four=[p for p in points if len(deg(p))>=4]
    assert not four, (filename,four)
    component_pin_branches=[]
    for c in read(pinfile)["components"]:
        for p in c["pins"]:
            q=pt(p["x"],p["y"])
            if len(deg(q))>1:component_pin_branches.append([c["reference"],p["number"],q])
    for c in g["components"]:
        if c["reference"].startswith("#") and len(deg(pt(c["x"],c["y"])))>1:component_pin_branches.append([c["reference"],"1"])
    assert not component_pin_branches, (filename,component_pin_branches)
    assert all(l["net"] not in {"GND","+3V3"} for l in g["labels"])
    geometry[filename]={"wire_segments":len(wires),"four_way_intersections":four,"pin_anchors_at_branches":component_pin_branches}
erc=read("erc.json")
violations=[v for s in erc["sheets"] for v in s["violations"]]
counts=collections.Counter(v["severity"] for v in violations)
types=collections.Counter(v["type"] for v in violations)
assert counts == {"error":18,"warning":3}, counts
assert types == {"pin_not_connected":16,"power_pin_not_driven":2,"isolated_pin_label":3},types
assert "four_way_junction" in {c["key"] for c in erc["ignored_checks"]}
for table in ["sym-lib-table","fp-lib-table"]:
    text=(PROJECT/table).read_text()
    assert "${KIPRJMOD}/../../libraries/" in text and "/Users/" not in text
result={"status":"BOUNDED_ENDPOINT_AND_METADATA_CHECKS_PASS; INTEGRATION_AND_POLICY_GATES_OPEN","physical_parts":27,"selected_parts":22,"unselected_placeholders":unselected,"preserved_endpoint_sets":17,"new_interface_endpoint_sets":3,"unfinished_mcu_pins":sorted(unfinished),"endpoint_sets":new,"erc_counts":dict(counts),"erc_types":dict(types),"geometry":geometry,"netclass_members":20,"mcu_pinmap":"STM32G0B1KET6N / stock STM32G0B1KETxN; pin20 electrically VDDIO2, generically labeled VDD by stock symbol","policy_blocks":["S03 native severity persistence API unavailable; default ignored corroborated by ERC report","S11 custom field visibility/font/position setters unavailable","5 unselected placeholders","S08 reused TCAN/ECS custom review marker approval unresolved","S04 printed root/child pagination unresolved"],"source_sha256":{str(p.relative_to(PROJECT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PROJECT.iterdir()) if p.name in {"controller_rev_b.kicad_sch","can_interfaces.kicad_sch","controller_rev_b.kicad_pro","sym-lib-table","fp-lib-table"}}}
(HERE/"verified.json").write_text(json.dumps(result,indent=2)+"\n")
(HERE/"fields_readback.json").write_text(json.dumps(field_readback,indent=2)+"\n")
with (HERE/"endpoint_sets.csv").open("w") as f:
    writer=csv.writer(f, lineterminator="\n");writer.writerow(["Net","Endpoints"])
    for n,e in new.items():writer.writerow([n,"; ".join(e)])
print(json.dumps({k:result[k] for k in ["status","physical_parts","preserved_endpoint_sets","new_interface_endpoint_sets","erc_counts","erc_types","geometry"]},indent=2))

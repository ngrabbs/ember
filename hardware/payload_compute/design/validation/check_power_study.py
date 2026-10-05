"""Verify exported connectivity/geometry and saved Konnect library/live queries."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

base = Path(__file__).resolve().parent / "payload_power_acceptance"
text = (base / "payload_power_acceptance-circuit.net").read_text()
for ref, value in {"R1": "10k / 0.1%", "R2": "1.91k / 0.1%"}.items():
    exported_value = re.search(r'\(ref "' + ref + r'"\)\s*\(value "([^"]+)"\)', text)
    assert exported_value and exported_value[1] == value, f"Incorrect exported feedback value: {ref}"
nets = {}
for block in text.split("\n\t\t(net\n")[1:]:
    name = re.search(r'\(name "([^"]+)"\)', block)[1]
    nets[name] = set(re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', block))
expected = {
    "+3V3": {("R5", "1")},
    "+5V": {(f"C{n}", "1") for n in range(5, 9)} | {("L1", "2"), ("R1", "1")},
    "/MAIN_EN": {("U1", "9"), ("R4", "1")},
    "/MAIN_RT": {("U1", "6"), ("R3", "1")},
    "/PG_MAIN": {("U1", "5"), ("R5", "2")},
    "/VIN_SELECTED": {("U1", str(n)) for n in [10, 11, 12]} |
                     {(f"C{n}", "1") for n in [1, 2, 3]},
    "GND": {(f"C{n}", "2") for n in [1, 2, 3, 5, 6, 7, 8]} |
           {("U1", "13"), ("R4", "2"), ("NT1", "2")},
    "GNDA": {("U1", "8"), ("R2", "2"), ("R3", "2"), ("NT1", "1")},
    "Net-(C4-Pad2)": {("C4", "2"), ("L1", "1")} |
                     {("U1", str(n)) for n in [1, 2, 3]},
    "Net-(U1-BOOT)": {("C4", "1"), ("U1", "4")},
    "Net-(U1-FB)": {("R1", "2"), ("R2", "1"), ("U1", "7")},
}
assert nets == expected, f"Exported topology differs: {nets}"

root = ET.parse(base / "payload_power_acceptance-readback.xml").getroot()
ns = {"i": "http://webstds.ipc.org/2581"}
shapes = {e.attrib["id"]: e[0].attrib for e in root.findall(".//i:EntryStandard", ns)}
pins = root.find(".//i:Package", ns).findall("i:Pin", ns)
electrical = [p for p in pins if p.attrib["electricalType"] == "ELECTRICAL"]
assert len(pins) == 15 and len(electrical) == 13
assert {p.attrib["number"] for p in electrical} == {str(n) for n in range(1, 14)}
for p in pins:
    loc = p.find("i:Location", ns).attrib
    shape = shapes[p.find("i:StandardPrimitiveRef", ns).attrib["id"]]
    number = p.attrib["number"]
    if number.isdecimal():
        n = int(number)
        x = -1.39 if n <= 6 else 1.39
        y = -1.25 + (n - 1) * 0.5 if n <= 6 else 1.25 - (n - 7) * 0.5
        width, height = 0.62, 0.25
        if n == 13:
            x, y, width, height = 0, 0, 1.3, 2.5
        assert abs(float(loc["x"]) - x) < 1e-6
        assert abs(-float(loc["y"]) - y) < 1e-6, "IPC Y-up conversion mismatch"
    else:
        assert p.attrib["electricalType"] == "UNDEFINED"
        width, height = 1.21, 1.10
        assert float(loc["x"]) == 0 and abs(float(loc["y"])) == 0.65
    assert abs(float(shape["width"]) - width) < 1e-6
    assert abs(float(shape["height"]) - height) < 1e-6
    assert abs(float(shape["radius"]) - 0.05) < 1e-6
layer_sets = {frozenset(p.attrib["layerRef"] for p in s.findall("i:PadstackPadDef", ns))
              for s in root.findall(".//i:PadStackDef", ns)}
assert layer_sets == {frozenset(["F.Cu", "F.Mask", "F.Paste"]),
                      frozenset(["F.Cu", "F.Mask"]), frozenset(["F.Paste"])}
component = root.find(".//i:Component", ns)
assert component.attrib["refDes"] == "U1" and component.attrib["layerRef"] == "F.Cu"

symbol = json.loads((base / "payload_power_acceptance-symbol-query.json").read_text())
footprint = json.loads((base / "payload_power_acceptance-footprint-query.json").read_text())
live = json.loads((base / "payload_power_acceptance-live-pad-query.json").read_text())
offline = json.loads((base / "payload_power_acceptance-offline-pad-query.json").read_text())
instance = json.loads((base / "payload_power_acceptance-instance-query.json").read_text())
assert symbol["properties"]["Footprint"] == "EMBER_Payload:TI_DRR0012_WSON_3x3mm_EP1.3x2.5mm"
assert instance["footprint"] == symbol["properties"]["Footprint"]
assert instance["lib_id"] == symbol["lib_id"] and instance["reference"] == "U1"
pin_map = {"1": ("SW", "power_out"), "2": ("SW", "passive"), "3": ("SW", "passive"),
           "4": ("BOOT", "passive"), "5": ("PG", "open_collector"), "6": ("RT", "passive"),
           "7": ("FB", "input"), "8": ("AGND", "power_in"), "9": ("EN", "input"),
           "10": ("VIN", "power_in"), "11": ("VIN", "power_in"), "12": ("VIN", "power_in"),
           "13": ("PGND", "power_in")}
assert symbol["pin_count"] == len(symbol["pins"]) == 13
assert {p["number"]: (p["name"], p["type"]) for p in symbol["pins"]} == pin_map
placed_pins = json.loads((base / "payload_power_acceptance-pin-query.json").read_text())
assert placed_pins["reference"] == "U1" and len(placed_pins["pins"]) == 13
assert {p["number"]: p["name"] for p in placed_pins["pins"]} == {n: data[0] for n, data in pin_map.items()}
for p in placed_pins["pins"]:
    library_pin = next(q for q in symbol["pins"] if q["number"] == p["number"])
    assert abs(p["x"] - instance["x"] - library_pin["x"]) < 1e-6
    assert abs(p["y"] - instance["y"] + library_pin["y"]) < 1e-6
assert footprint["pad_count"] == len(footprint["pads"]) == 15
assert footprint["coordinate_system"] == "footprint_local_mm_y_down"
numbered = {p["number"]: p for p in footprint["pads"] if p["number"]}
assert set(numbered) == set(pin_map)
paste = [p for p in footprint["pads"] if not p["number"]]
assert len(paste) == 2 and {p["y"] for p in paste} == {-0.65, 0.65}
for p in footprint["pads"]:
    if p["number"]:
        n = int(p["number"])
        x = -1.39 if n <= 6 else 1.39
        y = -1.25 + (n - 1) * 0.5 if n <= 6 else 1.25 - (n - 7) * 0.5
        width, height = 0.62, 0.25
        layers = {"F.Cu", "F.Mask", "F.Paste"}
        if n == 13:
            x, y, width, height, layers = 0, 0, 1.3, 2.5, {"F.Cu", "F.Mask"}
        assert abs(p["x"] - x) < 1e-6 and abs(p["y"] - y) < 1e-6
    else:
        width, height, layers = 1.21, 1.10, {"F.Paste"}
        assert p["x"] == 0
    assert abs(p["width"] - width) < 1e-6 and abs(p["height"] - height) < 1e-6
    assert p["type"] == "smd" and p["shape"] == "roundrect" and p["rotation"] == 0
    assert abs(min(width, height) * p["roundrect_rratio"] - 0.05) < 1e-6
    assert set(p["layers"]) == layers
assert live["source"] == "ipc" and live["reference"] == "U1"
assert live["pad_count"] == len(live["pads"]) == 15
for p in live["pads"]:
    candidates = [q for q in footprint["pads"] if q["number"] == p["number"] and
                  abs(p["x"] - 100 - q["x"]) < 1e-6 and abs(p["y"] - 100 - q["y"]) < 1e-6 and
                  set(p["layers"]) == set(q["layers"])]
    assert len(candidates) == 1, f"Live pad differs from library: {p}"
assert len({(p["number"], p["x"], p["y"]) for p in live["pads"]}) == 15
assert offline["source"] == "file" and offline["pad_count"] == 15
normalize = lambda pads: sorted((p["number"], p["x"], p["y"], tuple(sorted(p["layers"])), p["net"]) for p in pads)
assert normalize(offline["pads"]) == normalize(live["pads"])
print(json.dumps({"exported_nets_checked": len(nets), "electrical_pads_checked": 13,
                  "paste_only_features_checked": 2,
                  "library_default_footprint_checked": True, "live_pad_query_checked": True,
                  "physical_acceptance": "PASS for LMR51460 library; full power design pending"}, indent=2))

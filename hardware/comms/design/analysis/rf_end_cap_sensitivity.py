"""Sweep verified FH end-cap tolerance with both end capacitors tracking.

This is a sensitivity slice, not independent component corners or yield.
Run using the same NumPy-equipped Python as rf_filter_vendor.py.
"""
import json
import pathlib
import subprocess
import sys

base = pathlib.Path(__file__).resolve().parent
out = pathlib.Path(sys.argv[1])
rows = []
for shunt in (9.1, 8.2, 7.5):
    for end_cap in (3.65, 3.9, 4.15):
        dest = out / f"{shunt}-{end_cap}"
        settings = dict(shunt_pF=shunt, io_pF=end_cap, frequencies_MHz=[435, 437])
        subprocess.run([sys.executable, str(base / "rf_filter_vendor.py"),
                        str(base / "rf_filter_after.json"), str(dest),
                        json.dumps(settings)], check=True)
        rows.append(json.loads((dest / "results.json").read_text()))
(out / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
for shunt in (9.1, 8.2, 7.5):
    subset = [r for r in rows if r["settings"]["shunt_pF"] == shunt]
    loss = [-r["filters"]["TX_output"]["437MHz"][0] for r in subset]
    print(f"TX output, {shunt} pF shunts: {min(loss):.3f}–{max(loss):.3f} dB loss at 437 MHz")

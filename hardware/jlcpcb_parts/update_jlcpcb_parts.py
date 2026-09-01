#!/usr/bin/env python3
"""
Download and clean the JLCPCB basic+preferred parts list.

Source: https://github.com/CDFER/jlcpcb-parts-database
(auto-updated daily from JLCPCB/LCSC)

Usage:
    # Pipe from curl:
    curl -sL "https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv" \
        | python3 update_jlcpcb_parts.py

    # Or from a local file:
    python3 update_jlcpcb_parts.py < raw_download.csv
"""

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUT_PATH = SCRIPT_DIR / "jlcpcb_basic_preferred_parts.csv"


def main():
    reader = csv.DictReader(sys.stdin)
    rows = list(reader)

    clean = []
    for r in rows:
        is_basic = r.get("basic") == "1"
        is_preferred = r.get("preferred") == "1"
        if not (is_basic or is_preferred):
            continue

        cat1 = cat2 = ""
        try:
            extra = json.loads(r["extra"]) if r.get("extra") else {}
            if extra and "category" in extra:
                cat1 = extra["category"].get("name1", "")
                cat2 = extra["category"].get("name2", "")
        except (json.JSONDecodeError, KeyError):
            pass

        unit_price = ""
        try:
            prices = json.loads(r["price"]) if r.get("price") else []
            if prices:
                unit_price = f"${prices[0]['price']:.4f}"
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        clean.append(
            {
                "LCSC": f"C{r['lcsc']}",
                "Type": "Basic" if is_basic else "Preferred",
                "MPN": r.get("mfr", ""),
                "Manufacturer": r.get("manufacturer", ""),
                "Category": cat1,
                "Subcategory": cat2,
                "Package": r.get("package", ""),
                "Description": (r.get("description") or "")[:120],
                "Stock": r.get("stock", ""),
                "Unit_Price": unit_price,
                "Process": r.get("Assembly Process", ""),
                "Min_Qty": r.get("Min Order Qty", ""),
            }
        )

    clean.sort(
        key=lambda x: (
            0 if x["Type"] == "Basic" else 1,
            x["Category"],
            x["Subcategory"],
        )
    )

    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=clean[0].keys())
        writer.writeheader()
        writer.writerows(clean)

    basic_n = sum(1 for r in clean if r["Type"] == "Basic")
    print(f"Wrote {len(clean)} parts ({basic_n} basic, {len(clean)-basic_n} preferred)")
    print(f"  -> {OUT_PATH}")


if __name__ == "__main__":
    main()

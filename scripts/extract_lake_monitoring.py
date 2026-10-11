"""Extract DO, BOD (3 days, 27 C) and pH per month from the pack's lake-monitoring PDF into a tidy CSV.

    pip install pymupdf
    python scripts/extract_lake_monitoring.py path/to/Upper_Lower_Lake_monthly_2025-26_from_xgn.pdf

Writes data/lake_monitoring_2025_26.csv. Every parsed row is checked against the PDF's own Average / Max /
Min columns, and the script stops if any station does not agree, so a mis-read value cannot slip through.
The PDF is the one in the Track 2 pack (resources/); nothing is fetched from any government site.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "lake_monitoring_2025_26.csv"
PAIRS = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]          # each station's table runs over two PDF pages
WANTED = {"dissolved oxygen": "do", "b.o.d (3 days 27oc)": "bod3", "ph": "ph"}
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
NUM = re.compile(r"^\d+(?:\.\d+)?$")


def station_of(page) -> tuple[str, str]:
    """Station name and lake from the page's 'Natural Water Resource : ...' line."""
    text = re.search(r"Natural Water Resource\s*:\s*([^\n]+)", page.get_text())
    name = re.sub(r"\s*\(Sta\. code.*|\s*XGN ID.*|\s*bhopal\s*$", "", text.group(1), flags=re.I).strip(" ,.")
    return name, ("Lower Lake" if "lower" in name.lower() else "Upper Lake")


def main(pdf: str) -> None:
    doc = pymupdf.open(pdf)
    out, report = [], []
    for first, second in PAIRS:
        name, lake = station_of(doc[first])
        header = None
        rows = {}
        for pn in (first, second):
            tables = doc[pn].find_tables().tables
            if not tables:
                continue
            for r in tables[0].extract():
                cells = [(c or "").replace("\n", " ").strip() for c in r]
                if len(cells) < 18:
                    continue
                if cells[1].lower() == "par":
                    header = cells[3:15]
                key = WANTED.get(cells[1].lower())
                if key:
                    rows[key] = {"months": cells[3:15], "avg": cells[15], "max": cells[16], "min": cells[17], "page": pn + 1}
        assert header and len(rows) == 3, f"could not read {name}: found {sorted(rows)}"
        for key, row in rows.items():
            nums = [float(v) for v in row["months"] if NUM.match(v)]
            avg = float(row["avg"]) if NUM.match(row["avg"]) else None
            ok = bool(nums) and avg is not None and abs(sum(nums) / len(nums) - avg) <= 0.02 \
                and abs(max(nums) - float(row["max"])) <= 0.001 and abs(min(nums) - float(row["min"])) <= 0.001
            report.append((name, key, len(nums), round(sum(nums) / len(nums), 2) if nums else None, avg, ok))
            for i, v in enumerate(row["months"]):
                date = re.search(r"\((.*)\)", header[i].replace(" ", "")) if header[i] else None
                out.append({"station": name, "lake": lake, "month": MONTHS[i], "sample_date_as_printed": date.group(1) if date else "",
                            "parameter": key, "value": v if NUM.match(v) else "", "value_as_printed": v, "source_page": row["page"]})
    bad = [r for r in report if not r[-1]]
    for r in report:
        print(f"{'OK ' if r[-1] else 'BAD'} {r[0][:58]:58} {r[1]:5} months={r[2]:2} mean(parsed)={r[3]} printed_avg={r[4]}")
    if bad:
        sys.exit(f"{len(bad)} row(s) disagree with the PDF's own Average/Max/Min: not writing the CSV")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(out)} rows)")


if __name__ == "__main__":
    main(sys.argv[1])

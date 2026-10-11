"""Monthly lake monitoring, April 2025 to March 2026: the newest measurements in the Track 2 pack.

These are lake stations (mostly water-supply intakes), not the ghats, and sampled monthly rather than around
the festivals, so they are shown as context beside a ghat's own readings and never change its score.
BOD here is the 3-day, 27 C test, not the 5-day, 20 C test the Class B limit is defined for, so it is not
compared with that limit. Extracted by ``scripts/extract_lake_monitoring.py`` and checked against the PDF's own totals.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from utils.risk_engine import DO_MIN, PH_MAX, PH_MIN

LAKES_PATH = Path(__file__).resolve().parent.parent / "data" / "lake_monitoring_2025_26.csv"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
GENERIC = {"ghat", "kund", "lake", "dam", "park", "talab", "near", "bhopal"}


def _clean_name(name: str) -> str:
    """'UPPER LAKE AT BHOPAL NEAR INTAKE POINT KAMLA PARK, M.P' -> a readable title."""
    name = re.sub(r",?\s*M\.P\.?$", "", name.strip())
    return name.title() if name.isupper() else name


def lake_for_water_body(water_body: str) -> str | None:
    """Which monitored lake a ghat's water body belongs to, or None (Hathaikheda dam, Shahpura Lake, kunds ...)."""
    w = (water_body or "").lower()
    return "Upper Lake" if w.startswith("upper") else "Lower Lake" if w.startswith("lower") else None


def nearest_station(ghat: str, stations: list[dict]) -> str | None:
    """The station whose name shares a distinctive word with the ghat's name (e.g. Bairagarh, Kamla)."""
    words = {w for w in re.findall(r"[a-z]{4,}", ghat.lower()) if w not in GENERIC}
    for s in stations:
        if words & set(re.findall(r"[a-z]{4,}", s["name"].lower())):
            return s["id"]
    return None


@lru_cache(maxsize=4)
def load_lakes(path: Path = LAKES_PATH) -> dict:
    """``{"months": [...], "stations": [...]}`` with the monthly series and a few headline numbers per station. Never raises."""
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return {"months": MONTHS, "stations": []}
    stations = []
    for i, ((name, lake), g) in enumerate(df.groupby(["station", "lake"], sort=False)):
        series, dates = {}, {}
        for param, p in g.groupby("parameter"):
            p = p.set_index("month").reindex(MONTHS)
            series[param] = [float(v) if v != "" and v == v else None for v in p["value"].fillna("")]
            dates = {m: d for m, d in zip(p.index, p["sample_date_as_printed"].fillna(""))} or dates
        do, ph, bod = series.get("do", []), series.get("ph", []), series.get("bod3", [])
        have = lambda xs: [x for x in xs if x is not None]
        latest = next((m for m in reversed(range(12)) if do[m] is not None), None)
        stations.append({
            "id": f"s{i + 1}", "name": _clean_name(name), "lake": lake, "series": series, "dates": dates,
            "page": int(g["source_page"].iloc[0]), "months_measured": len(have(do)),
            "do_min": min(have(do)) if have(do) else None, "do_max": max(have(do)) if have(do) else None,
            "do_months_below": sum(1 for x in have(do) if x < DO_MIN),
            "ph_min": min(have(ph)) if have(ph) else None, "ph_max": max(have(ph)) if have(ph) else None,
            "ph_months_outside": sum(1 for x in have(ph) if not PH_MIN <= x <= PH_MAX),
            "bod3_max": max(have(bod)) if have(bod) else None,
            "latest_month": MONTHS[latest] if latest is not None else None,
            "latest": {k: (v[latest] if latest is not None else None) for k, v in series.items()},
        })
    return {"months": MONTHS, "stations": stations}

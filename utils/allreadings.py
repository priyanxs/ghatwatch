"""Every reading in the dataset (all 13 parameters), for the "All readings" explorer and the CSV download.

The ghat pages score only DO, BOD and pH, the parameters with a CPCB Class B limit. This module exposes the rest as well, exactly as the
reports print them, with the page each came from. For the three scored parameters the Class B result is added; the others are
shown as having no Class B limit, never as clean. Falls back to the labelled demo data if the CSV is missing or unusable.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from utils.data_loader import DATA_PATH, PHASE_MAP, generate_mock_data, parse_reading
from utils.risk_engine import check_bod, check_do, check_ph
from utils.sources import report_for_year

REQUIRED = ["year", "festival", "site", "phase", "parameter"]
SCORED = {"dissolved oxygen": check_do, "bod": check_bod, "ph": check_ph}
PHASE_LABEL = {"pre": "Pre-Visarjan", "during": "During", "after": "Post-Visarjan"}
COLUMNS = ["ghat", "year", "festival", "period", "phase", "parameter", "value", "unit", "flag", "as_printed", "page", "result", "report", "report_url"]


@lru_cache(maxsize=1)
def load_all_readings() -> tuple[pd.DataFrame, bool]:
    """One row per reading, with the Class B result where one applies. Returns ``(frame, is_demo)``."""
    is_demo = False
    try:
        raw = pd.read_csv(DATA_PATH, dtype=str, keep_default_na=False)
        if any(c not in raw.columns for c in REQUIRED) or raw.empty:
            raise ValueError("unusable file")
    except Exception:
        raw, is_demo = generate_mock_data(), True
    for col in ("value", "flag", "value_as_printed", "source_page", "unit_assumed"):
        if col not in raw.columns:
            raw[col] = ""
    rows = []
    for r in raw.itertuples(index=False):
        phase = PHASE_LABEL.get(str(r.phase).strip().lower())
        if phase is None:
            continue
        printed = (r.value or r.value_as_printed or r.flag or "").strip()
        check = SCORED.get(str(r.parameter).strip().lower())
        result = ""
        if check:
            value, qual = parse_reading(printed)
            result = check(value, qual)
        report = report_for_year(int(r.year)) if str(r.year).isdigit() else None
        rows.append([r.site.strip(), int(r.year), r.festival.strip().title(), f"{r.year} {r.festival.strip().title()}", phase, r.parameter.strip(),
                     (r.value or "").strip(), (r.unit_assumed or "").strip(), (r.flag or "").strip(), printed, (r.source_page or "").strip(), result,
                     "" if is_demo or not report else report["title"], "" if is_demo or not report else report["url"]])
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df.sort_values(["ghat", "year", "festival", "parameter", "phase"], kind="stable").reset_index(drop=True), is_demo

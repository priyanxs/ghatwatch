"""Load and clean historical Bhopal water-quality records.

Expected CSV (``data/bhopal_water_quality.csv``), one row per ghat / year / phase:

    ghat, year, phase, do_mg_l, bod_mg_l, source, page [, source_url]

``do_mg_l`` and ``bod_mg_l`` may hold messy lab strings such as ``"<2"`` (below detection
limit), ``"BDL"``, ``"NA"`` or ``""``. Nothing here decides whether water is clean; the
loader only normalises values and keeps the censoring qualifier so that the risk engine
can treat an unreadable or censored value conservatively.

If the CSV is missing or unusable, a clearly labelled mock dataset is generated so the
dashboard still runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from utils.sources import DEMO_LINKS, report_for_year

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "bhopal_water_quality.csv"

PRE, POST = "Pre-Visarjan", "Post-Visarjan"
PHASES = (PRE, POST)

# Names used by the mock generator (illustrative; real names come from the CSV).
MOCK_GHATS = (
    "Prempura Ghat",
    "Khatlapura Ghat",
    "Bhadbhada Ghat",
    "Lalghati Ghat",
    "Motia Talab Ghat",
    "Munshi Hussain Khan Talab Ghat",
    "Shahpura Lake Ghat",
)

NO_RECORD = "(no record)"

# Tokens meaning "nothing usable was recorded". A bare "BDL" is in this group on purpose:
# without the numeric detection limit we cannot prove compliance either way.
_MISSING = {"", "na", "n/a", "nan", "none", "null", "-", "--", "nm", "nt",
            "not measured", "not tested", "bdl", "nd", "<dl", "below detection limit"}
_NUMBER = re.compile(r"^([<>]?)\s*(-?\d+(?:\.\d+)?)$")

COLUMN_ALIASES = {
    "do": "do_mg_l", "dissolved_oxygen": "do_mg_l", "do_mg/l": "do_mg_l",
    "bod": "bod_mg_l", "bod_mg/l": "bod_mg_l",
    "station": "ghat", "location": "ghat",
    "pdf_page": "page", "page_no": "page", "report": "source",
    "url": "source_url", "link": "source_url", "report_url": "source_url",
}
REQUIRED = ["ghat", "year", "phase", "do_mg_l", "bod_mg_l"]


@dataclass
class LoadResult:
    """Cleaned data plus human-readable notes about anything that was skipped."""
    df: pd.DataFrame
    is_mock: bool
    notes: list[str] = field(default_factory=list)


def parse_reading(raw) -> tuple[float, str]:
    """Parse one lab value into ``(number, qualifier)``.

    Qualifier is ``""`` for an exact value, ``"<"`` / ``">"`` for a censored one
    (e.g. ``"<2"`` -> ``(2.0, "<")``). Anything unreadable or empty -> ``(nan, "")``.
    """
    try:
        if raw is None or (isinstance(raw, float) and np.isnan(raw)):
            return np.nan, ""
        text = str(raw).strip().lower()
        if text in _MISSING:
            return np.nan, ""
        text = text.replace("mg/l", "").replace("<=", "<").replace(">=", ">")
        text = text.replace("≤", "<").replace("≥", ">").replace(",", ".").strip()
        match = _NUMBER.match(text)
        if not match:
            return np.nan, ""
        value = float(match.group(2))
        return (value, match.group(1)) if value >= 0 else (np.nan, "")
    except (ValueError, TypeError):
        return np.nan, ""


def _normalise_phase(raw) -> str | None:
    text = str(raw).strip().lower()
    if "pre" in text or "before" in text:
        return PRE
    if "post" in text or "after" in text:
        return POST
    return None


def _clean(raw: pd.DataFrame, notes: list[str]) -> pd.DataFrame:
    """Normalise a raw CSV frame into the schema the rest of the app expects."""
    df = raw.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing_cols)}")

    for optional in ("source", "page", "source_url"):
        if optional not in df.columns:
            df[optional] = "Not recorded"
    df["source"] = df["source"].astype(str).str.strip().replace("", "Not recorded")
    df["page"] = df["page"].astype(str).str.strip().replace("", "Not recorded")
    # Only real web links are kept, so a bad cell can never become a script link on the page.
    df["source_url"] = df["source_url"].astype(str).str.strip()
    df.loc[~df["source_url"].str.lower().str.match(r"^https?://\S+$"), "source_url"] = ""

    df["ghat"] = df["ghat"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["phase"] = df["phase"].map(_normalise_phase)

    bad = df["year"].isna() | df["phase"].isna() | (df["ghat"] == "")
    if bad.any():
        notes.append(f"Skipped {int(bad.sum())} row(s) with an unreadable ghat, year or phase.")
        df = df[~bad]
    df["year"] = df["year"].astype(int)

    dupes = df.duplicated(["ghat", "year", "phase"], keep="first")
    if dupes.any():
        notes.append(f"Ignored {int(dupes.sum())} duplicate ghat/year/phase row(s) (kept the first).")
        df = df[~dupes]

    df["do_raw"] = df["do_mg_l"].astype(str).str.strip()
    df["bod_raw"] = df["bod_mg_l"].astype(str).str.strip()
    for prefix in ("do", "bod"):
        parsed = df[f"{prefix}_raw"].map(parse_reading)
        df[f"{prefix}_value"] = parsed.map(lambda p: p[0])
        df[f"{prefix}_qual"] = parsed.map(lambda p: p[1])

    unreadable = ((df["do_value"].isna() & ~df["do_raw"].str.lower().isin(_MISSING))
                  | (df["bod_value"].isna() & ~df["bod_raw"].str.lower().isin(_MISSING)))
    if unreadable.any():
        notes.append(f"{int(unreadable.sum())} row(s) had an unreadable DO/BOD value; "
                     "treated as missing, never as clean.")

    return df[["ghat", "year", "phase", "do_raw", "bod_raw", "do_value", "do_qual",
               "bod_value", "bod_qual", "source", "page", "source_url"]]


def _complete_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Add an explicit empty row for every ghat/year/phase that has no record at all.

    A year with no report for a ghat is a data gap, so it must show up as one.
    """
    full = pd.MultiIndex.from_product(
        [sorted(df["ghat"].unique()), range(df["year"].min(), df["year"].max() + 1), PHASES],
        names=["ghat", "year", "phase"])
    out = df.set_index(["ghat", "year", "phase"]).reindex(full).reset_index()
    absent = out["source"].isna()
    out.loc[absent, ["do_raw", "bod_raw"]] = NO_RECORD
    out.loc[absent, ["source", "page"]] = NO_RECORD
    out["source_url"] = out["source_url"].fillna("")
    for prefix in ("do", "bod"):
        out[f"{prefix}_qual"] = out[f"{prefix}_qual"].fillna("")
    return out


def link_known_reports(df: pd.DataFrame) -> pd.DataFrame:
    """For real readings, fill a missing source link (and name) from the year's published report."""
    df = df.copy()
    for i, row in df.iterrows():
        report = report_for_year(row["year"])
        if report is None:
            continue
        if not row["source_url"]:
            df.at[i, "source_url"] = report["url"]
        if row["source"] == "Not recorded":
            df.at[i, "source"] = report["title"]
    return df


def generate_mock_data(seed: int = 7) -> pd.DataFrame:
    """Build illustrative data for the 7 ghats (2019-2024). NOT real measurements.

    Includes the messy cases the loader must survive: ``<2`` / ``BDL`` / ``NA`` / blanks,
    and one ghat (Shahpura) with whole years missing.
    """
    rng = np.random.default_rng(seed)
    # name: (baseline DO, baseline BOD, post-Visarjan DO drop, post-Visarjan BOD rise)
    profile = {
        "Prempura Ghat": (5.6, 2.6, 1.4, 1.6),
        "Khatlapura Ghat": (4.8, 3.4, 1.8, 2.2),
        "Bhadbhada Ghat": (6.4, 2.0, 0.8, 0.9),
        "Lalghati Ghat": (5.9, 2.4, 1.2, 1.2),
        "Motia Talab Ghat": (4.3, 4.1, 1.6, 2.6),
        "Munshi Hussain Khan Talab Ghat": (6.8, 1.7, 0.6, 0.7),
        "Shahpura Lake Ghat": (6.0, 2.3, 1.0, 1.0),
    }
    rows = []
    for ghat, (do0, bod0, do_drop, bod_rise) in profile.items():
        for year in range(2019, 2025):
            page_base = int(rng.integers(12, 60))
            for phase in PHASES:
                post = phase == POST
                do = do0 - (do_drop if post else 0) + rng.normal(0, 0.35)
                bod = bod0 + (bod_rise if post else 0) + rng.normal(0, 0.3)
                rows.append({
                    "ghat": ghat, "year": year, "phase": phase,
                    "do_mg_l": f"{max(do, 0.5):.1f}", "bod_mg_l": f"{max(bod, 0.6):.1f}",
                    "source": f"MOCK - Bhopal Lakes Monitoring Report {year}",
                    "page": str(page_base + (1 if post else 0)),
                    "source_url": DEMO_LINKS.get(year, ""),
                })
    df = pd.DataFrame(rows)

    # Messy strings and gaps, so the parser and the data-gap rule are exercised.
    def put(ghat, year, phase, column, value):
        df.loc[(df.ghat == ghat) & (df.year == year) & (df.phase == phase), column] = value

    put("Bhadbhada Ghat", 2021, PRE, "bod_mg_l", "<2")      # censored, provably within limit
    put("Munshi Hussain Khan Talab Ghat", 2020, PRE, "bod_mg_l", "BDL")  # no limit given
    put("Lalghati Ghat", 2022, POST, "do_mg_l", "NA")
    put("Prempura Ghat", 2023, PRE, "do_mg_l", "")
    for year in (2021, 2022, 2023):                          # Shahpura: heavy gaps
        for phase in PHASES:
            put("Shahpura Lake Ghat", year, phase, "do_mg_l", "NA")
            put("Shahpura Lake Ghat", year, phase, "bod_mg_l", "NA")
    df = df[~((df.ghat == "Shahpura Lake Ghat") & (df.year == 2020))]  # whole year absent
    return df


def load_data(path: Path = DATA_PATH) -> LoadResult:
    """Load the CSV, or fall back to mock data. Never raises."""
    notes: list[str] = []
    raw, is_mock = None, False
    try:
        if path.exists():
            raw = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            notes.append(f"{path.name} not found.")
    except Exception as exc:  # unreadable file, bad encoding, empty file ...
        notes.append(f"Could not read {path.name}: {exc}")

    cleaned = None
    if raw is not None:
        try:
            cleaned = _clean(raw, notes)
            if cleaned.empty:
                notes.append("CSV contained no usable rows.")
                cleaned = None
        except Exception as exc:
            notes.append(f"Could not parse {path.name}: {exc}")

    if cleaned is None:
        is_mock = True
        notes.append("Showing generated MOCK data for demonstration only.")
        cleaned = _clean(generate_mock_data(), notes=[])

    if not is_mock:  # demo numbers are not from the published reports, so they are never linked to them
        cleaned = link_known_reports(cleaned)
    return LoadResult(df=_complete_grid(cleaned), is_mock=is_mock, notes=notes)

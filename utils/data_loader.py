"""Load and clean the MPPCB immersion readings for Bhopal's ghats.

Input is the Track 2 long format, ``data/bhopal_ghats_2023_2025.csv``: one row per
site / year / festival / phase / parameter, with the value as printed, a ``flag`` explaining an empty value
(BDL, not sampled, * , **) and the report ``source_page``. It is turned into one row per ghat / period /
phase with DO, BOD and pH, where a *period* is a year and festival such as ``2025 Durga``.

Nothing here decides whether water is clean. Values are only normalised, and the qualifier is kept so
the risk engine can treat a missing, censored or unreadable value conservatively.

If the CSV is missing or unusable a clearly labelled mock dataset is generated, in the same long format,
so the dashboard still runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from utils.sources import DEMO_LINKS, report_for_year

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "bhopal_ghats_2023_2025.csv"

PRE, DURING, POST = "Pre-Visarjan", "During", "Post-Visarjan"
PHASES = (PRE, DURING, POST)
PHASE_MAP = {"pre": PRE, "during": DURING, "after": POST}
FESTIVAL_ORDER = {"ganesh": 1, "durga": 2}
PARAM_COLUMNS = {"dissolved oxygen": "do", "bod": "bod", "ph": "ph"}   # parameter name (lower case) -> short name

NO_RECORD = "(no record)"

# Tokens meaning "nothing usable was recorded". The guide's blank codes (_ - * **) and "not sampled" are
# missing, never clean.
_MISSING = {"", "na", "n/a", "nan", "none", "null", "-", "--", "_", "*", "**", "nm", "nt",
            "not measured", "not tested", "not sampled"}
# BDL / ND = below detection limit / not detected: "very low, not zero, not missing".
_BDL = {"bdl", "nd", "<dl", "below detection limit", "not detected"}
_NUMBER = re.compile(r"^([<>]?)\s*(-?\d+(?:\.\d+)?)$")

REQUIRED = ["year", "festival", "site", "phase", "parameter"]


@dataclass
class LoadResult:
    """Cleaned data plus human-readable notes about anything that was skipped."""
    df: pd.DataFrame
    is_mock: bool
    notes: list[str] = field(default_factory=list)


def parse_reading(raw) -> tuple[float, str]:
    """Parse one lab value into ``(number, qualifier)``.

    Qualifier is ``""`` for an exact value, ``"<"`` / ``">"`` for a censored one
    (e.g. ``"<2"`` -> ``(2.0, "<")``), and ``"BDL"`` (no number) for below-detection-limit / not-detected.
    Anything unreadable or empty -> ``(nan, "")``.
    """
    try:
        if raw is None or (isinstance(raw, float) and np.isnan(raw)):
            return np.nan, ""
        text = str(raw).strip().lower()
        if text in _MISSING:
            return np.nan, ""
        if text in _BDL:
            return np.nan, "BDL"
        text = text.replace("mg/l", "").replace("<=", "<").replace(">=", ">")
        text = text.replace("≤", "<").replace("≥", ">").replace(",", ".").strip()
        match = _NUMBER.match(text)
        if not match:
            return np.nan, ""
        value = float(match.group(2))
        return (value, match.group(1)) if value >= 0 else (np.nan, "")
    except (ValueError, TypeError):
        return np.nan, ""


def _cell(value: str, printed: str, flag: str) -> str:
    """The text of one reading: the number if there is one, otherwise exactly what the report printed."""
    value, printed, flag = (value or "").strip(), (printed or "").strip(), (flag or "").strip()
    return value or printed or flag


def _pivot_long(raw: pd.DataFrame, notes: list[str]) -> pd.DataFrame:
    """Long CSV -> one row per ghat / period / phase with raw text for DO, BOD and pH."""
    df = raw.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
    for optional in ("value", "flag", "value_as_printed", "source_page", "site_match_confidence", "water_body"):
        if optional not in df.columns:
            df[optional] = ""

    df["site"] = df["site"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["festival"] = df["festival"].astype(str).str.strip().str.title()
    df["phase"] = df["phase"].astype(str).str.strip().str.lower().map(PHASE_MAP)
    df["short"] = df["parameter"].astype(str).str.strip().str.lower().map(PARAM_COLUMNS)

    bad = df["year"].isna() | df["phase"].isna() | (df["site"] == "") | (df["festival"] == "")
    if bad.any():
        notes.append(f"Skipped {int(bad.sum())} row(s) with an unreadable site, year, festival or phase.")
        df = df[~bad]
    df = df[df["short"].notna()]
    df["year"] = df["year"].astype(int)
    df["text"] = [_cell(v, p, f) for v, p, f in zip(df["value"], df["value_as_printed"], df["flag"])]

    key = ["site", "year", "festival", "phase"]
    dupes = df.duplicated(key + ["short"], keep="first")
    if dupes.any():
        notes.append(f"Ignored {int(dupes.sum())} duplicate reading(s) (kept the first).")
        df = df[~dupes]

    wide = df.pivot(index=key, columns="short", values="text")
    for col in ("do", "bod", "ph"):
        if col not in wide.columns:
            wide[col] = ""
    wide = wide[["do", "bod", "ph"]].fillna("").add_suffix("_raw").reset_index()

    # Page, water body and match confidence describe a whole site / year / festival table.
    meta = (df.groupby(["site", "year", "festival"])
              .agg(page=("source_page", "first"), water_body=("water_body", "first"), confidence=("site_match_confidence", "first"))
              .reset_index())
    out = wide.merge(meta, on=["site", "year", "festival"], how="left").rename(columns={"site": "ghat"})
    out["page"] = out["page"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True).replace("", "Not recorded")
    out["source"], out["source_url"] = "Not recorded", ""
    return out


def _enrich(df: pd.DataFrame, notes: list[str]) -> pd.DataFrame:
    """Parse the raw text into numbers + qualifiers and add the period columns."""
    df = df.copy()
    for p in ("do", "bod", "ph"):
        parsed = df[f"{p}_raw"].map(parse_reading)
        df[f"{p}_value"] = parsed.map(lambda x: x[0])
        df[f"{p}_qual"] = parsed.map(lambda x: x[1])
    known = _MISSING | _BDL
    unreadable = pd.Series(False, index=df.index)
    for p in ("do", "bod", "ph"):
        unreadable |= df[f"{p}_value"].isna() & (df[f"{p}_qual"] == "") & ~df[f"{p}_raw"].str.lower().isin(known)
    if unreadable.any():
        notes.append(f"{int(unreadable.sum())} reading(s) were unreadable; treated as missing, never as clean.")
    df["festival_order"] = df["festival"].str.lower().map(FESTIVAL_ORDER).fillna(9).astype(int)
    df["period"] = df["year"].astype(str) + " " + df["festival"]
    df["p_order"] = df["year"] * 10 + df["festival_order"]
    return df


def _complete_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Add an explicit empty row for every ghat / period / phase with no record at all.

    A festival table that a report does not contain is a data gap, so it must show up as one.
    """
    periods = df[["period", "year", "festival", "festival_order", "p_order"]].drop_duplicates()
    ghats = sorted(df["ghat"].unique())
    full = pd.MultiIndex.from_product([ghats, sorted(periods["period"], key=lambda p: periods.set_index("period").loc[p, "p_order"]), PHASES],
                                      names=["ghat", "period", "phase"])
    keep = ["do_raw", "bod_raw", "ph_raw", "do_value", "do_qual", "bod_value", "bod_qual", "ph_value", "ph_qual",
            "page", "source", "source_url", "water_body", "confidence"]
    out = df.set_index(["ghat", "period", "phase"])[keep].reindex(full).reset_index()
    out = out.merge(periods, on="period", how="left")
    absent = out["source"].isna()
    out.loc[absent, ["do_raw", "bod_raw", "ph_raw"]] = NO_RECORD
    out.loc[absent, ["source", "page"]] = NO_RECORD
    for p in ("do", "bod", "ph"):
        out[f"{p}_qual"] = out[f"{p}_qual"].fillna("")
    for col in ("source_url", "water_body", "confidence"):
        out[col] = out[col].fillna("")
    # a ghat's water body and match confidence are the same in every period
    for col in ("water_body", "confidence"):
        out[col] = out.groupby("ghat")[col].transform(lambda s: next((x for x in s if x), ""))
    return out.sort_values(["ghat", "p_order", "phase"]).reset_index(drop=True)


def link_known_reports(df: pd.DataFrame) -> pd.DataFrame:
    """For real readings, fill the source name and link from the year's published report."""
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


# ---------------------------------------------------------------- mock data
MOCK_GHATS = ("Khatlapura ghat", "Prempura ghat", "Rani Kamlapati ghat / Kamla Park kund", "Hathaikheda dam / kund",
              "Shahpura lake ghat", "Bairagarh (Sant Hirdaram) kund", "Malikhedi kund")


def generate_mock_data(seed: int = 7) -> pd.DataFrame:
    """Illustrative readings in the same long format as the real file. NOT real measurements.

    Mimics the real quirks: BDL, not-sampled and star flags, and two kunds with no Durga 2025 table.
    """
    rng = np.random.default_rng(seed)
    # ghat: (DO before, BOD before, DO drop during, BOD rise during)
    profile = {"Khatlapura ghat": (4.8, 3.4, 1.8, 2.2), "Prempura ghat": (5.6, 2.6, 1.4, 1.6),
               "Rani Kamlapati ghat / Kamla Park kund": (4.3, 4.1, 1.6, 2.6), "Hathaikheda dam / kund": (6.4, 2.0, 0.8, 0.9),
               "Shahpura lake ghat": (6.0, 2.3, 1.0, 1.0), "Bairagarh (Sant Hirdaram) kund": (5.9, 2.9, 1.5, 1.4),
               "Malikhedi kund": (6.8, 1.7, 0.6, 0.7)}
    rows = []
    for ghat, (do0, bod0, do_drop, bod_rise) in profile.items():
        for year in (2023, 2024, 2025):
            for festival in ("Ganesh", "Durga"):
                if festival == "Durga" and year == 2025 and ghat in ("Bairagarh (Sant Hirdaram) kund", "Malikhedi kund"):
                    continue  # no table in the report
                page = str(int(rng.integers(12, 80)))
                for phase, k in (("pre", 0.0), ("during", 1.0), ("after", 0.4)):
                    vals = {"Dissolved oxygen": max(do0 - k * do_drop + rng.normal(0, .35), 0.5),
                            "BOD": max(bod0 + k * bod_rise + rng.normal(0, .3), 0.6),
                            "pH": 7.4 + 0.45 * (k == 1.0) + rng.normal(0, .25)}
                    for param, v in vals.items():
                        rows.append({"year": year, "festival": festival, "site": ghat, "water_body": "", "phase": phase,
                                     "parameter": param, "value": f"{v:.1f}" if param != "pH" else f"{v:.2f}", "flag": "",
                                     "value_as_printed": "", "site_match_confidence": "high", "source_page": page})
    df = pd.DataFrame(rows)

    def put(site, year, festival, phase, param, value="", flag="", printed=""):
        m = (df.site == site) & (df.year == year) & (df.festival == festival) & (df.phase == phase) & (df.parameter == param)
        df.loc[m, ["value", "flag", "value_as_printed"]] = [value, flag, printed]

    put("Hathaikheda dam / kund", 2024, "Ganesh", "pre", "BOD", flag="BDL", printed="BDL")
    put("Prempura ghat", 2023, "Durga", "pre", "BOD", flag="not sampled", printed="_")
    put("Prempura ghat", 2023, "Durga", "during", "BOD", flag="not sampled", printed="_")
    put("Prempura ghat", 2023, "Durga", "after", "BOD", flag="not sampled", printed="_")
    for phase in ("pre", "during", "after"):                      # Shahpura: a whole table missing values
        for param in ("Dissolved oxygen", "BOD"):
            put("Shahpura lake ghat", 2024, "Durga", phase, param, flag="not sampled", printed="")
    return df


def _mock_frame(notes: list[str]) -> pd.DataFrame:
    wide = _enrich(_pivot_long(generate_mock_data(), notes=[]), notes=[])
    wide["source"] = "MOCK - illustrative values, " + wide["period"]
    wide["source_url"] = wide["year"].map(DEMO_LINKS).fillna("")
    return wide


def load_data(path: Path = DATA_PATH) -> LoadResult:
    """Load the CSV, or fall back to mock data. Never raises."""
    notes: list[str] = []
    raw, cleaned, is_mock = None, None, False
    try:
        if path.exists():
            raw = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            notes.append(f"{path.name} not found.")
    except Exception as exc:  # unreadable file, bad encoding, empty file ...
        notes.append(f"Could not read {path.name}: {exc}")

    if raw is not None:
        try:
            cleaned = link_known_reports(_enrich(_pivot_long(raw, notes), notes))
            if cleaned.empty:
                notes.append("CSV contained no usable rows.")
                cleaned = None
        except Exception as exc:
            notes.append(f"Could not parse {path.name}: {exc}")
            cleaned = None

    if cleaned is None:
        is_mock = True
        notes.append("Showing generated MOCK data for demonstration only.")
        cleaned = _mock_frame(notes)
    return LoadResult(df=_complete_grid(cleaned), is_mock=is_mock, notes=notes)

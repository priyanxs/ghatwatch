"""CPCB Class B compliance checks and historical risk scoring for each ghat.

Class B is "outdoor bathing (organised)". It is the closest CPCB class to people and idols entering the
water at a ghat, so it is the yardstick used here. Limits applied:
    Dissolved Oxygen (DO) >= 5 mg/L      BOD <= 3 mg/L      pH 6.5 to 8.5
Other tests (COD, solids, metals ...) have no Class B limit, so they are not scored.

Core rule: missing or inconclusive data is NEVER treated as clean. Every reading ends up as exactly one
of PASS / BREACH / NO DATA, and NO DATA is penalised in the score.

The score is a transparent weighted sum, so an officer can see why a ghat ranks where it does. It
describes *historical* records only; it is not a live safety measurement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils.data_loader import DURING, POST, PRE

DO_MIN = 5.0     # mg/L, must be at least this
BOD_MAX = 3.0    # mg/L, must be at most this
PH_MIN, PH_MAX = 6.5, 8.5

PASS, BREACH, NO_DATA = "PASS", "BREACH", "NO DATA"
PARAMS = ("do", "bod", "ph")

# Score = 100 * (W_BREACH * breach rate + W_SEVERITY * severity + W_DETERIORATION * deterioration)
W_BREACH, W_SEVERITY, W_DETERIORATION = 0.60, 0.25, 0.15
GAP_WEIGHT = 0.5          # a NO DATA reading counts as this fraction of a breach
GAP_FLAG_SHARE = 0.25     # above this share of NO DATA, the ghat can't rank as Low
HIGH_AT, MEDIUM_AT = 45, 30   # cut-offs are a starting point to agree with BMC

DISCLAIMER_EN = "Priority ranking based on historical records, not a live real-time safety measurement."
DISCLAIMER_HI = "यह प्राथमिकता रैंकिंग ऐतिहासिक रिकॉर्ड पर आधारित है, लाइव वास्तविक-समय सुरक्षा माप पर नहीं।"

GHAT_HI = {
    "Bairagarh (Sant Hirdaram) kund": "बैरागढ़ (संत हिरदाराम) कुंड",
    "Khatlapura ghat": "खटलापुरा घाट",
    "Prempura ghat": "प्रेमपुरा घाट",
    "Rani Kamlapati ghat / Kamla Park kund": "रानी कमलापति घाट / कमला पार्क कुंड",
    "Hathaikheda dam / kund": "हथाईखेड़ा बांध / कुंड",
    "Malikhedi kund": "मालीखेड़ी कुंड",
    "Shahpura lake ghat": "शाहपुरा झील घाट",
}
LEVEL_HI = {"High": "उच्च", "Medium": "मध्यम", "Low": "निम्न"}


# ---------------------------------------------------------------- per-reading checks
def check_do(value: float, qual: str) -> str:
    """Status of one DO reading. A censored value only counts when it settles the question.

    BDL / ND ("very low") cannot be read as a DO result either way, so it stays NO DATA.
    """
    if pd.isna(value):
        return NO_DATA
    if qual == "<":                       # true value is below `value`
        return BREACH if value <= DO_MIN else NO_DATA
    if qual == ">":                       # true value is above `value`
        return PASS if value >= DO_MIN else NO_DATA
    return PASS if value >= DO_MIN else BREACH


def check_bod(value: float, qual: str) -> str:
    """Status of one BOD reading. ``"<2"`` is a pass; ``"<5"`` proves nothing.

    BDL / ND means very low organic load, so it is a pass (not zero, and not missing).
    """
    if qual == "BDL":
        return PASS
    if pd.isna(value):
        return NO_DATA
    if qual == "<":
        return PASS if value <= BOD_MAX else NO_DATA
    if qual == ">":
        return BREACH if value >= BOD_MAX else NO_DATA
    return PASS if value <= BOD_MAX else BREACH


def check_ph(value: float, qual: str) -> str:
    """pH must sit between 6.5 and 8.5. A censored pH proves nothing, so it is NO DATA."""
    if pd.isna(value) or qual:
        return NO_DATA
    return PASS if PH_MIN <= value <= PH_MAX else BREACH


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add a status and an exceedance (0..1, how far past the limit) column for DO, BOD and pH."""
    out = df.copy()
    out["do_status"] = [check_do(v, q) for v, q in zip(out["do_value"], out["do_qual"])]
    out["bod_status"] = [check_bod(v, q) for v, q in zip(out["bod_value"], out["bod_qual"])]
    out["ph_status"] = [check_ph(v, q) for v, q in zip(out["ph_value"], out["ph_qual"])]
    out["do_exceed"] = np.where(out["do_status"] == BREACH, ((DO_MIN - out["do_value"]) / DO_MIN).clip(0, 1), 0.0)
    out["bod_exceed"] = np.where(out["bod_status"] == BREACH, ((out["bod_value"] - BOD_MAX) / BOD_MAX).clip(0, 1), 0.0)
    off = np.where(out["ph_value"] < PH_MIN, PH_MIN - out["ph_value"], out["ph_value"] - PH_MAX)
    out["ph_exceed"] = np.where(out["ph_status"] == BREACH, (off / 2.0).clip(0, 1), 0.0)
    return out


def row_status(r) -> str:
    """One overall status for a ghat/period/phase: any breach wins, then any gap, otherwise pass."""
    pair = {r.do_status, r.bod_status, r.ph_status}
    return BREACH if BREACH in pair else NO_DATA if NO_DATA in pair else PASS


# ---------------------------------------------------------------- scoring
def _level(score: float) -> str:
    return "High" if score >= HIGH_AT else "Medium" if score >= MEDIUM_AT else "Low"


def _need(share: float, high: float, medium: float) -> str:
    return "High" if share >= high else "Medium" if share >= medium else "Low"


def _phase_change(g: pd.DataFrame) -> dict:
    """Average change in DO and BOD from before immersion to during it, and to one week after.

    Only periods where both phases have a number are compared. ``deterioration`` (0..1) measures the
    during-immersion hit: a fall in DO and a rise in BOD.
    """
    by = {ph: g[g.phase == ph].set_index("period") for ph in (PRE, DURING, POST)}
    out = {}
    for tag, later in (("during", DURING), ("after", POST)):
        for p in ("do", "bod"):
            d = (by[later][f"{p}_value"] - by[PRE][f"{p}_value"]).dropna()
            out[f"{tag}_{p}_change"] = float(d.mean()) if len(d) else np.nan
            out[f"_{tag}_{p}"] = d
    parts = []
    if len(out["_during_do"]):
        parts.append((-out["_during_do"]).clip(lower=0, upper=DO_MIN).mean() / DO_MIN)
    if len(out["_during_bod"]):
        parts.append(out["_during_bod"].clip(lower=0, upper=BOD_MAX).mean() / BOD_MAX)
    out["deterioration"] = float(np.mean(parts)) if parts else 0.0
    return {k: v for k, v in out.items() if not k.startswith("_")}


def summarise_ghat(g: pd.DataFrame) -> dict:
    """Score one ghat from its annotated rows (all periods and phases)."""
    g = g.copy()
    g["w"] = g["p_order"].rank(method="dense")      # recent periods weigh more: oldest = 1
    wsum = g["w"].sum() * len(PARAMS)

    def total(status):
        return int(sum((g[f"{p}_status"] == status).sum() for p in PARAMS))

    def weighted(status):
        return float(sum(g.loc[g[f"{p}_status"] == status, "w"].sum() for p in PARAMS))

    breach_rate = (weighted(BREACH) + GAP_WEIGHT * weighted(NO_DATA)) / wsum
    severity = float(sum(((g[f"{p}_exceed"]) * g["w"]).sum() for p in PARAMS) / wsum)
    change = _phase_change(g)

    readings, gaps = len(g) * len(PARAMS), total(NO_DATA)
    gap_share = gaps / readings
    score = 100 * (W_BREACH * breach_rate + W_SEVERITY * severity + W_DETERIORATION * change["deterioration"])
    floor_applied = gap_share > GAP_FLAG_SHARE and score < MEDIUM_AT
    if floor_applied:  # too little evidence to call this ghat low risk
        score = float(MEDIUM_AT)
    score = round(min(score, 100.0), 1)

    tested = {p: int((g[f"{p}_status"] != NO_DATA).sum()) for p in PARAMS}
    breaches = {p: int((g[f"{p}_status"] == BREACH).sum()) for p in PARAMS}
    share = {p: (breaches[p] / tested[p] if tested[p] else 0.0) for p in PARAMS}
    needs = {
        "aeration": _need(share["do"], 0.5, 0.2),                                   # low oxygen
        "cleaning": _need(max(share["bod"], 0.5 if change["deterioration"] >= 0.3 else 0.0), 0.5, 0.2),  # organic waste
        "testing": _need(gap_share, GAP_FLAG_SHARE, 0.10),                          # data gaps
    }
    return {
        "risk_score": score, "risk_level": _level(score), "floor_applied": floor_applied,
        **{f"{p}_breaches": breaches[p] for p in PARAMS}, **{f"{p}_tested": tested[p] for p in PARAMS},
        "breaches": total(BREACH), "readings": readings, "no_data": gaps, "gap_pct": round(100 * gap_share, 1),
        **change, "deterioration": round(change["deterioration"], 2),
        "breach_rate": round(breach_rate, 3), "severity": round(severity, 3),
        "need_aeration": needs["aeration"], "need_cleaning": needs["cleaning"], "need_testing": needs["testing"],
    }


def rank_ghats(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per ghat, highest risk first, with a 1-based ``rank`` column."""
    annotated = annotate(df)
    rows = [{"ghat": name, **summarise_ghat(g)} for name, g in annotated.groupby("ghat")]
    ranking = pd.DataFrame(rows).sort_values(["risk_score", "gap_pct"], ascending=False)
    ranking.insert(0, "rank", range(1, len(ranking) + 1))
    return ranking.reset_index(drop=True)


# ---------------------------------------------------------------- action brief
def build_brief(ghat: str, summary: dict) -> dict:
    """Bilingual findings and recommendations for one ghat, driven only by its summary.

    Returns ``{"en": {...}, "hi": {...}}``; each has ``headline``, ``findings``, ``actions``.
    """
    s = summary
    level = s["risk_level"]
    ghat_hi = GHAT_HI.get(ghat, ghat)
    en = {"headline": f"{ghat}: {level} priority (risk score {s['risk_score']:.0f}/100)", "findings": [], "actions": []}
    hi = {"headline": f"{ghat_hi}: {LEVEL_HI[level]} प्राथमिकता (जोखिम स्कोर {s['risk_score']:.0f}/100)", "findings": [], "actions": []}

    if s["do_breaches"]:
        en["findings"].append(f"{s['do_breaches']} of {s['do_tested']} tested DO readings were below the CPCB Class B minimum of {DO_MIN:g} mg/L.")
        hi["findings"].append(f"{s['do_tested']} में से {s['do_breaches']} घुलित ऑक्सीजन (DO) माप CPCB श्रेणी-B की न्यूनतम सीमा {DO_MIN:g} mg/L से कम रहे।")
    if s["bod_breaches"]:
        en["findings"].append(f"{s['bod_breaches']} of {s['bod_tested']} tested BOD readings exceeded the CPCB Class B maximum of {BOD_MAX:g} mg/L.")
        hi["findings"].append(f"{s['bod_tested']} में से {s['bod_breaches']} BOD माप CPCB श्रेणी-B की अधिकतम सीमा {BOD_MAX:g} mg/L से अधिक रहे।")
    if s["ph_breaches"]:
        en["findings"].append(f"{s['ph_breaches']} of {s['ph_tested']} tested pH readings were outside {PH_MIN:g} to {PH_MAX:g}.")
        hi["findings"].append(f"{s['ph_tested']} में से {s['ph_breaches']} pH माप {PH_MIN:g} से {PH_MAX:g} के बाहर रहे।")
    if not (s["do_tested"] or s["bod_tested"] or s["ph_tested"]):
        en["findings"].append("No usable DO, BOD or pH reading is on record, so this ghat cannot be checked against the limits.")
        hi["findings"].append("कोई उपयोगी DO, BOD या pH माप दर्ज नहीं है, इसलिए इस घाट को सीमाओं के विरुद्ध जाँचा नहीं जा सकता।")
    elif not (s["do_breaches"] or s["bod_breaches"] or s["ph_breaches"]):
        en["findings"].append("No CPCB Class B breach in the readings that are on record.")
        hi["findings"].append("उपलब्ध रिकॉर्ड में CPCB श्रेणी-B की कोई सीमा-उल्लंघन नहीं मिला।")

    def f(v):
        return "n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:+.1f}"
    if not (np.isnan(s["during_do_change"]) and np.isnan(s["during_bod_change"])):
        en["findings"].append(f"Compared with before immersion, on average: during immersion DO {f(s['during_do_change'])} and BOD "
                              f"{f(s['during_bod_change'])} mg/L; one week after DO {f(s['after_do_change'])} and BOD {f(s['after_bod_change'])} mg/L.")
        hi["findings"].append(f"विसर्जन से पहले की तुलना में औसतन: विसर्जन के दौरान DO {f(s['during_do_change'])} और BOD "
                              f"{f(s['during_bod_change'])} mg/L; एक सप्ताह बाद DO {f(s['after_do_change'])} और BOD {f(s['after_bod_change'])} mg/L।")
    if s["no_data"]:
        en["findings"].append(f"{s['no_data']} of {s['readings']} expected readings ({s['gap_pct']:g}%) are missing or inconclusive. "
                              "Missing data is treated as a risk, not as clean water.")
        hi["findings"].append(f"अपेक्षित {s['readings']} में से {s['no_data']} माप ({s['gap_pct']:g}%) अनुपलब्ध या अनिर्णायक हैं। "
                              "अनुपलब्ध डेटा को स्वच्छ जल नहीं, जोखिम माना गया है।")

    if level == "High":
        en["actions"].append("Prioritise this ghat for water testing and an on-site inspection before immersion begins.")
        hi["actions"].append("विसर्जन शुरू होने से पहले इस घाट पर जल परीक्षण और स्थल निरीक्षण को प्राथमिकता दें।")
    if s["need_aeration"] != "Low":
        en["actions"].append("Arrange aeration here before immersion: dissolved oxygen is repeatedly below the limit.")
        hi["actions"].append("विसर्जन से पहले यहाँ वायुयन (एरेशन) की व्यवस्था करें: घुलित ऑक्सीजन बार-बार सीमा से कम रही है।")
    if s["need_cleaning"] != "Low":
        en["actions"].append("Send a cleaning crew: clear idol remains and offerings promptly, and consider designated artificial immersion tanks.")
        hi["actions"].append("सफ़ाई दल भेजें: मूर्ति अवशेष व पूजन सामग्री शीघ्र हटवाएँ, और निर्धारित कृत्रिम विसर्जन कुंड पर विचार करें।")
    if s["need_testing"] != "Low":
        en["actions"].append("Collect fresh DO, BOD and pH samples (before, during and after) to close the data gap before relying on this ranking.")
        hi["actions"].append("इस रैंकिंग पर निर्भर होने से पहले DO, BOD और pH के नए नमूने (पहले, दौरान और बाद में) लेकर डेटा अंतर भरें।")
    if not en["actions"]:
        en["actions"].append("Continue routine monitoring and re-check water quality before the festival.")
        hi["actions"].append("नियमित निगरानी जारी रखें और उत्सव से पहले जल गुणवत्ता की पुनः जाँच करें।")
    return {"en": en, "hi": hi}

"""CPCB Class B compliance checks and historical risk scoring for each ghat.

Limits (CPCB "bathing" water, Class B):
    Dissolved Oxygen (DO) >= 5 mg/L
    Biochemical Oxygen Demand (BOD) <= 3 mg/L

Core rule: missing or inconclusive data is NEVER treated as clean. Every reading ends up
as exactly one of PASS / BREACH / NO DATA, and NO DATA is penalised in the score.

The score is a transparent weighted sum, so an officer can see why a ghat ranks where it
does. It describes *historical* records only; it is not a live safety measurement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from utils.data_loader import POST, PRE

DO_MIN = 5.0   # mg/L, must be at least this
BOD_MAX = 3.0  # mg/L, must be at most this

PASS, BREACH, NO_DATA = "PASS", "BREACH", "NO DATA"

# Score = 100 * (W_BREACH * breach rate + W_SEVERITY * severity + W_DETERIORATION * deterioration)
W_BREACH, W_SEVERITY, W_DETERIORATION = 0.60, 0.25, 0.15
GAP_WEIGHT = 0.5          # a NO DATA reading counts as this fraction of a breach
GAP_FLAG_SHARE = 0.25     # above this share of NO DATA, the ghat can't rank as Low
HIGH_AT, MEDIUM_AT = 60, 35

DISCLAIMER_EN = "Priority ranking based on historical records, not a live real-time safety measurement."
DISCLAIMER_HI = "यह प्राथमिकता रैंकिंग ऐतिहासिक रिकॉर्ड पर आधारित है, लाइव वास्तविक-समय सुरक्षा माप पर नहीं।"

GHAT_HI = {
    "Prempura Ghat": "प्रेमपुरा घाट",
    "Khatlapura Ghat": "खटलापुरा घाट",
    "Bhadbhada Ghat": "भदभदा घाट",
    "Lalghati Ghat": "लालघाटी घाट",
    "Motia Talab Ghat": "मोतिया तालाब घाट",
    "Munshi Hussain Khan Talab Ghat": "मुंशी हुसैन खां तालाब घाट",
    "Shahpura Lake Ghat": "शाहपुरा झील घाट",
}
LEVEL_HI = {"High": "उच्च", "Medium": "मध्यम", "Low": "निम्न"}


# ---------------------------------------------------------------- per-reading checks
def check_do(value: float, qual: str) -> str:
    """Status of one DO reading. A censored value only counts when it settles the question."""
    if pd.isna(value):
        return NO_DATA
    if qual == "<":                       # true value is below `value`
        return BREACH if value <= DO_MIN else NO_DATA
    if qual == ">":                       # true value is above `value`
        return PASS if value >= DO_MIN else NO_DATA
    return PASS if value >= DO_MIN else BREACH


def check_bod(value: float, qual: str) -> str:
    """Status of one BOD reading. ``"<2"`` is a pass; ``"<5"`` proves nothing."""
    if pd.isna(value):
        return NO_DATA
    if qual == "<":
        return PASS if value <= BOD_MAX else NO_DATA
    if qual == ">":
        return BREACH if value >= BOD_MAX else NO_DATA
    return PASS if value <= BOD_MAX else BREACH


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """Add status and exceedance (0..1, how far past the limit) columns for DO and BOD."""
    out = df.copy()
    out["do_status"] = [check_do(v, q) for v, q in zip(out["do_value"], out["do_qual"])]
    out["bod_status"] = [check_bod(v, q) for v, q in zip(out["bod_value"], out["bod_qual"])]
    out["do_exceed"] = np.where(out["do_status"] == BREACH,
                                ((DO_MIN - out["do_value"]) / DO_MIN).clip(0, 1), 0.0)
    out["bod_exceed"] = np.where(out["bod_status"] == BREACH,
                                 ((out["bod_value"] - BOD_MAX) / BOD_MAX).clip(0, 1), 0.0)
    return out


# ---------------------------------------------------------------- scoring
def _level(score: float) -> str:
    return "High" if score >= HIGH_AT else "Medium" if score >= MEDIUM_AT else "Low"


def _phase_change(g: pd.DataFrame) -> tuple[float, float, float]:
    """Average Pre -> Post change in DO and BOD, and a 0..1 deterioration measure.

    Only years where both phases have a numeric value for that parameter are compared.
    """
    pre = g[g.phase == PRE].set_index("year")
    post = g[g.phase == POST].set_index("year")
    d_do = (post["do_value"] - pre["do_value"]).dropna()
    d_bod = (post["bod_value"] - pre["bod_value"]).dropna()
    avg_do = float(d_do.mean()) if len(d_do) else np.nan
    avg_bod = float(d_bod.mean()) if len(d_bod) else np.nan
    parts = []
    if len(d_do):
        parts.append((-d_do).clip(lower=0, upper=DO_MIN).mean() / DO_MIN)
    if len(d_bod):
        parts.append(d_bod.clip(lower=0, upper=BOD_MAX).mean() / BOD_MAX)
    return avg_do, avg_bod, float(np.mean(parts)) if parts else 0.0


def summarise_ghat(g: pd.DataFrame) -> dict:
    """Score one ghat from its annotated rows (all years, both phases)."""
    g = g.copy()
    # Recent years weigh more: weight = rank of the year (oldest = 1).
    g["w"] = g["year"].rank(method="dense")
    wsum = g["w"].sum() * 2  # two parameters per row

    def counts(status):
        return int((g["do_status"] == status).sum() + (g["bod_status"] == status).sum())

    breach_w = g.loc[g.do_status == BREACH, "w"].sum() + g.loc[g.bod_status == BREACH, "w"].sum()
    gap_w = g.loc[g.do_status == NO_DATA, "w"].sum() + g.loc[g.bod_status == NO_DATA, "w"].sum()
    breach_rate = (breach_w + GAP_WEIGHT * gap_w) / wsum
    severity = float(((g["do_exceed"] + g["bod_exceed"]) * g["w"]).sum() / wsum)
    avg_do, avg_bod, deterioration = _phase_change(g)

    total, gaps = len(g) * 2, counts(NO_DATA)
    gap_share = gaps / total
    score = 100 * (W_BREACH * breach_rate + W_SEVERITY * severity + W_DETERIORATION * deterioration)
    floor_applied = gap_share > GAP_FLAG_SHARE and score < MEDIUM_AT
    if floor_applied:  # too little evidence to call this ghat low risk
        score = float(MEDIUM_AT)
    score = round(min(score, 100.0), 1)

    return {
        "risk_score": score, "risk_level": _level(score), "floor_applied": floor_applied,
        "do_breaches": int((g.do_status == BREACH).sum()), "do_tested": int((g.do_status != NO_DATA).sum()),
        "bod_breaches": int((g.bod_status == BREACH).sum()), "bod_tested": int((g.bod_status != NO_DATA).sum()),
        "breaches": counts(BREACH), "readings": total, "no_data": gaps,
        "gap_pct": round(100 * gap_share, 1),
        "avg_do_change": avg_do, "avg_bod_change": avg_bod, "deterioration": round(deterioration, 2),
        "breach_rate": round(breach_rate, 3), "severity": round(severity, 3),
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
    en = {"headline": f"{ghat}: {level} priority (risk score {s['risk_score']:.0f}/100)",
          "findings": [], "actions": []}
    hi = {"headline": f"{ghat_hi}: {LEVEL_HI[level]} प्राथमिकता (जोखिम स्कोर {s['risk_score']:.0f}/100)",
          "findings": [], "actions": []}

    if s["do_breaches"]:
        en["findings"].append(f"{s['do_breaches']} of {s['do_tested']} tested DO readings were below "
                              f"the CPCB Class B minimum of {DO_MIN:g} mg/L.")
        hi["findings"].append(f"{s['do_tested']} में से {s['do_breaches']} घुलित ऑक्सीजन (DO) माप "
                              f"CPCB श्रेणी-B की न्यूनतम सीमा {DO_MIN:g} mg/L से कम रहे।")
    if s["bod_breaches"]:
        en["findings"].append(f"{s['bod_breaches']} of {s['bod_tested']} tested BOD readings exceeded "
                              f"the CPCB Class B maximum of {BOD_MAX:g} mg/L.")
        hi["findings"].append(f"{s['bod_tested']} में से {s['bod_breaches']} BOD माप "
                              f"CPCB श्रेणी-B की अधिकतम सीमा {BOD_MAX:g} mg/L से अधिक रहे।")
    if not (s["do_breaches"] or s["bod_breaches"]):
        en["findings"].append("No CPCB Class B breach in the readings that are on record.")
        hi["findings"].append("उपलब्ध रिकॉर्ड में CPCB श्रेणी-B की कोई सीमा-उल्लंघन नहीं मिला।")

    worse_after = ((not np.isnan(s["avg_do_change"]) and s["avg_do_change"] < 0)
                   or (not np.isnan(s["avg_bod_change"]) and s["avg_bod_change"] > 0))
    if not (np.isnan(s["avg_do_change"]) and np.isnan(s["avg_bod_change"])):
        do_c = "n/a" if np.isnan(s["avg_do_change"]) else f"{s['avg_do_change']:+.1f}"
        bod_c = "n/a" if np.isnan(s["avg_bod_change"]) else f"{s['avg_bod_change']:+.1f}"
        en["findings"].append(f"Average change from pre- to post-Visarjan: DO {do_c} mg/L, BOD {bod_c} mg/L.")
        hi["findings"].append(f"विसर्जन से पहले से बाद तक औसत बदलाव: DO {do_c} mg/L, BOD {bod_c} mg/L।")

    if s["no_data"]:
        en["findings"].append(f"{s['no_data']} of {s['readings']} expected readings ({s['gap_pct']:g}%) are missing "
                              "or inconclusive. Missing data is treated as a risk, not as clean water.")
        hi["findings"].append(f"अपेक्षित {s['readings']} में से {s['no_data']} माप ({s['gap_pct']:g}%) अनुपलब्ध या "
                              "अनिर्णायक हैं। अनुपलब्ध डेटा को स्वच्छ जल नहीं, जोखिम माना गया है।")

    if level == "High":
        en["actions"].append("Prioritise this ghat for water testing and an on-site inspection before immersion begins.")
        hi["actions"].append("विसर्जन शुरू होने से पहले इस घाट पर जल परीक्षण और स्थल निरीक्षण को प्राथमिकता दें।")
    if s["do_breaches"] or s["bod_breaches"]:
        en["actions"].append("Consider designated artificial immersion tanks or limits on idol immersion at this ghat.")
        hi["actions"].append("इस घाट पर निर्धारित कृत्रिम विसर्जन कुंड की व्यवस्था या मूर्ति विसर्जन की सीमा पर विचार करें।")
    if worse_after:
        en["actions"].append("Sample the water soon after immersion and clear idol remains and offerings promptly.")
        hi["actions"].append("विसर्जन के तुरंत बाद जल का नमूना लें और मूर्ति अवशेष व पूजन सामग्री शीघ्र हटवाएँ।")
    if s["no_data"]:
        en["actions"].append("Collect fresh DO and BOD samples to close the data gap before relying on this ranking.")
        hi["actions"].append("इस रैंकिंग पर निर्भर होने से पहले DO और BOD के नए नमूने लेकर डेटा अंतर भरें।")
    if not en["actions"]:
        en["actions"].append("Continue routine monitoring and re-check water quality before the festival.")
        hi["actions"].append("नियमित निगरानी जारी रखें और उत्सव से पहले जल गुणवत्ता की पुनः जाँच करें।")
    return {"en": en, "hi": hi}

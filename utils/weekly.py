"""The weekly public update: a short bilingual caption written from the latest ranking.

Captions come from fixed templates filled with the real numbers, never from a language model, so
nothing invented (a health claim, a wrong figure) can be posted. Each caption ends with three tips on
avoiding common mistakes; the set rotates weekly so the posts do not repeat.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from utils.clock import today_ist
from utils.risk_engine import GHAT_HI, LEVEL_HI

DURGA_VISARJAN = date(2026, 10, 20)
SITE = "https://ghatwatch.vercel.app"

# (English, Hindi) pairs. Practical advice only: no health claims the data cannot support.
TIPS = [
    ("Untested is not clean. Test a ghat before immersion.",
     "जाँच नहीं हुई ≠ साफ़ पानी। विसर्जन से पहले घाट की जाँच करें।"),
    ("These are past readings. Re-test just before immersion day.",
     "ये पुराने माप हैं। विसर्जन के दिन से ठीक पहले दोबारा जाँच करें।"),
    ("Use clay idols. Remove plastic, paint and flowers first.",
     "मिट्टी की मूर्ति चुनें। पहले प्लास्टिक, रंग और फूल हटाएँ।"),
    ("Immerse only at designated ghats or tanks, not the Upper or Lower Lake (NGT ban).",
     "विसर्जन केवल निर्धारित घाट या कुंड पर करें, ऊपरी/निचली झील में नहीं (NGT प्रतिबंध)।"),
    ("Don't tip food or flower offerings into the water. They use up oxygen.",
     "खाने और फूल की भेंट पानी में न डालें। ये ऑक्सीजन घटाते हैं।"),
    ("Read DO and BOD together, and compare before with after.",
     "DO और BOD साथ देखें, और पहले बनाम बाद की तुलना करें।"),
]


def days_left(today: date | None = None) -> int | None:
    """Days until Durga Visarjan, or None once it has passed."""
    n = (DURGA_VISARJAN - (today or today_ist())).days
    return n if n >= 0 else None


def tips_for(today: date) -> list[tuple[str, str]]:
    """Three tips, rotating by ISO week so consecutive weeks differ."""
    week = today.isocalendar()[1]
    return [TIPS[(week * 3 + i) % len(TIPS)] for i in range(3)]


def build_weekly_report(ranking: pd.DataFrame, is_mock: bool, today: date | None = None) -> dict:
    """Both captions plus the facts behind them. ``ranking`` is ``risk_engine.rank_ghats`` output."""
    today = today or today_ist()
    top = ranking.iloc[0]
    n, high = len(ranking), int((ranking.risk_level == "High").sum())
    gap = round(100 * ranking.no_data.sum() / ranking.readings.sum())
    left, tips = days_left(today), tips_for(today)
    score = round(top.risk_score)

    en = [f"GhatWatch weekly update · {today:%d %b %Y}",
          f"Highest risk: {top.ghat} ({score}/100, {top.risk_level}). {high} of {n} ghats high risk · "
          f"{gap}% of readings missing.",
          "Historical records, not live readings."]
    hi = [f"GhatWatch साप्ताहिक अपडेट · {today:%d/%m/%Y}",
          f"सर्वाधिक जोखिम: {GHAT_HI.get(top.ghat, top.ghat)} ({score}/100, {LEVEL_HI[top.risk_level]}). "
          f"{n} में से {high} घाट उच्च जोखिम · {gap}% माप अनुपलब्ध।",
          "ऐतिहासिक रिकॉर्ड, लाइव माप नहीं।"]
    if left is not None:
        en.append("Durga Visarjan is today." if left == 0 else f"{left} {'day' if left == 1 else 'days'} to Durga Visarjan.")
        hi.append("आज दुर्गा विसर्जन है।" if left == 0 else f"दुर्गा विसर्जन में {left} दिन।")
    en += ["Avoid mistakes:"] + [f"{i}. {t[0]}" for i, t in enumerate(tips, 1)] + [f"{SITE} #Bhopal #Visarjan"]
    hi += ["गलतियों से बचें:"] + [f"{i}. {t[1]}" for i, t in enumerate(tips, 1)] + [f"{SITE} #भोपाल #विसर्जन"]
    return {"date": today.isoformat(), "is_demo": is_mock, "caption_en": "\n".join(en), "caption_hi": "\n".join(hi),
            "tips": [{"en": a, "hi": b} for a, b in tips]}

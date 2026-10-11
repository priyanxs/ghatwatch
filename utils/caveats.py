"""What the data does NOT cover, in both languages.

Part fixed (from the Track 2 participant guide), part worked out from the data actually loaded, so the
page can say honestly where it is thin. The fixed notes avoid any claim about health effects.
"""
from __future__ import annotations

import pandas as pd

from utils.risk_engine import GHAT_HI, NO_DATA


def _gaps(data: pd.DataFrame) -> list[dict]:
    """Ghat / period combinations where the report has no table at all."""
    out = []
    for (ghat, period), g in data.groupby(["ghat", "period"]):
        if (g["page"] == "(no record)").all():
            out.append({"en": f"{ghat}: the report has no table for {period}, so it is counted as missing data.",
                        "hi": f"{GHAT_HI.get(ghat, ghat)}: रिपोर्ट में {period} की कोई तालिका नहीं है, इसलिए इसे अनुपलब्ध डेटा गिना गया है।"})
    return out


def _not_sampled(data: pd.DataFrame) -> list[dict]:
    """How many individual readings were blank, flagged not sampled, or otherwise unusable (outside the no-table periods)."""
    have_table = data[data["page"] != "(no record)"]
    n = int(sum((have_table[f"{p}_status"] == NO_DATA).sum() for p in ("do", "bod", "ph")))
    if not n:
        return []
    return [{"en": f"{n} individual DO, BOD or pH readings are blank, not sampled or otherwise unusable. They are shown as missing, never as clean.",
             "hi": f"{n} अलग-अलग DO, BOD या pH माप खाली, बिना नमूने के या अनुपयोगी हैं। इन्हें अनुपलब्ध दिखाया गया है, स्वच्छ नहीं।"}]


FIXED = [
    {"en": "Why CPCB Class B: it is the class for organised outdoor bathing, the closest match to people and idols entering the water at a ghat. Limits used: DO at least 5 mg/L, BOD at most 3 mg/L, pH 6.5 to 8.5.",
     "hi": "CPCB श्रेणी-B क्यों: यह संगठित बाहरी स्नान की श्रेणी है, जो घाट पर लोगों और मूर्तियों के पानी में जाने के सबसे करीब है। प्रयुक्त सीमाएँ: DO कम से कम 5 mg/L, BOD अधिकतम 3 mg/L, pH 6.5 से 8.5।"},
    {"en": "Only DO, BOD and pH are scored. COD, solids, turbidity, conductivity and the four metals tested (chromium, lead, zinc, copper) have no Class B limit. There is no coliform data.",
     "hi": "केवल DO, BOD और pH को आँका गया है। COD, ठोस, गंदलापन, चालकता और जाँचे गए चार धातु (क्रोमियम, सीसा, जस्ता, ताँबा) की श्रेणी-B में कोई सीमा नहीं है। कोलीफ़ॉर्म का डेटा नहीं है।"},
    {"en": "The reports print no units. The standard unit for each test is assumed (mg/L for DO and BOD).",
     "hi": "रिपोर्टों में इकाइयाँ नहीं छपी हैं। हर जाँच की मानक इकाई मानी गई है (DO और BOD के लिए mg/L)।"},
    {"en": "Each festival is sampled three times only: before, during and one week after. A short spike between samples can be missed.",
     "hi": "हर उत्सव में केवल तीन बार नमूने लिए जाते हैं: पहले, दौरान और एक सप्ताह बाद। नमूनों के बीच की कोई छोटी उछाल छूट सकती है।"},
    {"en": "“Rani Kamlapati ghat / Kamla Park kund” may be two different places: Ganesh tables say Kamla Park kund, Durga tables say Lower Lake ghat. The match is medium confidence.",
     "hi": "“रानी कमलापति घाट / कमला पार्क कुंड” दो अलग स्थान हो सकते हैं: गणेश तालिकाओं में कमला पार्क कुंड और दुर्गा तालिकाओं में निचली झील घाट लिखा है। मिलान मध्यम विश्वसनीयता का है।"},
    {"en": "BDL / ND (below detection limit) is read as “very low”, not zero and not missing: a pass for BOD, no usable result for DO and pH.",
     "hi": "BDL / ND (पहचान सीमा से कम) को “बहुत कम” माना गया है, शून्य या अनुपलब्ध नहीं: BOD के लिए सीमा के भीतर, DO और pH के लिए कोई उपयोगी परिणाम नहीं।"},
    {"en": "The ranking compares readings with legal limits only. It makes no claim about health effects.",
     "hi": "रैंकिंग केवल माप की कानूनी सीमाओं से तुलना करती है। स्वास्थ्य पर प्रभाव के बारे में कोई दावा नहीं किया गया है।"},
]


def build_caveats(data: pd.DataFrame) -> list[dict]:
    """Computed gaps first (they are about this data), then the fixed notes."""
    return _gaps(data) + _not_sampled(data) + FIXED

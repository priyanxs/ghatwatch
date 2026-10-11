"""English / Hindi text for the dashboard interface.

Only interface wording lives here. Water-quality values, ghat records and the action brief
text (``risk_engine.build_brief``) are handled elsewhere. Missing keys fall back to English,
then to the key itself, so a gap in a translation never crashes the page.
"""
from __future__ import annotations

from utils.risk_engine import GHAT_HI

LANGUAGES = {"en": "English", "hi": "हिन्दी"}

STRINGS: dict[str, dict[str, str]] = {
    # --- header / chrome
    "subtitle": {"en": "Visarjan water-quality decision assistant · Bhopal Municipal Corporation",
                 "hi": "विसर्जन जल-गुणवत्ता निर्णय सहायक · भोपाल नगर निगम"},
    "pill.ghats": {"en": "{n} Bhopal ghats", "hi": "भोपाल के {n} घाट"},
    "pill.cpcb": {"en": "CPCB Class B limits", "hi": "CPCB श्रेणी-B सीमाएँ"},
    "pill.brief": {"en": "English + हिन्दी brief", "hi": "English + हिन्दी सार"},
    "pill.hist": {"en": "Historical records · not live", "hi": "ऐतिहासिक रिकॉर्ड · लाइव नहीं"},
    "demo": {"en": "<b>Demo data.</b> The values below are generated for demonstration and are not real "
                   "measurements. Put your records in <code>data/bhopal_water_quality.csv</code> to replace them.",
             "hi": "<b>डेमो डेटा।</b> नीचे दिए गए मान प्रदर्शन के लिए बनाए गए हैं, वास्तविक माप नहीं हैं। "
                   "इन्हें बदलने के लिए अपने रिकॉर्ड <code>data/bhopal_water_quality.csv</code> में रखें।"},
    "notes": {"en": "Data-loading notes ({n})", "hi": "डेटा लोड संबंधी टिप्पणियाँ ({n})"},
    # --- sidebar
    "sb.brand": {"en": "Bhopal · BMC decision support", "hi": "भोपाल · BMC निर्णय सहायता"},
    "sb.lang": {"en": "Language / भाषा", "hi": "Language / भाषा"},
    "sb.select": {"en": "Select a ghat", "hi": "घाट चुनें"},
    "sb.caption": {"en": "Ghats are listed from highest to lowest risk.",
                   "hi": "घाट उच्चतम से निम्नतम जोखिम के क्रम में हैं।"},
    # --- overview
    "m.ghats": {"en": "Ghats monitored", "hi": "निगरानी वाले घाट"},
    "m.high": {"en": "High-risk ghats", "hi": "उच्च-जोखिम घाट"},
    "m.breaches": {"en": "CPCB Class B breaches", "hi": "CPCB श्रेणी-B उल्लंघन"},
    "m.breaches.help": {"en": "DO below 5 mg/L or BOD above 3 mg/L, all years.",
                        "hi": "सभी वर्षों में DO 5 mg/L से कम या BOD 3 mg/L से अधिक।"},
    "m.nodata": {"en": "Readings with no data", "hi": "बिना डेटा वाले माप"},
    "m.nodata.help": {"en": "Missing or inconclusive readings. These are never counted as clean.",
                      "hi": "अनुपलब्ध या अनिर्णायक माप। इन्हें कभी स्वच्छ नहीं गिना जाता।"},
    "h.ranking": {"en": "Priority ranking", "hi": "प्राथमिकता रैंकिंग"},
    "h.ranking.sub": {"en": "The 7 ghats ordered by historical risk score, highest first",
                      "hi": "ऐतिहासिक जोखिम स्कोर के अनुसार घाट, सबसे अधिक जोखिम पहले"},
    "r.rank": {"en": "Rank", "hi": "क्रम"},
    "r.ghat": {"en": "Ghat", "hi": "घाट"},
    "r.level": {"en": "Risk level", "hi": "जोखिम स्तर"},
    "r.score": {"en": "Risk score", "hi": "जोखिम स्कोर"},
    "r.do": {"en": "DO breaches", "hi": "DO उल्लंघन"},
    "r.bod": {"en": "BOD breaches", "hi": "BOD उल्लंघन"},
    "r.gap": {"en": "Data gap %", "hi": "डेटा अंतर %"},
    "r.caption": {"en": "Breach columns read “breaches / readings tested”. Score weights recent years more, "
                        "and adds a penalty for missing data.",
                  "hi": "उल्लंघन कॉलम “उल्लंघन / परखे गए माप” दर्शाते हैं। स्कोर में हाल के वर्षों को अधिक महत्व "
                        "मिलता है और अनुपलब्ध डेटा पर दंड जुड़ता है।"},
    # --- selected ghat
    "g.sub": {"en": "Rank {r} of {n} by historical risk score",
              "hi": "ऐतिहासिक जोखिम स्कोर के अनुसार {n} में से क्रम {r}"},
    "tab.dive": {"en": "Deep-dive & evidence", "hi": "विस्तृत विश्लेषण और साक्ष्य"},
    "tab.trends": {"en": "Historical trends", "hi": "ऐतिहासिक रुझान"},
    "tab.brief": {"en": "Action brief & PDF", "hi": "कार्य-सार और PDF"},
    "d.score": {"en": "Risk score", "hi": "जोखिम स्कोर"},
    "d.level": {"en": "Risk level", "hi": "जोखिम स्तर"},
    "d.breaches": {"en": "CPCB breaches", "hi": "CPCB उल्लंघन"},
    "d.gap": {"en": "Data gap", "hi": "डेटा अंतर"},
    "d.missing": {"en": "**Missing-data rule:** {n} of {total} expected readings are missing or inconclusive "
                        "(for example “<5” for BOD cannot prove compliance). Missing data is **never** counted "
                        "as clean water; each one adds to the risk score.",
                  "hi": "**अनुपलब्ध-डेटा नियम:** अपेक्षित {total} में से {n} माप अनुपलब्ध या अनिर्णायक हैं "
                        "(जैसे BOD के लिए “<5” अनुपालन सिद्ध नहीं करता)। अनुपलब्ध डेटा को **कभी** स्वच्छ जल नहीं "
                        "गिना जाता; हर ऐसा माप जोखिम स्कोर बढ़ाता है।"},
    "d.floor": {"en": "Too little data to rate this ghat Low. Its score is held at the Medium threshold ({m}) "
                      "until it is re-tested.",
                "hi": "इस घाट को निम्न जोखिम आँकने के लिए डेटा बहुत कम है। पुनः परीक्षण होने तक इसका स्कोर "
                      "मध्यम सीमा ({m}) पर रोका गया है।"},
    "d.limit": {"en": "CPCB Class B limit check  ·  DO ≥ {do} mg/L  ·  BOD ≤ {bod} mg/L",
                "hi": "CPCB श्रेणी-B सीमा जाँच  ·  DO ≥ {do} mg/L  ·  BOD ≤ {bod} mg/L"},
    "c.year": {"en": "Year", "hi": "वर्ष"},
    "c.phase": {"en": "Phase", "hi": "चरण"},
    "c.do": {"en": "DO (mg/L)", "hi": "DO (mg/L)"},
    "c.bod": {"en": "BOD (mg/L)", "hi": "BOD (mg/L)"},
    "d.how": {"en": "How this score is built", "hi": "यह स्कोर कैसे बना"},
    "d.how.body": {
        "en": "- **Breach rate × {w1}**: share of readings breaching a limit (recent years weigh more). "
              "Each no-data reading counts as {gw} of a breach. → `{br}`\n"
              "- **Severity × {w2}**: how far breaching values are past the limit. → `{sev}`\n"
              "- **Post-Visarjan deterioration × {w3}**: average fall in DO and rise in BOD from pre- to "
              "post-Visarjan. → `{det}`\n"
              "- Levels: High ≥ {hi}, Medium ≥ {mid}, otherwise Low.",
        "hi": "- **उल्लंघन दर × {w1}**: सीमा तोड़ने वाले मापों का हिस्सा (हाल के वर्षों को अधिक महत्व)। "
              "प्रत्येक डेटा-रहित माप उल्लंघन के {gw} के बराबर गिना जाता है। → `{br}`\n"
              "- **गंभीरता × {w2}**: उल्लंघन वाले मान सीमा से कितने आगे हैं। → `{sev}`\n"
              "- **विसर्जन-पश्चात गिरावट × {w3}**: विसर्जन से पहले से बाद तक DO में औसत गिरावट और BOD में औसत "
              "वृद्धि। → `{det}`\n"
              "- स्तर: उच्च ≥ {hi}, मध्यम ≥ {mid}, अन्यथा निम्न।"},
    "d.evidence": {"en": "Evidence trail (source report and PDF page)",
                   "hi": "साक्ष्य ट्रेल (स्रोत रिपोर्ट और PDF पृष्ठ)"},
    "e.source": {"en": "Source report", "hi": "स्रोत रिपोर्ट"},
    "e.page": {"en": "PDF page", "hi": "PDF पृष्ठ"},
    "e.do": {"en": "DO as recorded", "hi": "दर्ज DO"},
    "e.bod": {"en": "BOD as recorded", "hi": "दर्ज BOD"},
    # --- trends
    "tr.do": {"en": "Dissolved Oxygen (higher is better)", "hi": "घुलित ऑक्सीजन (अधिक बेहतर)"},
    "tr.bod": {"en": "BOD (lower is better)", "hi": "BOD (कम बेहतर)"},
    "tr.lim.do": {"en": "CPCB Class B minimum {v}", "hi": "CPCB श्रेणी-B न्यूनतम {v}"},
    "tr.lim.bod": {"en": "CPCB Class B maximum {v}", "hi": "CPCB श्रेणी-B अधिकतम {v}"},
    "tr.cap": {"en": "Breaks in a line mean no usable reading that year. Censored values such as “<2” are plotted "
                     "at their stated bound; hover shows the value as recorded.",
               "hi": "रेखा में टूटन का अर्थ है उस वर्ष कोई उपयोगी माप नहीं। “<2” जैसे सीमित मान उनकी बताई सीमा पर "
                     "दर्शाए गए हैं; होवर करने पर दर्ज मान दिखता है।"},
    # --- brief
    "b.note": {"en": "The PDF always contains both languages.", "hi": "PDF में हमेशा दोनों भाषाएँ रहती हैं।"},
    "b.nohindi": {"en": "The PDF will be English-only: install `uharfbuzz` and a Devanagari font to include Hindi.",
                  "hi": "PDF केवल अंग्रेज़ी में बनेगा: हिन्दी जोड़ने के लिए `uharfbuzz` और देवनागरी फ़ॉन्ट इंस्टॉल करें।"},
    "b.download": {"en": "⬇️ Download PDF Brief", "hi": "⬇️ PDF सार डाउनलोड करें"},
    "b.error": {"en": "Could not build the PDF brief: {e}", "hi": "PDF सार नहीं बन सका: {e}"},
    # --- simple single-page layout (public frontend)
    "top.summary": {"en": "<b>{high} of {n} ghats</b> are high risk · {breaches} CPCB breaches on record · "
                          "{gap}% of readings missing",
                    "hi": "<b>{n} में से {high} घाट</b> उच्च जोखिम वाले हैं · रिकॉर्ड में CPCB उल्लंघन {breaches} · "
                          "{gap}% माप अनुपलब्ध"},
    "r.line": {"en": "DO below limit {do} of {dt} · BOD above limit {bod} of {bt} · {gap}% data missing",
               "hi": "DO सीमा से कम {do}/{dt} · BOD सीमा से अधिक {bod}/{bt} · {gap}% डेटा अनुपलब्ध"},
    "h.pick": {"en": "Tap a ghat to see its details below.", "hi": "नीचे विवरण देखने के लिए किसी घाट को चुनें।"},
    "sec.why": {"en": "What the tests show", "hi": "जाँच क्या बताती है"},
    "sec.do": {"en": "What to do", "hi": "क्या करें"},
    "sec.trend": {"en": "How it changed over the years", "hi": "वर्षों में बदलाव"},
    "sec.table": {"en": "All readings and their sources", "hi": "सभी माप और उनके स्रोत"},
    "sec.brief": {"en": "Action brief", "hi": "कार्य-सार"},
    "b.other": {"en": "Also in हिन्दी", "hi": "English में भी देखें"},
    "tr.help": {"en": "Dotted line = CPCB limit. A break in a line means no reading that year.",
                "hi": "बिंदीदार रेखा = CPCB सीमा। रेखा में टूटन का अर्थ है उस वर्ष कोई माप नहीं।"},
    "err.load": {"en": "Could not load this ghat ({e}). Please try again.",
                 "hi": "यह घाट लोड नहीं हो सका ({e})। कृपया पुनः प्रयास करें।"},
    # --- value labels
    "lvl.High": {"en": "High", "hi": "उच्च"},
    "lvl.Medium": {"en": "Medium", "hi": "मध्यम"},
    "lvl.Low": {"en": "Low", "hi": "निम्न"},
    "phase.Pre-Visarjan": {"en": "Pre-Visarjan", "hi": "विसर्जन से पहले"},
    "phase.Post-Visarjan": {"en": "Post-Visarjan", "hi": "विसर्जन के बाद"},
    "status.PASS": {"en": "✅ Pass", "hi": "✅ सीमा के भीतर"},
    "status.BREACH": {"en": "❌ Breach", "hi": "❌ उल्लंघन"},
    "status.NO DATA": {"en": "⚠️ No data", "hi": "⚠️ डेटा नहीं"},
    "val.(no record)": {"en": "(no record)", "hi": "(कोई रिकॉर्ड नहीं)"},
    "val.Not recorded": {"en": "Not recorded", "hi": "दर्ज नहीं"},
}


def text(key: str, lang: str, **fmt) -> str:
    """Interface string ``key`` in ``lang``, with ``fmt`` filled in."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    value = entry.get(lang) or entry["en"]
    return value.format(**fmt) if fmt else value


def ghat_name(name: str, lang: str) -> str:
    """Hindi ghat name when known, otherwise the name as recorded."""
    return GHAT_HI.get(name, name) if lang == "hi" else name


def label(prefix: str, value: str, lang: str) -> str:
    """Translate a category value (``lvl.High``, ``phase.Post-Visarjan`` ...); unknown values pass through."""
    key = f"{prefix}.{value}"
    return text(key, lang) if key in STRINGS else value

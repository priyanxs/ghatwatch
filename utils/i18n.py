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
    "c.year": {"en": "Year", "hi": "वर्ष"},
    "c.phase": {"en": "Phase", "hi": "चरण"},
    "c.do": {"en": "DO (mg/L)", "hi": "DO (mg/L)"},
    "c.bod": {"en": "BOD (mg/L)", "hi": "BOD (mg/L)"},
    "d.how": {"en": "How this score is built", "hi": "यह स्कोर कैसे बना"},
    "d.evidence": {"en": "Evidence trail (source report and PDF page)",
                   "hi": "साक्ष्य ट्रेल (स्रोत रिपोर्ट और PDF पृष्ठ)"},
    "e.source": {"en": "Source report", "hi": "स्रोत रिपोर्ट"},
    "e.open": {"en": "Open the source report in a new tab", "hi": "स्रोत रिपोर्ट नई टैब में खोलें"},
    "e.open.demo": {"en": "Demo reading: opens the real report for that year. Page numbers here are illustrative.",
                    "hi": "डेमो माप: उस वर्ष की असली रिपोर्ट खुलती है। यहाँ के पृष्ठ क्रमांक उदाहरण मात्र हैं।"},
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
    "h.pick": {"en": "Tap a ghat to see its details below.", "hi": "नीचे विवरण देखने के लिए किसी घाट को चुनें।"},
    "sec.why": {"en": "What the tests show", "hi": "जाँच क्या बताती है"},
    "sec.do": {"en": "What to do", "hi": "क्या करें"},
    "sec.trend": {"en": "How it changed over the years", "hi": "वर्षों में बदलाव"},
    "sec.table": {"en": "All readings and their sources", "hi": "सभी माप और उनके स्रोत"},
    "sec.brief": {"en": "Action brief", "hi": "कार्य-सार"},
    "b.other": {"en": "Also in हिन्दी", "hi": "English में भी देखें"},
    # --- dashboard layout (public frontend)
    "hero.tag": {"en": "Know which Visarjan ghats need attention first",
                 "hi": "जानिए विसर्जन के किन घाटों पर सबसे पहले ध्यान देना है"},
    "f.all": {"en": "All", "hi": "सभी"},
    "sec.detail": {"en": "Ghat details", "hi": "घाट का विवरण"},
    "latest.do": {"en": "Dissolved oxygen", "hi": "घुलित ऑक्सीजन"},
    "latest.bod": {"en": "BOD", "hi": "BOD"},
    "latest.limit.do": {"en": "Limit: at least {v} mg/L", "hi": "सीमा: कम से कम {v} mg/L"},
    "sec.compare": {"en": "Compare all ghats", "hi": "सभी घाटों की तुलना"},
    "sec.matrix": {"en": "Year-by-year status", "hi": "वर्ष-दर-वर्ष स्थिति"},
    "lg.pass": {"en": "Within limits", "hi": "सीमा के भीतर"},
    "lg.breach": {"en": "Breach", "hi": "उल्लंघन"},
    "lg.nodata": {"en": "No data (never counted as clean)", "hi": "डेटा नहीं (स्वच्छ नहीं गिना जाता)"},
    "src.title": {"en": "Source reports", "hi": "स्रोत रिपोर्ट"},
    "src.demo": {"en": "The demo data is not taken from these reports. Once the real records are loaded, every reading "
                       "links to its report and page.",
                 "hi": "डेमो डेटा इन रिपोर्टों से नहीं लिया गया है। असली रिकॉर्ड लोड होने पर हर माप अपनी रिपोर्ट और पृष्ठ से "
                       "जुड़ेगा।"},
    "src.live": {"en": "Every reading in the evidence table links to its report, at the cited page.",
                 "hi": "साक्ष्य तालिका का हर माप अपनी रिपोर्ट से, बताए गए पृष्ठ पर, जुड़ा है।"},
    "foot": {"en": "GhatWatch · Decision support for Bhopal Municipal Corporation. Based on historical records; "
                   "verify on site before acting.",
             "hi": "GhatWatch · भोपाल नगर निगम के लिए निर्णय सहायता। ऐतिहासिक रिकॉर्ड पर आधारित; "
                   "कार्रवाई से पहले स्थल पर जाँच करें।"},
    "tr.offline": {"en": "Charts could not be loaded (check the internet connection). The tables still show every reading.",
                   "hi": "चार्ट लोड नहीं हो सके (इंटरनेट कनेक्शन जाँचें)। तालिकाओं में हर माप अब भी दिख रहा है।"},
    # --- unique features
    "hero.countdown": {"en": "{n} days to Durga Visarjan · 20 Oct 2026", "hi": "दुर्गा विसर्जन में {n} दिन · 20 अक्टूबर 2026"},
    "trend.worse": {"en": "▲ worse than last year", "hi": "▲ पिछले वर्ष से बदतर"},
    "trend.better": {"en": "▼ better than last year", "hi": "▼ पिछले वर्ष से बेहतर"},
    "trend.same": {"en": "● about the same as last year", "hi": "● पिछले वर्ष के लगभग समान"},
    "trend.na": {"en": "no year-on-year data", "hi": "वर्ष-दर-वर्ष डेटा नहीं"},
    "city.download": {"en": "⬇️ City-wide brief (PDF)", "hi": "⬇️ पूरे शहर का सार (PDF)"},
    "city.help": {"en": "One page ranking all ghats with the first action for each, in English and Hindi.",
                  "hi": "एक पृष्ठ में सभी घाटों की रैंकिंग और हर घाट की पहली कार्रवाई, अंग्रेज़ी और हिन्दी में।"},
    "share.wa": {"en": "Share on WhatsApp", "hi": "WhatsApp पर भेजें"},
    "weekly.title": {"en": "Weekly public update", "hi": "साप्ताहिक सार्वजनिक अपडेट"},
    "weekly.lede": {"en": "Written automatically from the latest ranking, with three tips to avoid common mistakes. "
                          "Posted every Monday once social channels are connected.",
                    "hi": "नवीनतम रैंकिंग से अपने-आप लिखा जाता है, सामान्य गलतियों से बचने के तीन सुझावों के साथ। "
                          "सोशल चैनल जुड़ने पर हर सोमवार पोस्ट होता है।"},
    "weekly.copy": {"en": "Copy", "hi": "कॉपी करें"},
    "weekly.copied": {"en": "Copied ✓", "hi": "कॉपी हुआ ✓"},
    "weekly.off": {"en": "Auto-posting is off: nothing is published until channels are connected and enabled.",
                   "hi": "ऑटो-पोस्टिंग बंद है: चैनल जुड़ने और चालू होने तक कुछ प्रकाशित नहीं होता।"},
    "weekly.on": {"en": "Auto-posting is on for: {ch}.", "hi": "ऑटो-पोस्टिंग चालू है: {ch}।"},
    "weekly.demo": {"en": "Demo data is never posted automatically.", "hi": "डेमो डेटा कभी अपने-आप पोस्ट नहीं होता।"},
    "err.load": {"en": "Could not load this ghat ({e}). Please try again.",
                 "hi": "यह घाट लोड नहीं हो सका ({e})। कृपया पुनः प्रयास करें।"},
    "m.breaches.help": {"en": "DO below 5 mg/L, BOD above 3 mg/L or pH outside 6.5 to 8.5, all periods.",
                        "hi": "सभी अवधियों में DO 5 mg/L से कम, BOD 3 mg/L से अधिक या pH 6.5 से 8.5 के बाहर।"},
    "r.line": {"en": "DO below limit {do} of {dt} · BOD above limit {bod} of {bt} · pH out of range {ph} of {pt} · {gap}% data missing",
               "hi": "DO सीमा से कम {do}/{dt} · BOD सीमा से अधिक {bod}/{bt} · pH सीमा के बाहर {ph}/{pt} · {gap}% डेटा अनुपलब्ध"},
    "d.limit": {"en": "CPCB Class B limit check  ·  DO ≥ {do} mg/L  ·  BOD ≤ {bod} mg/L  ·  pH {phmin} to {phmax}",
                "hi": "CPCB श्रेणी-B सीमा जाँच  ·  DO ≥ {do} mg/L  ·  BOD ≤ {bod} mg/L  ·  pH {phmin} से {phmax}"},
    "d.how.body": {
        "en": "- **Breach rate × {w1}**: share of DO, BOD and pH readings breaching a CPCB Class B limit (recent periods weigh more). "
              "Each no-data reading counts as {gw} of a breach. → `{br}`\n"
              "- **Severity × {w2}**: how far breaching values are past the limit. → `{sev}`\n"
              "- **Impact of immersion × {w3}**: average fall in DO and rise in BOD from before to during immersion. → `{det}`\n"
              "- Levels: High ≥ {hi}, Medium ≥ {mid}, otherwise Low. These cut-offs are a starting point to agree with BMC.",
        "hi": "- **उल्लंघन दर × {w1}**: CPCB श्रेणी-B की सीमा तोड़ने वाले DO, BOD और pH मापों का हिस्सा (हाल की अवधियों को अधिक महत्व)। "
              "प्रत्येक डेटा-रहित माप उल्लंघन के {gw} के बराबर गिना जाता है। → `{br}`\n"
              "- **गंभीरता × {w2}**: उल्लंघन वाले मान सीमा से कितने आगे हैं। → `{sev}`\n"
              "- **विसर्जन का प्रभाव × {w3}**: विसर्जन से पहले से दौरान तक DO में औसत गिरावट और BOD में औसत वृद्धि। → `{det}`\n"
              "- स्तर: उच्च ≥ {hi}, मध्यम ≥ {mid}, अन्यथा निम्न। ये सीमाएँ BMC के साथ तय करने की शुरुआती रेखा हैं।"},
    "sec.latest": {"en": "Latest readings ({y})", "hi": "नवीनतम माप ({y})"},
    "latest.limit.bod": {"en": "Limit: at most {v} mg/L", "hi": "सीमा: अधिकतम {v} mg/L"},
    "latest.ph": {"en": "pH", "hi": "pH"},
    "latest.limit.ph": {"en": "Limit: {v}", "hi": "सीमा: {v}"},
    "latest.fallback": {"en": "{p} has no table for this ghat, so the latest available period is shown.",
                        "hi": "इस घाट की {p} की कोई तालिका नहीं है, इसलिए उपलब्ध नवीनतम अवधि दिखाई गई है।"},
    "matrix.help": {"en": "Each period has three cells: before, during and one week after immersion.",
                    "hi": "हर अवधि के तीन खाने हैं: विसर्जन से पहले, दौरान और एक सप्ताह बाद।"},
    "phase.Pre-Visarjan": {"en": "Before immersion", "hi": "विसर्जन से पहले"},
    "phase.During": {"en": "During immersion", "hi": "विसर्जन के दौरान"},
    "phase.Post-Visarjan": {"en": "One week after", "hi": "एक सप्ताह बाद"},
    "tr.help": {"en": "Dotted line = CPCB limit. A break in a line means no reading in that period.",
                "hi": "बिंदीदार रेखा = CPCB सीमा। रेखा में टूटन का अर्थ है उस अवधि में कोई माप नहीं।"},
    "tr.ph": {"en": "pH (6.5 to 8.5 is within limits)", "hi": "pH (6.5 से 8.5 सीमा के भीतर)"},
    "tr.lim.ph": {"en": "CPCB Class B range {v}", "hi": "CPCB श्रेणी-B दायरा {v}"},
    "c.period": {"en": "Period", "hi": "अवधि"},
    "c.ph": {"en": "pH", "hi": "pH"},
    "e.ph": {"en": "pH as recorded", "hi": "दर्ज pH"},
    "cmp.score": {"en": "Risk score by ghat (tap a bar to open it)", "hi": "घाट के अनुसार जोखिम स्कोर (खोलने के लिए बार चुनें)"},
    "sec.plan": {"en": "Where to send resources", "hi": "संसाधन कहाँ भेजें"},
    "plan.help": {"en": "How much each ghat needs aeration (low oxygen), cleaning (organic waste) and extra testing (data gaps).",
                  "hi": "हर घाट को कितनी वायुयन (कम ऑक्सीजन), सफ़ाई (जैविक कचरा) और अतिरिक्त जाँच (डेटा अंतर) चाहिए।"},
    "need.aeration": {"en": "Aeration", "hi": "वायुयन"},
    "need.cleaning": {"en": "Cleaning", "hi": "सफ़ाई"},
    "need.testing": {"en": "Testing", "hi": "जाँच"},
    "sec.caveats": {"en": "What this data does not cover", "hi": "यह डेटा क्या कवर नहीं करता"},
    "caveats.help": {"en": "Read this before acting on the ranking.", "hi": "रैंकिंग पर कार्रवाई से पहले इसे पढ़ें।"},
    "sec.verified": {"en": "Matches the organisers’ own totals: {do} of {dt} DO readings below 5 mg/L and {bod} of {bt} BOD readings above 3 mg/L.",
                     "hi": "आयोजकों के अपने आँकड़ों से मेल खाता है: {dt} में से {do} DO माप 5 mg/L से कम और {bt} में से {bod} BOD माप 3 mg/L से अधिक।"},
    "sec.map": {"en": "Where the ghats are", "hi": "घाट कहाँ हैं"},
    "map.help": {"en": "Colour = risk level, number = score. Tap a marker to open that ghat.",
                 "hi": "रंग = जोखिम स्तर, संख्या = स्कोर। किसी मार्कर पर टैप करके उस घाट को खोलें।"},
    "map.exact": {"en": "Position of a map feature with this ghat's name. Not field-verified.", "hi": "इस घाट के नाम वाली नक्शे की जगह की स्थिति। मौके पर सत्यापित नहीं।"},
    "map.approx": {"en": "Approximate position (centre of the lake or the locality). Not field-verified.",
                   "hi": "अनुमानित स्थिति (झील या मोहल्ले का केंद्र)। मौके पर सत्यापित नहीं।"},
    "map.unmapped": {"en": "Not shown on the map (location not confirmed): {names}.", "hi": "नक्शे पर नहीं दिखाए गए (स्थान की पुष्टि नहीं): {names}।"},
    "map.open": {"en": "Open details", "hi": "विवरण खोलें"},
    "map.offline": {"en": "The map could not be loaded (check the internet connection). The ranking below still works.",
                    "hi": "नक्शा लोड नहीं हो सका (इंटरनेट कनेक्शन जाँचें)। नीचे की रैंकिंग काम करती है।"},
    "sec.lakes": {"en": "Lake conditions since the 2025 festivals", "hi": "2025 के उत्सवों के बाद झील की स्थिति"},
    "lakes.help": {"en": "Monthly lake monitoring, April 2025 to March 2026: the newest measurements in the pack. Context only: these are lake stations, not the ghat, and they never change the score.",
                   "hi": "मासिक झील निगरानी, अप्रैल 2025 से मार्च 2026: पैक के सबसे नए माप। केवल संदर्भ के लिए: ये झील के स्टेशन हैं, घाट नहीं, और ये स्कोर नहीं बदलते।"},
    "lakes.chart": {"en": "Dissolved oxygen by month (mg/L)", "hi": "मासिक घुलित ऑक्सीजन (mg/L)"},
    "lakes.station": {"en": "Station", "hi": "स्टेशन"},
    "lakes.months": {"en": "Months", "hi": "महीने"},
    "lakes.do": {"en": "DO range · months below 5", "hi": "DO दायरा · 5 से कम वाले महीने"},
    "lakes.ph": {"en": "pH range · months outside 6.5-8.5", "hi": "pH दायरा · 6.5-8.5 के बाहर वाले महीने"},
    "lakes.bod": {"en": "BOD, 3 days at 27°C (max)", "hi": "BOD, 3 दिन 27°C पर (अधिकतम)"},
    "lakes.nearest": {"en": "nearest station", "hi": "निकटतम स्टेशन"},
    "lakes.none": {"en": "This ghat is not on the Upper or Lower Lake, so the lake monitoring in the pack does not cover it.",
                   "hi": "यह घाट ऊपरी या निचली झील पर नहीं है, इसलिए पैक की झील निगरानी इसे कवर नहीं करती।"},
    "lakes.bodnote": {"en": "BOD here is the 3-day, 27°C test, not the 5-day, 20°C test the 3 mg/L limit is defined for, so it is not judged against that limit.",
                      "hi": "यहाँ BOD 3-दिन, 27°C का परीक्षण है, न कि 5-दिन, 20°C वाला जिसके लिए 3 mg/L की सीमा तय है, इसलिए इसे उस सीमा से नहीं आँका गया।"},
    "lakes.nodata": {"en": "no reading", "hi": "कोई माप नहीं"},
    # --- value labels
    "lvl.High": {"en": "High", "hi": "उच्च"},
    "lvl.Medium": {"en": "Medium", "hi": "मध्यम"},
    "lvl.Low": {"en": "Low", "hi": "निम्न"},
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

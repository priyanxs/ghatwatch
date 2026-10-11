# GhatWatch

**Live site: https://ghatwatch.vercel.app**

Track 2 · Visarjan Ghat Watch · Claude Impact Lab × Cerebras Café Compute, Bhopal

**Team:** _add team name and members here_

**The one user:** a Bhopal Municipal Corporation officer who plans Durga visarjan (20 Oct 2026) and decides where to
send extra **cleaning, aeration and water testing**. GhatWatch turns three years of MPPCB test reports into a ranked
list of Bhopal's 7 immersion ghats, with the reason for each rank, the numbers behind it traced to the report and
page, and a short English + Hindi brief the officer can forward.

It ranks by **historical** records. It is not a live measurement and makes no claim about health effects.

## What it does

- **Ranks the 7 ghats** by a transparent score (breach rate 60%, severity 25%, impact of immersion 15%); the page shows each part.
- **Checks CPCB Class B** (outdoor bathing): DO ≥ 5 mg/L, BOD ≤ 3 mg/L, pH 6.5 to 8.5, for every ghat, festival and phase
  (before, during, one week after). Reproduces the organisers' own totals: **42 of 116** DO readings below 5, **100 of 112** BOD readings above 3.
- **Missing data is never clean.** Blank, `not sampled`, `*`, `**` and a missing festival table all count as missing and raise the risk.
  `BDL` / `ND` is read as "very low": a pass for BOD, no usable result for DO and pH.
- **Traceable.** Every reading shows its report and page and links to the MPPCB PDF at that page.
- **Resource plan.** Per ghat: how much it needs aeration (low oxygen), cleaning (organic waste) and extra testing (data gaps).
- **Honest about gaps.** A "What this data does not cover" panel is built from the data and the guide's caveats.
- **Latest lake conditions** (monthly, Apr 2025 to Mar 2026, the newest data in the pack) beside each ghat on the Upper or Lower Lake, as context that never changes the score.
- **Map** of the ghats with risk-coloured markers (positions are approximate, see below).
- **Bilingual.** Whole interface and the one-page PDF brief in English and Hindi, per ghat and for the whole city.
- **Also:** year-on-year trend per ghat, Durga Visarjan countdown, WhatsApp share, and a weekly public update (see below).

## Run it (5 steps)

```bash
git clone https://github.com/priyanxs/ghatwatch.git && cd ghatwatch
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn api.index:app --reload
# open http://localhost:8000
```

Deploy: import the repo on vercel.com/new. No build command needed.

## What works, and what doesn't

Works: everything above, on the real 2023 to 2025 data; falls back to clearly labelled demo data if the CSV is missing or broken.

Doesn't, or is limited:
- **Map positions are not field-verified.** The data has no coordinates. Positions come from OpenStreetMap lookups: only
  Prempura ghat is an exact feature; the others are the centre of their lake or locality. **Hathaikheda dam / kund** was not found, so it is off the map.
  Fix or add positions in `data/ghat_locations.csv` (`lat`, `lon`).
- **Score cut-offs** (High ≥ 45, Medium ≥ 30) are a starting point to agree with BMC, not an official standard.
- The lake monitoring covers only the Upper and Lower Lake stations (mostly water-supply intakes, not the ghats), May is blank, and its BOD is the 3-day, 27°C test, so it is not judged against the 3 mg/L limit.
- Only DO, BOD and pH have a Class B limit, so only they are scored. There is no coliform data.
- "Rani Kamlapati ghat / Kamla Park kund" may be two places (medium match confidence). Bairagarh and Malikhedi have no Durga 2025 table.
- Each festival is sampled only three times, so a short spike between samples can be missed.
- Weekly auto-posting is built but off until you connect an account (and it never posts demo data). Not tested against a live account.

## Data used

- `data/bhopal_ghats_2023_2025.csv`: the Track 2 dataset, from https://github.com/Laaaaksh/bhopal-impact-lab-2026 (`tracks/02-visarjan-ghat-watch`), extracted from the MPPCB reports below.
- Reports (MPPCB): [Ganesh and Durga Visarjan 2025](https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2025.pdf),
  [2024](https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2024.pdf),
  [Idol Immersion Report 2023 (CPCB format)](https://www.mppcb.mp.gov.in/proc/mon/Idol_immer._Report_23_CPCB.pdf).
- Lake monitoring: [Upper and Lower Lake monthly water quality 2025-26](https://xgn.mp.nic.in/File_Upload/MONITORING//Yearly%20Water%20Quality%20Status/2026/July/UPPER%20LAKE-2025-26..pdf), read from the copy in the pack, extracted by `scripts/extract_lake_monitoring.py` and checked against the PDF's own averages, maxima and minima.
- Limits: [CPCB water quality criteria](https://cpcb.gov.in/water-quality-criteria/), Class B.
- `data/ghat_locations.csv`: positions looked up in OpenStreetMap (© OpenStreetMap contributors, ODbL). Map tiles © OpenStreetMap contributors.
- Font: Noto Sans Devanagari (SIL OFL), bundled so the Hindi PDF works on a server.

No government system was logged into, scraped or written to.

## Layout

```
api/index.py     FastAPI backend (one Vercel Python function)
public/          static frontend: index.html, style.css, app.js (no build step)
utils/           data_loader, risk_engine, caveats, locations, i18n, pdf_generator, weekly, publish, sources
data/            the ghat readings, lake monitoring and ghat positions
scripts/         extract_lake_monitoring.py (needs `pip install pymupdf`; not used at runtime)
fonts/           bundled Devanagari font
```

## API

| route | returns |
| --- | --- |
| `GET /api/overview` | metrics, limits, weights, ranking, resource needs, period grid, caveats, sources |
| `GET /api/ghats/{id}` | summary, every reading with CPCB status, bilingual brief |
| `GET /api/ghats/{id}/brief.pdf` | one-page English + Hindi brief for a ghat |
| `GET /api/readiness.pdf` | one-page brief ranking all ghats |
| `GET /api/weekly-report` | this week's captions (preview, never posts) |
| `GET /api/cron/weekly-post` | cron-only; posts when configured |
| `GET /api/i18n` | interface strings (English / Hindi) |
| `GET /api/docs` | interactive API docs (local development only; disabled on Vercel) |

## Weekly public update (off by default)

A bilingual caption is written from the latest ranking, with three tips on avoiding common mistakes (rotating weekly).
Captions are fixed templates filled with real numbers, never AI-generated. Vercel Cron calls `/api/cron/weekly-post`
every Monday 09:00 IST. Nothing is posted unless these environment variables are set in Vercel (never in code):

| variable | purpose |
| --- | --- |
| `CRON_SECRET` | required; the endpoint is disabled without it |
| `POST_ENABLED=true` | master switch; otherwise a dry run |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | a Telegram channel or group |
| `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN` | a Mastodon account |
| `SOCIAL_WEBHOOK_URL` | any https webhook (Zapier, Make, IFTTT) to reach X, Facebook, LinkedIn, Instagram |

Demo data is never posted.

## Security

Read-only site, no logins or uploads. Strict Content-Security-Policy and other browser protections, escaped output, a locked-down weekly-post endpoint
(off by default, never posts demo data), pinned and audited dependencies. See `SECURITY.md`.

## Licence

MIT, see `LICENSE`.

# GhatWatch

**Live site: https://ghatwatch.vercel.app**

Visarjan water-quality decision assistant for BMC officers, Bhopal. Ranks the ghats by **historical**
water-quality records (CPCB Class B: DO ≥ 5 mg/L, BOD ≤ 3 mg/L). It is not a live safety measurement.
Missing data is never treated as clean water.

```
api/index.py     FastAPI backend (one Vercel Python function)
public/          static frontend: index.html, style.css, app.js (no build step)
utils/           data_loader, risk_engine, pdf_generator, i18n  (shared logic)
fonts/           bundled Noto Sans Devanagari, so the Hindi PDF works on servers
data/            put bhopal_water_quality.csv here (see data/README.md)
app.py           optional local Streamlit dashboard (not deployed)
```

## Features beyond the ranking

- **Weekly public update**: a bilingual caption written from the latest ranking, with three tips on avoiding
  common mistakes (rotating weekly), ready to copy or auto-post. Captions are fixed templates filled with real
  numbers, never AI-generated, so nothing invented can be posted.
- **Countdown** to Durga Visarjan (20 Oct 2026) and a **year-on-year trend** on every ghat.
- **City-wide one-page brief** (PDF, English + Hindi) ranking all ghats with each one's first action.
- **Share on WhatsApp**: a short forwardable message per ghat.

## Auto-posting the weekly update (off by default)

Vercel Cron calls `/api/cron/weekly-post` every Monday 09:00 IST. Nothing is posted unless you set these
environment variables in the Vercel project (never in code):

| variable | purpose |
| --- | --- |
| `CRON_SECRET` | required; the endpoint is disabled without it and rejects any other caller |
| `POST_ENABLED=true` | master switch; otherwise every run is a dry run |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | post to a Telegram channel or group |
| `MASTODON_BASE_URL`, `MASTODON_ACCESS_TOKEN` | post to a Mastodon account |
| `SOCIAL_WEBHOOK_URL` | any https webhook (Zapier, Make, IFTTT) to reach X, Facebook, LinkedIn, Instagram |

**Demo data is never posted**, even with everything enabled. Preview this week's captions at `/api/weekly-report`.

## API

| route | returns |
| --- | --- |
| `GET /api/health` | liveness, and whether Hindi PDF rendering is available |
| `GET /api/overview` | metrics, limits, score weights, ranking of all ghats |
| `GET /api/ghats/{ghat}` | summary, every reading with CPCB status, bilingual brief |
| `GET /api/ghats/{ghat}/brief.pdf` | one-page English + Hindi PDF brief |
| `GET /api/readiness.pdf` | one-page city-wide brief for all ghats |
| `GET /api/weekly-report` | this week's captions (preview, never posts) |
| `GET /api/cron/weekly-post` | cron-only; posts when configured (see above) |
| `GET /api/i18n` | interface strings (English / Hindi) |
| `GET /api/docs` | interactive API docs |

## Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn api.index:app --reload      # http://localhost:8000  (frontend + API)
.venv/bin/streamlit run app.py                # optional: the Streamlit version
```

## Deploy to Vercel

1. Add your data as `data/bhopal_water_quality.csv` (otherwise demo data is shown, clearly labelled).
2. Push this folder to a Git repository and import it at vercel.com/new, or run `npx vercel` here.
   No build command or framework preset is needed.
3. The Python version comes from `.python-version` (3.12). Dependencies come from `requirements.txt`.

Changing the data means redeploying: the CSV is read once per server instance.

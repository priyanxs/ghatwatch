# GhatWatch

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

## API

| route | returns |
| --- | --- |
| `GET /api/health` | liveness, and whether Hindi PDF rendering is available |
| `GET /api/overview` | metrics, limits, score weights, ranking of all ghats |
| `GET /api/ghats/{ghat}` | summary, every reading with CPCB status, bilingual brief |
| `GET /api/ghats/{ghat}/brief.pdf` | one-page English + Hindi PDF brief |
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

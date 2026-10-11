"""GhatWatch backend: a small FastAPI app that Vercel runs as one Python serverless function.

Endpoints (all GET, JSON unless noted):
    /api/health                      liveness check
    /api/i18n                        interface strings for the frontend (English + Hindi)
    /api/overview                    headline metrics, limits, score weights and the ranking of all ghats
    /api/ghats/{ghat}                one ghat: summary, every reading with CPCB status, bilingual brief
    /api/ghats/{ghat}/brief.pdf      one-page bilingual PDF brief (application/pdf)

All the scoring lives in ``utils/``; this file only exposes it. Locally, run
``uvicorn api.index:app`` and the static frontend in ``public/`` is served at ``/`` too. On
Vercel, ``public/`` is served by Vercel itself and only ``/api/*`` reaches this function.
"""
from __future__ import annotations

import math
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make `utils` importable inside the serverless function

import numpy as np  # noqa: E402
from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from utils import i18n  # noqa: E402
from utils import risk_engine as engine  # noqa: E402
from utils.data_loader import load_data  # noqa: E402
from utils.pdf_generator import build_pdf, hindi_available  # noqa: E402

app = FastAPI(title="GhatWatch API", version="1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

READING_COLUMNS = ["year", "phase", "do_raw", "bod_raw", "do_value", "bod_value",
                   "do_status", "bod_status", "source", "page"]


def clean(value):
    """Make pandas / numpy values JSON-safe: numpy scalars -> Python, NaN -> null."""
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


@lru_cache(maxsize=1)
def state():
    """Load, annotate and rank once per warm instance. The CSV only changes on redeploy."""
    result = load_data()
    return engine.annotate(result.df), engine.rank_ghats(result.df), result.is_mock, result.notes


def find_ghat(name: str):
    """Return ``(annotated rows, ranking row)`` for a ghat, or 404."""
    data, ranking, _, _ = state()
    match = ranking[ranking.ghat == name]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Unknown ghat: {name}")
    return data[data.ghat == name], match.iloc[0]


@app.get("/api/health")
def health():
    return {"status": "ok", "hindi_pdf": hindi_available()}


@app.get("/api/i18n")
def strings():
    return {"languages": i18n.LANGUAGES, "strings": i18n.STRINGS}


@app.get("/api/overview")
def overview():
    data, ranking, is_mock, notes = state()
    readings = len(data) * 2
    gaps = int((data.do_status == engine.NO_DATA).sum() + (data.bod_status == engine.NO_DATA).sum())
    breaches = int((data.do_status == engine.BREACH).sum() + (data.bod_status == engine.BREACH).sum())
    rows = [{**r, "ghat_hi": i18n.ghat_name(r["ghat"], "hi")} for r in ranking.to_dict("records")]
    return clean({
        "is_mock": is_mock,
        "notes": notes,
        "disclaimer": {"en": engine.DISCLAIMER_EN, "hi": engine.DISCLAIMER_HI},
        "metrics": {"ghats": len(ranking), "high_risk": int((ranking.risk_level == "High").sum()),
                    "breaches": breaches, "no_data_pct": round(100 * gaps / readings, 1)},
        "limits": {"do_min": engine.DO_MIN, "bod_max": engine.BOD_MAX},
        "weights": {"breach": engine.W_BREACH, "severity": engine.W_SEVERITY,
                    "deterioration": engine.W_DETERIORATION, "gap": engine.GAP_WEIGHT,
                    "high_at": engine.HIGH_AT, "medium_at": engine.MEDIUM_AT},
        "ranking": rows,
    })


@app.get("/api/ghats/{ghat}")
def ghat_detail(ghat: str):
    rows, summary = find_ghat(ghat)
    summary = summary.to_dict()
    readings = rows.sort_values(["year", "phase"], ascending=[False, False])[READING_COLUMNS]
    return clean({
        "ghat": ghat,
        "ghat_hi": i18n.ghat_name(ghat, "hi"),
        "rank": summary["rank"],
        "summary": summary,
        "readings": readings.to_dict("records"),
        "brief": engine.build_brief(ghat, summary),
    })


@app.get("/api/ghats/{ghat}/brief.pdf")
def ghat_brief_pdf(ghat: str):
    rows, summary = find_ghat(ghat)
    _, ranking, is_mock, _ = state()
    summary = summary.to_dict()
    try:
        pdf = build_pdf(ghat, summary, engine.build_brief(ghat, summary), rows,
                        int(summary["rank"]), len(ranking), is_mock)
    except Exception as exc:  # report a clean error instead of a bare 500 trace
        raise HTTPException(status_code=500, detail=f"Could not build the PDF brief: {exc}") from exc
    slug = re.sub(r"[^a-z0-9]+", "_", ghat.lower()).strip("_")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="ghatwatch_{slug}.pdf"'})


# Local development only: on Vercel the static frontend is served by the platform.
if not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="public")

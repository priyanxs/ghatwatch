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
from fastapi import FastAPI, Header, HTTPException  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from utils import i18n  # noqa: E402
from utils import risk_engine as engine  # noqa: E402
from utils.caveats import build_caveats  # noqa: E402
from utils.data_loader import PHASES, load_data  # noqa: E402
from utils.lakes import lake_for_water_body, load_lakes, nearest_station  # noqa: E402
from utils.locations import load_locations  # noqa: E402
from utils.pdf_generator import build_pdf, hindi_available  # noqa: E402
from utils import publish as social  # noqa: E402
from utils.pdf_generator import build_city_pdf  # noqa: E402
from utils.sources import REFERENCE_LINKS, SOURCE_REPORTS  # noqa: E402
from utils.weekly import build_weekly_report, days_left  # noqa: E402

app = FastAPI(title="GhatWatch API", version="1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

READING_COLUMNS = ["period", "year", "festival", "phase", "do_raw", "bod_raw", "ph_raw", "do_value", "bod_value", "ph_value",
                   "do_status", "bod_status", "ph_status", "source", "page", "source_url"]
PHASE_RANK = {p: i for i, p in enumerate(PHASES)}


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


def slugify(name: str) -> str:
    """URL-safe id for a ghat. Real names contain "/" and brackets, which cannot sit in a URL path."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def find_ghat(key: str):
    """Return ``(annotated rows, ranking row)`` for a ghat given its id (or its name), or 404."""
    data, ranking, _, _ = state()
    match = ranking[ranking.ghat.map(slugify) == slugify(key)]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Unknown ghat: {key}")
    name = match.iloc[0].ghat
    return data[data.ghat == name], match.iloc[0]


def trends(data) -> dict:
    """Per ghat: did the latest year get better or worse than the year before (share of tested readings that breach)?"""
    years = sorted(int(y) for y in data.year.unique())
    out = {}
    for ghat, g in data.groupby("ghat"):
        rates = []
        for y in years[-2:]:
            rows = g[g.year == y]
            tested = sum(int((rows[f"{p}_status"] != engine.NO_DATA).sum()) for p in engine.PARAMS)
            breaches = sum(int((rows[f"{p}_status"] == engine.BREACH).sum()) for p in engine.PARAMS)
            rates.append(breaches / tested if tested else None)
        if len(rates) < 2 or None in rates:
            out[ghat] = "na"
        else:
            diff = rates[1] - rates[0]
            out[ghat] = "worse" if diff > 0.05 else "better" if diff < -0.05 else "same"
    return out


def timeline(data) -> dict:
    """Per ghat, period and phase: one overall status for the period-by-period grid.

    BREACH if DO, BOD or pH breached; otherwise NO DATA if any is missing or inconclusive; otherwise PASS.
    Missing data therefore never shows up as a pass.
    """
    out: dict = {}
    for r in data.itertuples():
        out.setdefault(r.ghat, {}).setdefault(r.period, {})[r.phase] = engine.row_status(r)
    return out


@app.get("/api/health")
def health():
    return {"status": "ok", "hindi_pdf": hindi_available()}


@app.get("/api/i18n")
def strings():
    return {"languages": i18n.LANGUAGES, "strings": i18n.STRINGS}


@app.get("/api/overview")
def overview():
    data, ranking, is_mock, notes = state()
    # Headline totals cover every scored reading: DO, BOD and pH for each ghat / period / phase.
    readings = len(data) * len(engine.PARAMS)
    gaps = sum(int((data[f"{p}_status"] == engine.NO_DATA).sum()) for p in engine.PARAMS)
    breaches = sum(int((data[f"{p}_status"] == engine.BREACH).sum()) for p in engine.PARAMS)
    trend, places = trends(data), load_locations()
    rows = [{**r, "location": places.get(r["ghat"]), "id": slugify(r["ghat"]), "ghat_hi": i18n.ghat_name(r["ghat"], "hi"), "trend": trend[r["ghat"]]} for r in ranking.to_dict("records")]
    return clean({
        "days_left": days_left(),
        "as_of": __import__("datetime").date.today().isoformat(),
        "sources": {"reports": SOURCE_REPORTS, "references": REFERENCE_LINKS},
        "periods": [{"key": p, "year": int(y), "festival": f} for p, y, f in
                    data[["period", "year", "festival", "p_order"]].drop_duplicates().sort_values("p_order")[["period", "year", "festival"]].itertuples(index=False)],
        "timeline": timeline(data),
        "caveats": build_caveats(data),
        "lakes": load_lakes(),
        "is_mock": is_mock,
        "notes": notes,
        "disclaimer": {"en": engine.DISCLAIMER_EN, "hi": engine.DISCLAIMER_HI},
        "metrics": {"ghats": len(ranking), "high_risk": int((ranking.risk_level == "High").sum()),
                    "breaches": breaches, "no_data_pct": round(100 * gaps / readings, 1)},
        "limits": {"do_min": engine.DO_MIN, "bod_max": engine.BOD_MAX, "ph_min": engine.PH_MIN, "ph_max": engine.PH_MAX},
        "weights": {"breach": engine.W_BREACH, "severity": engine.W_SEVERITY,
                    "deterioration": engine.W_DETERIORATION, "gap": engine.GAP_WEIGHT,
                    "high_at": engine.HIGH_AT, "medium_at": engine.MEDIUM_AT},
        "ranking": rows,
    })


@app.get("/api/ghats/{ghat}")
def ghat_detail(ghat: str):
    rows, summary = find_ghat(ghat)
    summary = summary.to_dict()
    ghat = summary["ghat"]
    readings = (rows.assign(_ph=rows["phase"].map(PHASE_RANK)).sort_values(["p_order", "_ph"], ascending=[False, True])[READING_COLUMNS])
    return clean({
        "ghat": ghat,
        "id": slugify(ghat),
        "ghat_hi": i18n.ghat_name(ghat, "hi"),
        "rank": summary["rank"],
        "water_body": next((x for x in rows["water_body"] if x), ""),
        "lake": lake_for_water_body(next((x for x in rows["water_body"] if x), "")),
        "nearest_station": nearest_station(ghat, [s for s in load_lakes()["stations"] if s["lake"] == lake_for_water_body(next((x for x in rows["water_body"] if x), ""))]),
        "confidence": next((x for x in rows["confidence"] if x), ""),
        "summary": summary,
        "readings": readings.to_dict("records"),
        "brief": engine.build_brief(ghat, summary),
    })


@app.get("/api/ghats/{ghat}/brief.pdf")
def ghat_brief_pdf(ghat: str):
    rows, summary = find_ghat(ghat)
    _, ranking, is_mock, _ = state()
    summary = summary.to_dict()
    ghat = summary["ghat"]
    try:
        pdf = build_pdf(ghat, summary, engine.build_brief(ghat, summary), rows,
                        int(summary["rank"]), len(ranking), is_mock)
    except Exception as exc:  # report a clean error instead of a bare 500 trace
        raise HTTPException(status_code=500, detail=f"Could not build the PDF brief: {exc}") from exc
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="ghatwatch_{slugify(ghat).replace("-", "_")}.pdf"'})


@app.get("/api/readiness.pdf")
def readiness_pdf():
    """One page for the whole city: every ghat ranked, with its first recommended action in both languages."""
    _, ranking, is_mock, _ = state()
    rows = []
    for r in ranking.to_dict("records"):
        brief = engine.build_brief(r["ghat"], r)
        rows.append({**r, "ghat_hi": i18n.ghat_name(r["ghat"], "hi"),
                     "action_en": brief["en"]["actions"][0], "action_hi": brief["hi"]["actions"][0]})
    return Response(build_city_pdf(rows, is_mock), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="ghatwatch_city_brief.pdf"'})


def auto_post_status(is_mock: bool) -> dict:
    return {"enabled": social.enabled(), "channels": social.configured_channels(), "blocked_demo": is_mock}


@app.get("/api/weekly-report")
def weekly_report():
    """Preview of this week's captions (English + Hindi). Never posts anything."""
    _, ranking, is_mock, _ = state()
    return {**build_weekly_report(ranking, is_mock), "auto_post": auto_post_status(is_mock)}


@app.get("/api/cron/weekly-post")
def weekly_post(authorization: str | None = Header(default=None)):
    """Called by Vercel Cron every Monday. Posts only when CRON_SECRET matches, posting is enabled and the data is real."""
    secret = os.environ.get("CRON_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET is not set, so this endpoint is disabled.")
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    _, ranking, is_mock, _ = state()
    report = build_weekly_report(ranking, is_mock)
    status = auto_post_status(is_mock)
    if is_mock:
        return {"posted": False, "reason": "demo data is never posted", **status}
    if not status["enabled"] or not status["channels"]:
        return {"posted": False, "reason": "dry run: POST_ENABLED is not true or no channel is configured", **status}
    results = social.publish(report)
    return {"posted": any(r["ok"] for r in results), "results": results, "date": report["date"]}


# Local development only: on Vercel the static frontend is served by the platform.
if not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="public")

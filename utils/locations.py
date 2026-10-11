"""Where each ghat is, for the map. Read from ``data/ghat_locations.csv`` (lat, lon, how sure we are).

The readings carry no coordinates, so positions come from OpenStreetMap lookups and are not field-verified.
A ghat with no coordinates simply stays off the map and is listed as "not confirmed". Never raises.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

LOCATIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "ghat_locations.csv"
BHOPAL_LAT, BHOPAL_LON = (22.9, 23.5), (77.1, 77.7)   # anything outside this box is a typo, not a Bhopal ghat


@lru_cache(maxsize=4)
def load_locations(path: Path = LOCATIONS_PATH) -> dict[str, dict]:
    """``{ghat name: {lat, lon, precision, basis}}`` for rows with usable coordinates."""
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return {}
    out = {}
    for r in df.itertuples():
        try:
            lat, lon = float(r.lat), float(r.lon)
        except (ValueError, TypeError):
            continue
        if BHOPAL_LAT[0] <= lat <= BHOPAL_LAT[1] and BHOPAL_LON[0] <= lon <= BHOPAL_LON[1]:
            out[r.ghat.strip()] = {"lat": lat, "lon": lon, "precision": r.precision.strip() or "approximate", "basis": r.basis.strip()}
    return out

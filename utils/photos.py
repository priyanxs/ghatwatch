"""Reference photos of the water body a ghat sits on, with their credits.

The readings come with no pictures, and a photo of an individual ghat with an open licence could not be found, so each
ghat on the Upper or Lower Lake shows an openly licensed photo of *that lake* (from Wikimedia Commons), clearly captioned as
a reference and not as the ghat itself. Ghats on other water bodies show no photo rather than a wrong one. The catalogue is
``data/ghat_photos.csv``; the images are in ``public/images/ghats``. Never raises.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

PHOTOS_PATH = Path(__file__).resolve().parent.parent / "data" / "ghat_photos.csv"


@lru_cache(maxsize=2)
def load_photos(path: Path = PHOTOS_PATH) -> dict[str, dict]:
    """``{lake: {image, body_en, body_hi, author, license, license_url, source_url}}``."""
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except Exception:
        return {}
    return {r["lake"]: {k: r[k] for k in ("image", "body_en", "body_hi", "author", "license", "license_url", "source_url")}
            for r in df.to_dict("records") if r.get("image", "").startswith("/images/")}

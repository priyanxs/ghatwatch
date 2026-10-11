"""Today's date in India. Vercel runs in UTC, so between midnight and 05:30 IST plain ``date.today()`` is a day behind."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def today_ist() -> date:
    return datetime.now(IST).date()

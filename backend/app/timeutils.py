from datetime import datetime, timezone
from typing import Optional


def as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalise a datetime read from the DB to timezone-aware UTC.

    Columns are declared DateTime(timezone=True). Postgres (production)
    returns tz-aware values, but SQLite (local dev) has no timezone storage
    and returns naive ones. Comparing a naive value against
    datetime.now(timezone.utc) raises:

        TypeError: can't compare offset-naive and offset-aware datetimes

    Values are always written as UTC, so treating a naive value as UTC is
    correct rather than a guess.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

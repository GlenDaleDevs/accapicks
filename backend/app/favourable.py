"""Favourable Matchups cache.

The model fetches five season CSVs plus upcoming fixtures, which is far too
slow to do on a request. A background task refreshes it periodically and the
endpoint serves whatever is cached — including an empty result, which is a
legitimate answer ("no strong mismatches this round") rather than an error.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .predictionmodel.matchups import find_favourable_matchups

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 6 * 60 * 60  # ladder and fixtures both move slowly
RETRY_INTERVAL_SECONDS = 15 * 60
FIXTURE_WINDOW_DAYS = 8

# Only surface genuinely lopsided ties. A round that says "nothing strong this
# week" is more credible than one that always serves up ten.
MIN_DIFFERENTIAL = 0.75

_cache = {
    "generated_at": None,
    "season": None,
    "metric": None,
    "threshold": MIN_DIFFERENTIAL,
    "fixtures": [],
    "error": None,
}


def _flatten(report):
    """Flatten the per-league report into one threshold-filtered list."""
    rows = []
    for league in report.get("leagues", {}).values():
        for m in league.get("matchups", []):
            if abs(m.get("differential", 0)) < MIN_DIFFERENTIAL:
                continue
            rows.append({
                "event_id": m["event_id"],
                "commence_time": m["commence_time"],
                "sport_key": _odds_key(m["div"]),
                "div_name": m["div_name"],
                "favours": m["favours"],
                "differential": m["differential"],
                "home": _side(m["home"]),
                "away": _side(m["away"]),
            })
    # Widest gap first, so the strongest signal leads.
    rows.sort(key=lambda r: abs(r["differential"]), reverse=True)
    return rows


def _side(side):
    """Only the fields the card shows. Deliberately no probability: the tab
    states records and lets the reader draw the conclusion."""
    return {
        "team": side["team"],
        "won": side["won"],
        "drawn": side["drawn"],
        "lost": side["lost"],
        "div_name": side["div_name"],
    }


def _odds_key(div_code):
    from .predictionmodel.config import DIVISION_BY_CODE
    return DIVISION_BY_CODE.get(div_code, {}).get("odds_key")


def get_cached():
    return dict(_cache)


def refresh_once():
    """Synchronous refresh. Raises nothing — failures are recorded in the cache."""
    try:
        report = find_favourable_matchups(
            days_ahead=FIXTURE_WINDOW_DAYS,
            strict=False,  # a name we can't resolve must not blank the whole tab
        )
    except Exception as exc:
        logger.warning("Favourable matchups refresh failed: %s", exc)
        _cache["error"] = "unavailable"
        return

    _cache.update({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # Surfaced so the UI can say "based on last season's home/away form"
        # while the ladder still comes from the finished season.
        "season": report.get("season"),
        "metric": report.get("metric"),
        "threshold": MIN_DIFFERENTIAL,
        "fixtures": _flatten(report),
        "error": None,
    })
    logger.info(
        "Favourable matchups refreshed: %d above threshold from %d fixtures",
        len(_cache["fixtures"]), report.get("fixtures_evaluated", 0),
    )


async def refresh_favourable_matchups():
    """Background task. Retries sooner after a failure than a success."""
    while True:
        await asyncio.to_thread(refresh_once)
        delay = RETRY_INTERVAL_SECONDS if _cache["error"] else REFRESH_INTERVAL_SECONDS
        await asyncio.sleep(delay)

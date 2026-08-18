"""League tables for the Form tab.

Overall, home-only and away-only standings for the four divisions AccaPicks
carries fixtures for, built from the same football-data.co.uk results the
ladder uses. Five CSV fetches is far too slow for a request, so a background
task refreshes into this cache and the endpoint serves whatever is there.

A finished season never changes, so it is built once and kept. The current
season is rebuilt on the same slow tick as its source file's TTL.
"""

import asyncio
import logging
from datetime import datetime, timezone

from .predictionmodel.config import (CURRENT_SEASON, DIVISION_BY_CODE,
                                     LADDER_SEASON, TARGET_DIVISIONS)
from .predictionmodel.footballdata import fetch_results
from .predictionmodel.ladder import build_division_tables, rank_table

logger = logging.getLogger(__name__)

# Season codes are never exposed as query params — the client asks for
# "current" or "last" and the mapping lives here.
SEASONS = {"current": CURRENT_SEASON, "last": LADDER_SEASON}

REFRESH_INTERVAL_SECONDS = 6 * 60 * 60
RETRY_INTERVAL_SECONDS = 15 * 60

COUNTING_FIELDS = ("played", "won", "drawn", "lost", "gf", "ga")

_cache = {
    key: {"season": code, "generated_at": None, "leagues": [], "ready": False}
    for key, code in SEASONS.items()
}


def _overall(home_table, away_table):
    """One combined table from the home and away splits."""
    merged = {}
    for entry in list(home_table) + list(away_table):
        row = merged.setdefault(entry["team"], {"team": entry["team"], **{f: 0 for f in COUNTING_FIELDS}})
        for field in COUNTING_FIELDS:
            row[field] += entry[field]

    for row in merged.values():
        row["gd"] = row["gf"] - row["ga"]
        row["points"] = row["won"] * 3 + row["drawn"]
    return list(merged.values())


def _serialise(table):
    """Ranked rows trimmed to what the table renders."""
    return [
        {
            "pos": entry["div_rank"],
            "team": entry["team"],
            "played": entry["played"],
            "won": entry["won"],
            "drawn": entry["drawn"],
            "lost": entry["lost"],
            "gf": entry["gf"],
            "ga": entry["ga"],
            "gd": entry["gd"],
            "points": entry["points"],
        }
        for entry in rank_table(table)
    ]


def _build_league(season_code, div_code):
    division = DIVISION_BY_CODE[div_code]
    league = {"code": div_code, "name": division["name"],
              "overall": [], "home": [], "away": [], "error": None}

    try:
        rows = fetch_results(season_code, div_code)
    except Exception as exc:
        # A season's file doesn't exist until its first results are published,
        # so an early-August miss is expected rather than broken.
        logger.info("No standings for %s %s: %s", season_code, div_code, exc)
        league["error"] = "unavailable"
        return league

    home_table, away_table = build_division_tables(rows)
    league["overall"] = _serialise(_overall(home_table, away_table))
    league["home"] = _serialise(home_table)
    league["away"] = _serialise(away_table)
    return league


def get_cached(key):
    return dict(_cache[key])


def refresh_once(key):
    """Synchronous rebuild of one season. Never raises — a division that can't
    be fetched is marked unavailable and the rest still render."""
    season_code = SEASONS[key]
    leagues = [_build_league(season_code, div_code) for div_code in TARGET_DIVISIONS]

    _cache[key] = {
        "season": season_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "leagues": leagues,
        "ready": True,
    }
    logger.info(
        "Standings refreshed for %s: %d/%d divisions",
        season_code,
        sum(1 for lg in leagues if not lg["error"]),
        len(leagues),
    )


async def refresh_standings():
    """Background task. The finished season is immutable, so it is built once
    and then left alone; only the current season is re-fetched."""
    await asyncio.to_thread(refresh_once, "last")

    while True:
        await asyncio.to_thread(refresh_once, "current")
        # A division still missing its file is worth retrying sooner.
        stale = any(lg["error"] for lg in _cache["current"]["leagues"])
        await asyncio.sleep(RETRY_INTERVAL_SECONDS if stale else REFRESH_INTERVAL_SECONDS)

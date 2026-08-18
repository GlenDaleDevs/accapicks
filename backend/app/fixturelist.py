"""Fixtures and results by week, for the Fixtures tab.

Two feeds, one shape. Upcoming fixtures come from The-Odds-API /events (zero
credits, about a round ahead); everything already played comes from the
football-data.co.uk results the Form tables are built from. Both are bucketed
into Monday-to-Sunday weeks in UK time, so "last week's results" and "this
week's fixtures" are the same kind of thing to the client.

Team names are reconciled to the football-data vocabulary, so a club doesn't
change name between a result and a fixture — or between here and the tables.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from . import odds_api
from .predictionmodel import names
from .predictionmodel.config import (CURRENT_SEASON, DIVISION_BY_CODE,
                                     TARGET_DIVISIONS)
from .predictionmodel.footballdata import fetch_results
from .weekblocks import UK_TZ

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 60 * 60  # the events cache has the same TTL
RETRY_INTERVAL_SECONDS = 10 * 60

_cache = {"generated_at": None, "weeks": [], "by_week": {}, "ready": False}


def _week_start(day):
    """The Monday of that day's week."""
    return day - timedelta(days=day.weekday())


def _week_label(monday):
    sunday = monday + timedelta(days=6)
    if monday.month == sunday.month:
        return f"{monday.day}–{sunday.day} {monday.strftime('%b')}"
    return (f"{monday.day} {monday.strftime('%b')} – "
            f"{sunday.day} {sunday.strftime('%b')}")


def _uk_date(iso):
    """Kickoff dates are bucketed in UK time — a 20:00 kickoff must not land on
    the next day just because the API speaks UTC."""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UK_TZ).date()
    except (AttributeError, ValueError):
        return None


def _canonical(name, index):
    """Odds-API club name -> football-data name, so both feeds agree."""
    resolved = names.resolve(name, index)
    if resolved:
        return resolved
    # Early season the index is thin (a club with no results yet isn't in it),
    # so fall back to the alias table and then to the name as given.
    return names.ALIASES.get(name, name)


def _played_matches(div_code, buckets):
    """Results already in the football-data file, bucketed by week.

    Returns the fixtures seen per week (so the same tie can't be listed again
    as upcoming) and the division's football-data club vocabulary.
    """
    try:
        rows = fetch_results(CURRENT_SEASON, div_code)
    except Exception as exc:
        logger.info("No results yet for %s %s: %s", CURRENT_SEASON, div_code, exc)
        return defaultdict(set), set()

    seen = defaultdict(set)
    teams = set()
    for row in rows:
        played_on = row["played_on"]
        if not played_on:
            continue
        monday = _week_start(played_on)
        buckets[monday][div_code].append({
            "date": played_on.isoformat(),
            "kickoff": None,
            "home": row["home"],
            "away": row["away"],
            "home_goals": row["home_goals"],
            "away_goals": row["away_goals"],
            "played": True,
        })
        seen[monday].add((row["home"], row["away"]))
        teams.update((row["home"], row["away"]))

    return seen, teams


def _upcoming_matches(div_code, buckets, seen, index):
    """Fixtures still to be played, from the free /events endpoint."""
    sport_key = DIVISION_BY_CODE[div_code]["odds_key"]
    if not sport_key:
        return

    for event in odds_api.get_events(sport_key):
        commence = event.get("commence_time")
        day = _uk_date(commence)
        if not day:
            continue

        home = _canonical(event.get("home_team"), index)
        away = _canonical(event.get("away_team"), index)
        monday = _week_start(day)
        # A fixture that has just been played can still be listed as upcoming.
        if (home, away) in seen.get(monday, set()):
            continue

        buckets[monday][div_code].append({
            "date": day.isoformat(),
            "kickoff": commence,
            "home": home,
            "away": away,
            "home_goals": None,
            "away_goals": None,
            "played": False,
        })


def _sorted_leagues(by_div):
    """Every target division, in ladder order, with its matches in kickoff
    order. Divisions with nothing on are kept so the league chips don't move."""
    leagues = []
    for code in TARGET_DIVISIONS:
        matches = sorted(by_div.get(code, []),
                         key=lambda m: (m["date"], m["kickoff"] or "", m["home"]))
        leagues.append({
            "code": code,
            "name": DIVISION_BY_CODE[code]["name"],
            "matches": matches,
        })
    return leagues


def refresh_once():
    """Rebuild every week. Never raises — a feed that fails leaves its matches
    out rather than emptying the tab."""
    buckets = defaultdict(lambda: defaultdict(list))

    for div_code in TARGET_DIVISIONS:
        seen, teams = _played_matches(div_code, buckets)
        _upcoming_matches(div_code, buckets, seen, names.build_index(teams))

    today = datetime.now(UK_TZ).date()
    this_monday = _week_start(today)

    weeks = [
        {"key": monday.isoformat(), "label": _week_label(monday),
         "upcoming": monday >= this_monday}
        for monday in sorted(buckets)
    ]

    _cache.update({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weeks": weeks,
        "by_week": {monday.isoformat(): _sorted_leagues(by_div)
                    for monday, by_div in buckets.items()},
        "ready": True,
    })
    logger.info("Fixture list refreshed: %d weeks", len(weeks))


def default_week():
    """This week if it has anything on, otherwise the next week that does —
    landing on an empty week during an international break helps nobody."""
    weeks = _cache["weeks"]
    if not weeks:
        return None
    this_monday = _week_start(datetime.now(UK_TZ).date()).isoformat()
    for week in weeks:
        if week["key"] >= this_monday:
            return week["key"]
    return weeks[-1]["key"]


def get_week(key=None):
    key = key or default_week()
    return {
        "generated_at": _cache["generated_at"],
        "ready": _cache["ready"],
        "weeks": _cache["weeks"],
        "week": key,
        "leagues": _cache["by_week"].get(key, _sorted_leagues({})),
    }


async def refresh_fixture_list():
    """Background task. Retries sooner while nothing has been built."""
    while True:
        try:
            await asyncio.to_thread(refresh_once)
        except Exception as exc:
            logger.error("Fixture list refresh failed: %s", exc)
        delay = REFRESH_INTERVAL_SECONDS if _cache["ready"] else RETRY_INTERVAL_SECONDS
        await asyncio.sleep(delay)

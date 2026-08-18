"""Fixtures and results by week, for the Fixtures tab.

Two feeds, one shape. Upcoming fixtures come from The-Odds-API /events (zero
credits, about a round ahead); everything already played comes from the
football-data.co.uk results the Form tables are built from. Both are bucketed
into game weeks in UK time, so "last week's results" and "this week's
fixtures" are the same kind of thing to the client.

Team names are reconciled to the football-data vocabulary, so a club doesn't
change name between a result and a fixture — or between here and the tables.

Each division also carries a per-club league position and last-five form,
computed from the same results, so a row can say where a side sits and how it
has been going without a second request.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from . import odds_api
from .predictionmodel import names
from .predictionmodel.config import (CURRENT_SEASON, DIVISION_BY_CODE,
                                     TARGET_DIVISIONS)
from .predictionmodel.footballdata import fetch_results
from .standings import overall_table
from .weekblocks import UK_TZ

logger = logging.getLogger(__name__)

TUESDAY = 1
FORM_LENGTH = 5

REFRESH_INTERVAL_SECONDS = 60 * 60  # the events cache has the same TTL
RETRY_INTERVAL_SECONDS = 10 * 60

_cache = {"generated_at": None, "weeks": [], "by_week": {}, "teams": {},
          "ready": False}


def _week_start(day):
    """The Tuesday that opens this day's game week.

    A round is Thu/Fri/Sat/Sun/Mon around its Saturday — the same shape
    weekblocks.WEEKEND_OFFSETS uses for accas — so the window has to run
    Tuesday to Monday. A calendar week would split a round in two, putting a
    Monday night game with the following Saturday's fixtures instead of the
    one it was played alongside.
    """
    return day - timedelta(days=(day.weekday() - TUESDAY) % 7)


def _day_label(day):
    return f"{day.day} {day.strftime('%b')}"


def _week_label(dates):
    """The span the week's fixtures actually cover, not the whole window —
    "15–17 Aug" says more than the Tuesday the bucket happens to start on."""
    first, last = min(dates), max(dates)
    if first == last:
        return _day_label(first)
    if first.month == last.month:
        return f"{first.day}–{last.day} {first.strftime('%b')}"
    return f"{_day_label(first)} – {_day_label(last)}"


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


def _fetch_rows(div_code):
    try:
        return fetch_results(CURRENT_SEASON, div_code)
    except Exception as exc:
        logger.info("No results yet for %s %s: %s", CURRENT_SEASON, div_code, exc)
        return []


def _outcome(scored, conceded):
    if scored > conceded:
        return "W"
    return "L" if scored < conceded else "D"


def _team_stats(rows):
    """{club: {"pos": int|None, "form": ["W", "D", ...]}} for one division.

    Form is oldest to newest, capped at the last five, so the rightmost circle
    is the most recent result.
    """
    position = {row["team"]: row["pos"] for row in overall_table(rows)} if rows else {}

    form = defaultdict(list)
    for row in sorted(rows, key=lambda r: r["played_on"] or date.min):
        form[row["home"]].append(_outcome(row["home_goals"], row["away_goals"]))
        form[row["away"]].append(_outcome(row["away_goals"], row["home_goals"]))

    return {
        team: {"pos": position.get(team), "form": form[team][-FORM_LENGTH:]}
        for team in set(position) | set(form)
    }


def _played_matches(rows, div_code, buckets):
    """Bucket results by week.

    Returns the fixtures seen per week, so the same tie can't be listed again
    as upcoming, and the division's football-data club vocabulary.
    """
    seen = defaultdict(set)
    teams = set()
    for row in rows:
        played_on = row["played_on"]
        if not played_on:
            continue
        week = _week_start(played_on)
        buckets[week][div_code].append({
            "date": played_on.isoformat(),
            "kickoff": None,
            "home": row["home"],
            "away": row["away"],
            "home_goals": row["home_goals"],
            "away_goals": row["away_goals"],
            "played": True,
        })
        seen[week].add((row["home"], row["away"]))
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
        week = _week_start(day)
        # A fixture that has just been played can still be listed as upcoming.
        if (home, away) in seen.get(week, set()):
            continue

        buckets[week][div_code].append({
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

    stats = {}
    for div_code in TARGET_DIVISIONS:
        rows = _fetch_rows(div_code)
        seen, teams = _played_matches(rows, div_code, buckets)
        _upcoming_matches(div_code, buckets, seen, names.build_index(teams))
        stats[div_code] = _team_stats(rows)

    this_week = _week_start(datetime.now(UK_TZ).date())

    weeks = []
    for start, by_div in sorted(buckets.items()):
        dates = [date.fromisoformat(m["date"])
                 for matches in by_div.values() for m in matches]
        weeks.append({
            "key": start.isoformat(),
            "label": _week_label(dates) if dates else _day_label(start),
            "upcoming": start >= this_week,
        })

    _cache.update({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weeks": weeks,
        "by_week": {start.isoformat(): _sorted_leagues(by_div)
                    for start, by_div in buckets.items()},
        # One table per division rather than per week: a club's position is the
        # same whichever week is on screen, so it is stored once.
        "teams": stats,
        "ready": True,
    })
    logger.info("Fixture list refreshed: %d weeks", len(weeks))


def default_week():
    """This week if it has anything on, otherwise the next week that does —
    landing on an empty week during an international break helps nobody."""
    weeks = _cache["weeks"]
    if not weeks:
        return None
    this_week = _week_start(datetime.now(UK_TZ).date()).isoformat()
    for week in weeks:
        if week["key"] >= this_week:
            return week["key"]
    return weeks[-1]["key"]


def get_week(key=None):
    key = key or default_week()
    leagues = [
        {**league, "teams": _cache["teams"].get(league["code"], {})}
        for league in _cache["by_week"].get(key, _sorted_leagues({}))
    ]
    return {
        "generated_at": _cache["generated_at"],
        "ready": _cache["ready"],
        "weeks": _cache["weeks"],
        "week": key,
        "leagues": leagues,
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

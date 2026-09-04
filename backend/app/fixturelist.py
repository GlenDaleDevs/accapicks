"""Fixtures and results by week, for the Fixtures tab.

Two feeds, one shape. Upcoming fixtures come from The-Odds-API /events (zero
credits, about a round ahead); everything already played comes from the
football-data.co.uk results the Form tables are built from. Both are bucketed
into game weeks in UK time, so "last week's results" and "this week's
fixtures" are the same kind of thing to the client.

Team names are reconciled to the football-data vocabulary, so a club doesn't
change name between a result and a fixture — or between here and the tables.

Each division also carries a per-club league position and last-five trackers —
results, both teams to score, and over 2.5 goals — each split three ways into
overall, home-only and away-only, computed from the same results, so a row can
say where a side sits and how it has been going without a second request.
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

# The four covered divisions plus the National League, in ladder order, for
# hunting down a moved club's actual last-season division. Index in this list
# doubles as tier (0 = top), which is all `classify_move` needs.
SEARCH_DIVISIONS = list(TARGET_DIVISIONS) + ["EC"]

REFRESH_INTERVAL_SECONDS = 60 * 60  # the events cache has the same TTL
RETRY_INTERVAL_SECONDS = 10 * 60

_cache = {"generated_at": None, "weeks": [], "by_week": {}, "teams": {},
          "ready": False}


def _week_start(day):
    """The date that opens this day's game week.

    Two kinds of week, kept apart so a midweek round and the following weekend
    don't share a bucket (which showed a team twice):
      - Fri/Sat/Sun/Mon → the weekend's Friday. A Monday-night game stays with
        the weekend it was played alongside, not the next one.
      - Tue/Wed/Thu → the midweek round's Tuesday.
    Thursday sits with midweek here — a weekend acca never includes a Thursday
    (weekblocks.WEEKEND_OFFSETS is Fri/Sun/Mon), so it's display-only either way.

    MIRRORED in src/components/FixturesTab.jsx weekKeyFor — change both together
    (JS getDay() is Sun=0..Sat=6, so it converts to this Mon=0 convention first).
    """
    wd = day.weekday()  # Mon=0 .. Sun=6
    back = 3 if wd == 0 else wd - 4 if wd >= 4 else wd - 1
    return day - timedelta(days=back)


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
    # A silent miss renders exactly like "no games played yet", so say so —
    # one refresh with a full index enumerates every gap in the alias table.
    if index:
        logger.warning("Unresolved club name %r — check names.ALIASES", name)
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


def _last_five(entries):
    """The three trackers over the most recent five of these matches.

    Sliced before splitting so all three describe the same five games — flick
    between them and you are comparing like with like.
    """
    recent = entries[-FORM_LENGTH:]
    return {
        "results": [result for _, result, _, _ in recent],
        "btts": [btts for _, _, btts, _ in recent],
        "over25": [over for _, _, _, over in recent],
    }


def _team_stats(rows):
    """Per-club position and last-five trackers for one division.

    {club: {"pos": int|None,
            "overall": {"results": [...], "btts": [...], "over25": [...]},
            "home": {...}, "away": {...}}}

    Home and away are the same three trackers over that club's home-only or
    away-only matches, which is a different last five from the overall one.
    """
    position = {row["team"]: row["pos"] for row in overall_table(rows)} if rows else {}

    history = defaultdict(list)
    for row in sorted(rows, key=lambda r: r["played_on"] or date.min):
        home_goals, away_goals = row["home_goals"], row["away_goals"]
        # Y/N rather than booleans: the client colours a tracker the same way
        # whichever one it is showing.
        btts = "Y" if home_goals > 0 and away_goals > 0 else "N"
        over25 = "Y" if home_goals + away_goals > 2 else "N"

        history[row["home"]].append(
            ("home", _outcome(home_goals, away_goals), btts, over25))
        history[row["away"]].append(
            ("away", _outcome(away_goals, home_goals), btts, over25))

    stats = {}
    for team in set(position) | set(history):
        played = history[team]
        stats[team] = {
            "pos": position.get(team),
            "overall": _last_five(played),
            "home": _last_five([e for e in played if e[0] == "home"]),
            "away": _last_five([e for e in played if e[0] == "away"]),
        }
    return stats


def _resolve_target(name):
    """Normalised forms to match a row's team name against: the name as given,
    and its alias-mapped form, so a raw odds-API name still matches
    football-data's vocabulary even for a club with no fixture-list index
    entry to resolve through (a promoted side with no games yet, say)."""
    variants = {names.normalise(name)}
    alias = names.ALIASES.get(name)
    if alias:
        variants.add(names.normalise(alias))
    return variants


def team_detail(season_code, div_code, name):
    """One team's table line, results and form for a season.

    Everything is derived from a single parse of that season's results, so the
    table line, the fixture list and the form dots can't disagree with each
    other the way reading table from one cache and fixtures from another
    could. Mirrors `_team_stats`/`_last_five` above for the form shape.

    A club with no rows this season (opening weekend, not yet promoted into
    this division) returns a blank-but-valid shape -- table None, fixtures
    empty, empty form trackers -- never an error.
    """
    try:
        rows = fetch_results(season_code, div_code)
    except Exception as exc:
        # Same guard as `_fetch_rows`/`standings._build_league`: the season's
        # file doesn't exist until its first results are published.
        logger.info("No team detail for %s %s (%r): %s", season_code, div_code, name, exc)
        rows = []

    variants = _resolve_target(name)

    def _side(row):
        if names.normalise(row["home"]) in variants:
            return "home"
        if names.normalise(row["away"]) in variants:
            return "away"
        return None

    played = []
    fixtures = []
    for row in sorted(rows, key=lambda r: r["played_on"] or date.min):
        venue = _side(row)
        if not venue:
            continue
        if venue == "home":
            gf, ga, opponent = row["home_goals"], row["away_goals"], row["away"]
        else:
            gf, ga, opponent = row["away_goals"], row["home_goals"], row["home"]
        result = _outcome(gf, ga)
        btts = "Y" if row["home_goals"] > 0 and row["away_goals"] > 0 else "N"
        over25 = "Y" if row["home_goals"] + row["away_goals"] > 2 else "N"
        played.append((venue, result, btts, over25))
        fixtures.append({
            "date": row["played_on"].isoformat() if row["played_on"] else None,
            "opponent": opponent,
            "venue": venue,
            "gf": gf,
            "ga": ga,
            "result": result,
        })

    # `played` stays oldest-first for `_last_five`; the fixture list itself
    # reads newest first.
    fixtures.reverse()

    table = None
    for entry in overall_table(rows):
        if names.normalise(entry["team"]) in variants:
            table = {field: entry[field] for field in
                      ("pos", "played", "won", "drawn", "lost", "gf", "ga", "gd", "points")}
            break

    return {
        "table": table,
        "fixtures": fixtures,
        "form": {
            "overall": _last_five(played),
            "home": _last_five([e for e in played if e[0] == "home"]),
            "away": _last_five([e for e in played if e[0] == "away"]),
        },
    }


def locate_team_division(season_code, name, prefer):
    """Which division a club's rows actually live in for a season.

    Tries `prefer` (usually the club's current division) first, since that is
    the common case and avoids extra fetches. Falls through the rest of
    `SEARCH_DIVISIONS` in ladder order for a club that has moved. Mirrors
    `team_detail`'s per-division fetch guard -- a missing/unpublished season
    file for one division just means "not there", not an error.
    """
    order = [prefer] + [d for d in SEARCH_DIVISIONS if d != prefer]
    variants = _resolve_target(name)

    for div_code in order:
        if div_code not in SEARCH_DIVISIONS:
            continue
        try:
            rows = fetch_results(season_code, div_code)
        except Exception as exc:
            logger.info("No rows for %s %s while locating %r: %s",
                        season_code, div_code, name, exc)
            continue
        if any(names.normalise(entry["team"]) in variants for entry in overall_table(rows)):
            return div_code

    return None


def classify_move(prev_div, current_div):
    """None if unchanged (or either division isn't one we track), else
    "relegated"/"promoted" for the direction from `prev_div` to `current_div`.

    `SEARCH_DIVISIONS` is ordered top-to-bottom, so a lower index is a higher
    tier -- moving to a higher index means the club dropped a division.
    """
    if prev_div == current_div:
        return None
    if prev_div not in SEARCH_DIVISIONS or current_div not in SEARCH_DIVISIONS:
        return None
    return ("relegated"
            if SEARCH_DIVISIONS.index(prev_div) < SEARCH_DIVISIONS.index(current_div)
            else "promoted")


def team_detail_resolved(season_code, current_div, name):
    """`team_detail`, but for a season where the club may have played in a
    different division than the one it's in now -- resolves that division
    first and flags the move so the client can label it.

    `shown` is where the club actually played that season; it only differs
    from `current_div` when the club has since been promoted or relegated.
    """
    shown = locate_team_division(season_code, name, current_div) or current_div
    detail = team_detail(season_code, shown, name)
    return {
        **detail,
        "shown_division": shown,
        "shown_division_name": DIVISION_BY_CODE.get(shown, {}).get("name", shown),
        "move": classify_move(shown, current_div),
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
            "odds_key": DIVISION_BY_CODE[code]["odds_key"],
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


def attach_odds(payload, league_code):
    """Join cached bookmaker odds onto one division's upcoming fixtures.

    Only the requested division, and only when the viewed week is upcoming, so
    a past week never costs a request. Prices come through the same per-league
    cache the pick modal used (4h TTL), so browsing and tapping add no API
    traffic of their own — at worst one refresh per league per TTL window.

    Rows are copied, not mutated: the match dicts belong to the module cache.
    """
    week = next((w for w in payload["weeks"] if w["key"] == payload["week"]), None)
    league = next((l for l in payload["leagues"] if l["code"] == league_code), None)
    if not week or not week["upcoming"] or not league or not league.get("odds_key"):
        return payload
    # A division with nothing to play this week (an international break) has
    # nothing to price — don't spend a request finding that out.
    if not any(not row["played"] for row in league["matches"]):
        return payload

    index = names.build_index(_cache["teams"].get(league_code, {}).keys())
    priced = {}
    for match in odds_api.get_football_matches(league["odds_key"]):
        formatted = odds_api.format_match_for_display(match, league=league["odds_key"])
        if not formatted:
            continue
        key = (_canonical(formatted["home_team"], index),
               _canonical(formatted["away_team"], index))
        priced[key] = formatted

    league["matches"] = [
        row if row["played"]
        else {**row, "odds": priced.get((row["home"], row["away"]))}
        for row in league["matches"]
    ]
    return payload


async def refresh_fixture_list():
    """Background task. Retries sooner while nothing has been built."""
    while True:
        try:
            await asyncio.to_thread(refresh_once)
        except Exception as exc:
            logger.error("Fixture list refresh failed: %s", exc)
        delay = REFRESH_INTERVAL_SECONDS if _cache["ready"] else RETRY_INTERVAL_SECONDS
        await asyncio.sleep(delay)


if __name__ == "__main__":
    # classify_move direction check -- the bug-prone bit is inverting
    # relegated/promoted, so pin the concrete cases from the spec.
    cases = [
        ("E0", "E1", "relegated"),  # came down from the Prem into the Champ
        ("E1", "E0", "promoted"),   # went up from the Champ into the Prem
        ("EC", "E3", "promoted"),   # went up from the National League into L2
        ("E1", "E1", None),         # stayed put
    ]
    for prev_div, current_div, expected in cases:
        actual = classify_move(prev_div, current_div)
        assert actual == expected, (
            f"classify_move({prev_div!r}, {current_div!r}) = {actual!r}, expected {expected!r}")
        print(f"classify_move({prev_div!r}, {current_div!r}) = {actual!r}  OK")
    print("All classify_move cases passed.")

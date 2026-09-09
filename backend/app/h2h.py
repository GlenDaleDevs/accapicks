"""Head-to-head record between two teams, from football-data.co.uk history.

Deep history (~12 seasons x E0-E3) is loaded once by a background task and
kept in memory -- 48 files, each disk-cached permanently once football-data
marks a season finished (see predictionmodel.footballdata._is_fresh). The
request path never fetches; it only filters whatever the background task has
already loaded, so a slow cold warm-up can never turn into a slow request.
"""

import asyncio
import logging
import os
import time

from .predictionmodel import names
from .predictionmodel.config import CURRENT_SEASON, TARGET_DIVISIONS
from .predictionmodel.footballdata import fetch_results

logger = logging.getLogger(__name__)

SEASON_COUNT = 12
MAX_MEETINGS = 15

# The warm-up fetches ~48 files. football-data.co.uk rate-limits bursts, and a
# burst there gets the whole IP throttled — which then fails the CURRENT-season
# fetches the form dots, standings and team pages depend on. So trickle: wait
# before starting (let the essential feeds fetch first) and space each fetch out.
WARM_START_DELAY_SECONDS = 60
FETCH_SPACING_SECONDS = 3

# Kill switch: set H2H_WARM_ENABLED=0 in Railway to stop ALL H2H football-data
# fetching, so the core feeds (form dots, standings, team pages) have the site
# to themselves if it has rate-limited the IP. H2H just shows "still loading"
# until re-enabled.
WARM_ENABLED = os.getenv("H2H_WARM_ENABLED", "1") != "0"

_cache = {"rows": [], "known": set(), "ready": False}
_unresolved_logged = set()


def _season_codes(count=SEASON_COUNT):
    """`count` football-data season codes ending at CURRENT_SEASON, oldest
    first (e.g. "1516".."2627"). Derived from CURRENT_SEASON so it can never
    emit a code newer than the live season."""
    start_year = int(CURRENT_SEASON[:2])
    codes = [
        f"{(start_year - i) % 100:02d}{(start_year - i + 1) % 100:02d}"
        for i in range(count)
    ]
    codes.reverse()
    return codes


SEASON_CODES = _season_codes()


def load_history():
    """Fetch every (season, division) grid cell, skipping any that fail.

    A missing old division-season (a club's division didn't exist, or a
    file simply isn't published) must not crash the whole load -- mirrors
    fixturelist._fetch_rows.
    """
    rows = []
    first = True
    for season in SEASON_CODES:
        for div in TARGET_DIVISIONS:
            # Space out the fetches so the burst can't get football-data to
            # throttle the IP (which would take the current-season feeds down
            # with it). The first cell goes immediately; the rest trickle.
            if not first:
                time.sleep(FETCH_SPACING_SECONDS)
            first = False
            try:
                season_rows = fetch_results(season, div)
            except Exception as exc:
                logger.info("H2H: no history for %s %s: %s", season, div, exc)
                continue
            for row in season_rows:
                rows.append({**row, "season": season})
    return rows


def get_history():
    """(rows, ready) from the background-warmed cache."""
    return _cache["rows"], _cache["ready"]


async def warm_h2h_history():
    """Background task: load the whole grid once into the cache.

    Finished seasons are immutable once cached to disk and the current
    season's slice is tiny, so a single load is enough -- there is nothing
    to gain from re-looping the way standings/fixtures do on a TTL.

    Waits before starting so the essential fixtures/standings fetches (which the
    form dots and tables need) get to football-data first and are cached before
    this trickle begins.
    """
    if not WARM_ENABLED:
        logger.warning("H2H warm-up disabled (H2H_WARM_ENABLED=0); no history loaded")
        return
    await asyncio.sleep(WARM_START_DELAY_SECONDS)
    rows = await asyncio.to_thread(load_history)
    _cache["rows"] = rows
    _cache["known"] = {names.normalise(r["home"]) for r in rows} | {
        names.normalise(r["away"]) for r in rows
    }
    _cache["ready"] = True
    logger.info(
        "H2H history warmed: %d rows across %d seasons x %d divisions",
        len(rows), len(SEASON_CODES), len(TARGET_DIVISIONS),
    )


def _variants(name):
    """Normalised forms to match a row's team name against -- the name as
    given, and its alias-mapped form. Mirrors fixturelist._resolve_target."""
    variants = {names.normalise(name)}
    alias = names.ALIASES.get(name)
    if alias:
        variants.add(names.normalise(alias))
    return variants


def _log_unresolved(name):
    if name not in _unresolved_logged:
        _unresolved_logged.add(name)
        logger.info("H2H: no history rows match team %r", name)


def _empty_record(home, away, ready):
    return {
        "ready": ready,
        "team_a": home,
        "team_b": away,
        "summary": {"a_wins": 0, "draws": 0, "b_wins": 0, "played": 0},
        "meetings": [],
    }


def h2h_record(home, away):
    """All-time record between `home` (team_a) and `away` (team_b).

    Orientation is decided per meeting BEFORE scoring -- which side of that
    row team_a actually played, home or away -- then scored against that,
    not against the (home, away) parameter order. Copies fixturelist._side.
    """
    home = (home or "").strip()
    away = (away or "").strip()
    rows, ready = get_history()

    if not home or not away or not ready or not rows:
        return _empty_record(home, away, ready)

    a_variants = _variants(home)
    b_variants = _variants(away)

    known = _cache["known"]
    if not (a_variants & known):
        _log_unresolved(home)
    if not (b_variants & known):
        _log_unresolved(away)

    a_wins = draws = b_wins = 0
    meetings = []
    for row in rows:
        row_home = names.normalise(row["home"])
        row_away = names.normalise(row["away"])

        if row_home in a_variants and row_away in b_variants:
            a_is_home = True
        elif row_home in b_variants and row_away in a_variants:
            a_is_home = False
        else:
            continue

        hg, ag = row["home_goals"], row["away_goals"]
        if hg == ag:
            draws += 1
        elif (a_is_home and hg > ag) or (not a_is_home and ag > hg):
            a_wins += 1
        else:
            b_wins += 1

        played_on = row.get("played_on")
        meetings.append({
            "date": played_on.isoformat() if played_on else row.get("date"),
            "home": row["home"],
            "away": row["away"],
            "home_goals": hg,
            "away_goals": ag,
            "division": row["div"],
            "season": row["season"],
        })

    meetings.sort(key=lambda m: m["date"] or "", reverse=True)

    return {
        "ready": True,
        "team_a": home,
        "team_b": away,
        "summary": {
            "a_wins": a_wins,
            "draws": draws,
            "b_wins": b_wins,
            "played": a_wins + draws + b_wins,
        },
        "meetings": meetings[:MAX_MEETINGS],
    }


if __name__ == "__main__":
    # Orientation self-test: the subtle bug is scoring against parameter
    # order instead of which side team_a actually played. Cover both an
    # a-home-win and an a-away-win.
    from datetime import date as _date

    def _row(home, away, hg, ag, played_on, season="2425"):
        return {
            "div": "E0", "home": home, "away": away,
            "home_goals": hg, "away_goals": ag, "played_on": played_on,
            "date": played_on.isoformat() if played_on else "", "season": season,
        }

    _cache["rows"] = [
        _row("Arsenal", "Chelsea", 2, 1, _date(2024, 10, 1)),  # a home win
        _row("Chelsea", "Arsenal", 1, 3, _date(2025, 3, 1)),   # a away win
        _row("Chelsea", "Arsenal", 2, 2, _date(2023, 11, 5)),  # draw
    ]
    _cache["ready"] = True
    _cache["known"] = {names.normalise("Arsenal"), names.normalise("Chelsea")}

    record = h2h_record("Arsenal", "Chelsea")
    assert record["ready"] is True
    assert record["summary"] == {"a_wins": 2, "draws": 1, "b_wins": 0, "played": 3}, record
    assert record["meetings"][0]["date"] == "2025-03-01", "expected newest-first"
    assert record["meetings"][-1]["date"] == "2023-11-05"

    # Reversed call: team_a/team_b swap, so wins should flip too.
    reversed_record = h2h_record("Chelsea", "Arsenal")
    assert reversed_record["summary"] == {"a_wins": 0, "draws": 1, "b_wins": 2, "played": 3}, reversed_record

    print("h2h orientation self-test: PASS", record["summary"], reversed_record["summary"])

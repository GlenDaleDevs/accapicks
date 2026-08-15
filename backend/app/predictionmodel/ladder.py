"""Continuous cross-division home and away ladders.

Two independent ladders are built from split form:

  home ladder -- every club ranked by its HOME-only record
  away ladder -- every club ranked by its AWAY-only record

Each is a single continuous ranking across all five tiers, so a Championship
club and a League Two club sit on one comparable scale:

  Premier League    1 - 20
  Championship     21 - 44
  League One       45 - 68
  League Two       69 - 92
  National League  93 - 116

Offsets come from the actual size of each table, not hardcoded constants.
"""

from .config import DIVISION_OFFSETS, DIVISIONS, LADDER_SEASON
from .footballdata import fetch_results


def _blank(team):
    return {
        "team": team, "played": 0, "won": 0, "drawn": 0, "lost": 0,
        "gf": 0, "ga": 0,
    }


def _finalise(record):
    record["gd"] = record["gf"] - record["ga"]
    record["points"] = record["won"] * 3 + record["drawn"]
    return record


def build_division_tables(rows):
    """Split one division's results into a home table and an away table."""
    home, away = {}, {}

    for r in rows:
        h = home.setdefault(r["home"], _blank(r["home"]))
        a = away.setdefault(r["away"], _blank(r["away"]))

        h["played"] += 1
        a["played"] += 1
        h["gf"] += r["home_goals"]
        h["ga"] += r["away_goals"]
        a["gf"] += r["away_goals"]
        a["ga"] += r["home_goals"]

        if r["home_goals"] > r["away_goals"]:
            h["won"] += 1
            a["lost"] += 1
        elif r["home_goals"] < r["away_goals"]:
            h["lost"] += 1
            a["won"] += 1
        else:
            h["drawn"] += 1
            a["drawn"] += 1

    # A club that has only played away so far must still appear in the home
    # table (with a blank record), or the two tables desync and the ladder
    # offsets stop lining up.
    for team in set(home) | set(away):
        home.setdefault(team, _blank(team))
        away.setdefault(team, _blank(team))

    return (
        [_finalise(v) for v in home.values()],
        [_finalise(v) for v in away.values()],
    )


def _rank(table):
    """Sort by points, then goal difference, then goals for. Name breaks ties
    so the ordering is deterministic across runs."""
    ordered = sorted(
        table,
        key=lambda t: (-t["points"], -t["gd"], -t["gf"], t["team"]),
    )
    for i, entry in enumerate(ordered, start=1):
        entry["div_rank"] = i
    return ordered


def build_ladders(season=LADDER_SEASON):
    """Return {"home": {team: entry}, "away": {team: entry}, "size": int}."""
    home_ladder, away_ladder = {}, {}
    offset = 0

    for division in DIVISIONS:
        code = division["code"]
        try:
            rows = fetch_results(season, code)
        except Exception as exc:
            raise RuntimeError(
                f"cannot build the ladder: {division['name']} ({code}) is "
                f"unavailable for season {season} -- {exc}"
            ) from exc

        if not rows:
            raise RuntimeError(
                f"cannot build the ladder: {division['name']} ({code}) returned "
                f"no results for season {season}. Dropping a tier would shift "
                f"every ladder offset below it."
            )

        home_table, away_table = build_division_tables(rows)

        if len(home_table) != len(away_table):
            raise RuntimeError(
                f"{code}: home table has {len(home_table)} clubs but away has "
                f"{len(away_table)} -- tables are out of sync"
            )

        for table, ladder in ((home_table, home_ladder), (away_table, away_ladder)):
            for entry in _rank(table):
                entry["div"] = code
                entry["div_name"] = division["name"]
                entry["ladder_rank"] = offset + entry["div_rank"]
                entry["ppg"] = (
                    entry["points"] / entry["played"] if entry["played"] else 0.0
                )
                # Same scale for every tier, so a Championship side's away form
                # is comparable with a League One side's.
                entry["adjusted_ppg"] = entry["ppg"] + DIVISION_OFFSETS.get(code, 0.0)
                ladder[entry["team"]] = entry

        offset += len(home_table)

    _validate(home_ladder, "home")
    _validate(away_ladder, "away")

    return {"home": home_ladder, "away": away_ladder, "size": offset}


def _validate(ladder, label):
    ranks = sorted(e["ladder_rank"] for e in ladder.values())
    expected = list(range(1, len(ladder) + 1))
    if ranks != expected:
        missing = set(expected) - set(ranks)
        dupes = {r for r in ranks if ranks.count(r) > 1}
        raise RuntimeError(
            f"{label} ladder is not a clean 1..{len(ladder)} sequence "
            f"(missing={sorted(missing)[:5]} duplicated={sorted(dupes)[:5]})"
        )

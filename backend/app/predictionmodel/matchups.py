"""Favourable-matchup detection.

For a fixture, the home side is judged on its position in the HOME ladder and
the visitor on its position in the AWAY ladder -- so a side that is formidable
at home meeting a side that travels badly scores highly, even if their overall
league positions are similar.

    differential = awayLadderRank(away) - homeLadderRank(home)

Positive  -> the home team ranks better at home than the visitor does away:
             favours the home side.
Negative  -> favours the away side.

Both ladders are continuous across five tiers, so cross-division comparisons
are meaningful.
"""

import logging

from .config import (DEFAULT_METRIC, DIVISION_BY_CODE, LADDER_SEASON,
                     TARGET_DIVISIONS, TOP_N_PER_LEAGUE)
from .fixtures import fetch_fixtures
from .ladder import build_ladders
from .names import build_index, resolve

logger = logging.getLogger(__name__)


METRICS = ("rank", "adjusted")


def _gap(home_entry, away_entry, metric):
    """Strength gap, signed so that POSITIVE always favours the home side.

    rank     -- ladder places. Division membership dominates by construction:
                the worst Championship away side outranks the best League One
                home side no matter how they played.
    adjusted -- home/away PPG on a common scale via measured division offsets.
                A relegated club keeps a real edge (~+0.96 PPG dropping out of
                the Prem) rather than an unbeatable one.
    """
    if metric == "rank":
        return away_entry["ladder_rank"] - home_entry["ladder_rank"]
    if metric == "adjusted":
        return home_entry["adjusted_ppg"] - away_entry["adjusted_ppg"]
    raise ValueError(f"unknown metric {metric!r}, expected one of {METRICS}")


def _side(entry):
    return {
        "team": entry["team"],
        "ladder_rank": entry["ladder_rank"],
        "ppg": round(entry["ppg"], 2),
        "adjusted_ppg": round(entry["adjusted_ppg"], 2),
        "div": entry["div"],
        "div_name": entry["div_name"],
        "div_rank": entry["div_rank"],
        "played": entry["played"],
        "won": entry["won"],
        "drawn": entry["drawn"],
        "lost": entry["lost"],
        "gf": entry["gf"],
        "ga": entry["ga"],
        "gd": entry["gd"],
        "points": entry["points"],
    }


def evaluate_fixtures(fixtures, ladders, metric=DEFAULT_METRIC):
    """Attach ladder data and a differential to every fixture.

    Returns (evaluated, unresolved). A fixture whose teams can't be resolved is
    reported, never silently dropped.
    """
    # Each side is resolved against the ladder it will actually be looked up in.
    # The two ladders hold the same clubs in practice, but relying on that
    # coupling makes a desync fail silently instead of loudly.
    home_index = build_index(ladders["home"])
    away_index = build_index(ladders["away"])
    evaluated, unresolved = [], []

    for fixture in fixtures:
        home = resolve(fixture["home"], home_index)
        away = resolve(fixture["away"], away_index)

        if not home or not away:
            unresolved.append({
                "fixture": f"{fixture['home']} vs {fixture['away']}",
                "div": fixture["div"],
                "missing": [
                    raw for raw, res in
                    ((fixture["home"], home), (fixture["away"], away))
                    if not res
                ],
            })
            continue

        home_entry = ladders["home"][home]
        away_entry = ladders["away"][away]
        differential = _gap(home_entry, away_entry, metric)

        evaluated.append({
            "div": fixture["div"],
            "div_name": fixture["div_name"],
            "commence_time": fixture["commence_time"],
            "event_id": fixture["event_id"],
            "home": _side(home_entry),
            "away": _side(away_entry),
            "metric": metric,
            "differential": round(differential, 2),
            "abs_differential": round(abs(differential), 2),
            "favours": "home" if differential > 0 else "away" if differential < 0 else "neither",
        })

    return evaluated, unresolved


def top_per_league(evaluated, top_n=TOP_N_PER_LEAGUE):
    """Group by division and take the widest differentials in each."""
    grouped = {}
    for match in evaluated:
        grouped.setdefault(match["div"], []).append(match)

    result = {}
    for code in TARGET_DIVISIONS:
        matches = grouped.get(code, [])
        matches.sort(key=lambda m: (-m["abs_differential"], m["commence_time"] or ""))
        result[code] = {
            "div": code,
            "div_name": DIVISION_BY_CODE[code]["name"],
            "matchups": matches[:top_n],
            "considered": len(matches),
        }
    return result


def find_favourable_matchups(days_ahead=8, top_n=TOP_N_PER_LEAGUE,
                             season=LADDER_SEASON, strict=True,
                             metric=DEFAULT_METRIC):
    """Full pipeline: ladders -> fixtures -> differentials -> top N per league."""
    ladders = build_ladders(season)
    fixtures = fetch_fixtures(days_ahead=days_ahead)
    evaluated, unresolved = evaluate_fixtures(fixtures, ladders, metric=metric)

    if unresolved:
        for item in unresolved:
            logger.error("UNRESOLVED TEAM in %s: %s (missing: %s)",
                         item["div"], item["fixture"], ", ".join(item["missing"]))
        if strict:
            raise RuntimeError(
                f"{len(unresolved)} fixture(s) had teams missing from the ladder "
                f"-- add them to names.ALIASES. First: {unresolved[0]['fixture']}"
            )

    return {
        "season": season,
        "metric": metric,
        "ladder_size": ladders["size"],
        "fixtures_seen": len(fixtures),
        "fixtures_evaluated": len(evaluated),
        "unresolved": unresolved,
        "leagues": top_per_league(evaluated, top_n),
    }

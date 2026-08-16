"""Backtest the Favourable Matchups differential against historical results.

The football-data.co.uk CSVs the ladder is already built from carry the
fixtures, the results AND the closing odds, so the whole experiment runs off
one source. Nothing here touches The-Odds-API, which also means none of it
depends on names.py reconciliation — both sides speak football-data.

Two ladder modes, answering different questions:

  prior    ladder built from the whole of season S-1. This is exactly what
           production does today, all season long.
  todate   ladder built from results in season S before the fixture's own
           date. This is the "post-GW10 switch" that config.py documents and
           favourable.py never implements.

Usage:
    python -m scripts.backtest_matchups                # full run
    python -m scripts.backtest_matchups --seasons 2526
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.predictionmodel.config import DIVISIONS, TARGET_DIVISIONS  # noqa: E402
from app.predictionmodel.footballdata import fetch_results  # noqa: E402
from app.predictionmodel.ladder import build_ladders_from_rows  # noqa: E402
from app.predictionmodel.matchups import _gap  # noqa: E402

import backtest_report as report  # noqa: E402

# COVID seasons are excluded: home advantage collapsed behind closed doors, and
# config.py already leaves them out when deriving the division offsets.
SEASONS = ["2223", "2324", "2425", "2526"]

ALL_DIVISIONS = [d["code"] for d in DIVISIONS]


def prior_season(season):
    """"2526" -> "2425"."""
    start = int(season[:2])
    return f"{start - 1:02d}{start:02d}"


def load_season(season):
    """{div_code: rows} across all five tiers, sorted by date."""
    rows_by_div = {}
    for code in ALL_DIVISIONS:
        rows = fetch_results(season, code)
        rows_by_div[code] = sorted(
            (r for r in rows if r["played_on"]), key=lambda r: r["played_on"]
        )
    return rows_by_div


def _rounds_played(rows_by_div, code):
    """Rough matchweek index per fixture: how many games each club has played.

    Used only to split early season from late, so an approximation from the
    home side's game count is enough — no fixture-list scraping needed.
    """
    played = {}
    numbers = {}
    for row in rows_by_div[code]:
        for team in (row["home"], row["away"]):
            played[team] = played.get(team, 0) + 1
        numbers[id(row)] = max(played[row["home"]], played[row["away"]])
    return numbers


class TodateLadders:
    """Ladders rebuilt from results before each distinct date in the season.

    One ladder per matchday rather than per fixture — same thing, since every
    fixture on a date sees the same prior results, and it keeps the rebuild
    count in the low hundreds.
    """

    def __init__(self, rows_by_div):
        self._rows = rows_by_div
        self._cache = {}

    def for_date(self, day):
        if day in self._cache:
            return self._cache[day]
        before = {
            code: [r for r in rows if r["played_on"] < day]
            for code, rows in self._rows.items()
        }
        # Every tier needs at least one result or the offsets shift. Early
        # August has none, so those fixtures simply go unevaluated.
        try:
            ladders = build_ladders_from_rows(before)
        except RuntimeError:
            ladders = None
        self._cache[day] = ladders
        return ladders


def evaluate_season(season, mode, metric):
    """One row per fixture in the target divisions of `season`."""
    rows_by_div = load_season(season)

    if mode == "prior":
        ladders = build_ladders_from_rows(load_season(prior_season(season)))
        get_ladders = lambda _day: ladders  # noqa: E731
    else:
        todate = TodateLadders(rows_by_div)
        get_ladders = todate.for_date

    results = []
    unresolved = 0
    for code in TARGET_DIVISIONS:
        rounds = _rounds_played(rows_by_div, code)
        for row in rows_by_div[code]:
            ladders = get_ladders(row["played_on"])
            if ladders is None:
                unresolved += 1
                continue

            home = ladders["home"].get(row["home"])
            away = ladders["away"].get(row["away"])
            if not home or not away:
                # A club promoted from tier six has no prior-season record.
                unresolved += 1
                continue

            differential = _gap(home, away, metric)
            if row["home_goals"] > row["away_goals"]:
                outcome = "home"
            elif row["home_goals"] < row["away_goals"]:
                outcome = "away"
            else:
                outcome = "draw"

            results.append({
                "season": season,
                "div": code,
                "round": rounds[id(row)],
                "home": row["home"],
                "away": row["away"],
                "differential": differential,
                "favours": "home" if differential > 0 else "away" if differential < 0 else None,
                "outcome": outcome,
                "avg_h": row["avg_h"], "avg_d": row["avg_d"], "avg_a": row["avg_a"],
                "max_h": row["max_h"], "max_a": row["max_a"],
            })

    return results, unresolved


def run(seasons, modes, metrics):
    everything = {}
    for mode in modes:
        for metric in metrics:
            rows, skipped = [], 0
            for season in seasons:
                season_rows, season_skipped = evaluate_season(season, mode, metric)
                rows.extend(season_rows)
                skipped += season_skipped
                print(f"  {season} {mode}/{metric}: {len(season_rows)} fixtures, "
                      f"{season_skipped} unevaluated", file=sys.stderr)
            everything[(mode, metric)] = (rows, skipped)
    return everything


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", nargs="+", default=SEASONS)
    parser.add_argument("--modes", nargs="+", default=["prior", "todate"])
    parser.add_argument("--metrics", nargs="+", default=["adjusted", "rank"])
    parser.add_argument("--json", type=Path, help="also dump raw rows here")
    args = parser.parse_args()

    print("Loading and evaluating...", file=sys.stderr)
    everything = run(args.seasons, args.modes, args.metrics)

    report.print_report(everything, args.seasons)

    if args.json:
        payload = {
            f"{mode}|{metric}": rows
            for (mode, metric), (rows, _) in everything.items()
        }
        args.json.write_text(json.dumps(payload), encoding="utf-8")
        print(f"\nRaw rows written to {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()

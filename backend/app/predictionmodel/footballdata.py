"""football-data.co.uk results CSVs.

A finished season's file never changes, so it's cached to disk permanently and
fetched exactly once. The current season's file is refetched when stale.
"""

import csv
import io
import logging
import time
from datetime import datetime

import requests

from .config import CACHE_DIR, CURRENT_SEASON, LADDER_SEASON

logger = logging.getLogger(__name__)

BASE_URL = "https://www.football-data.co.uk/mmz4281"
CURRENT_SEASON_TTL = 6 * 60 * 60  # 6 hours

# football-data.co.uk rejects the default python-requests User-Agent (non-200),
# which this module treats as a failure and silently serves the stale cache for
# — so a bot-looking request freezes results at the last good fetch. A real
# browser UA is required to get a clean 200 with the CSV.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*",
}


def _cache_path(season, div_code):
    return CACHE_DIR / f"{season}_{div_code}.csv"


def _is_fresh(path, season):
    if not path.exists():
        return False
    # Any season other than the current one is finished and therefore
    # immutable -- never refetch it, not just the ladder's LADDER_SEASON.
    # Only the season still being played carries a TTL.
    if season != CURRENT_SEASON:
        return True
    return (time.time() - path.stat().st_mtime) < CURRENT_SEASON_TTL


def fetch_results(season, div_code):
    """Return parsed result rows for one division-season.

    Rows without a full-time result are skipped -- the current-season file
    contains scheduled-but-unplayed rows, and blank trailing lines are common
    in these files.
    """
    path = _cache_path(season, div_code)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if _is_fresh(path, season):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    else:
        url = f"{BASE_URL}/{season}/{div_code}.csv"
        try:
            resp = requests.get(url, timeout=30, headers=_HEADERS)
            # Not raise_for_status(): a missing file here returns 300 Multiple
            # Choices (Apache MultiViews) with an HTML body offering OTHER
            # LEAGUES as alternatives -- P1.csv, N1.csv, B1.csv. That is a 3xx,
            # so raise_for_status() waves it through and the HTML parses to an
            # empty table. Anything but a clean 200 is a failure.
            if resp.status_code != 200:
                raise RuntimeError(
                    f"HTTP {resp.status_code} -- {div_code}.csv likely does not "
                    f"exist for season {season} yet"
                )
        except Exception as exc:
            # Fall back to a stale cache rather than losing the division entirely
            if path.exists():
                logger.warning("fetch failed for %s %s (%s) -- using cached copy",
                               season, div_code, exc)
                text = path.read_text(encoding="utf-8-sig", errors="replace")
            else:
                raise RuntimeError(f"could not fetch {url}: {exc}") from exc
        else:
            resp.encoding = "utf-8-sig"
            text = resp.text
            path.write_text(text, encoding="utf-8")

    rows = parse_results(text, div_code, season)
    # Row count for the live season, so Railway logs make it obvious whether a
    # thin table is our fetch failing (see the warning above) or football-data
    # simply not having published the round yet.
    if season != LADDER_SEASON:
        logger.info("football-data %s/%s: %d played rows", season, div_code, len(rows))
    return rows


# Closing odds where available, pre-match otherwise. Carried through so the
# backtest can price the model's picks — a hit rate means nothing without the
# odds that were on offer. The ladder ignores these entirely.
_ODDS_COLUMNS = {
    "avg_h": ("AvgCH", "AvgH"),
    "avg_d": ("AvgCD", "AvgD"),
    "avg_a": ("AvgCA", "AvgA"),
    "max_h": ("MaxCH", "MaxH"),
    "max_d": ("MaxCD", "MaxD"),
    "max_a": ("MaxCA", "MaxA"),
}


def _price(raw, names):
    """First populated column of `names`, as a float. None when unpriced."""
    for name in names:
        value = (raw.get(name) or "").strip()
        if value:
            try:
                price = float(value)
            except ValueError:
                continue
            if price > 1:
                return price
    return None


def parse_date(value):
    """football-data dates are dd/mm/yy in older files and dd/mm/yyyy in newer."""
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_results(text, div_code, season="?"):
    """Parse a football-data.co.uk results CSV, refusing anything suspicious.

    Rows without a full-time result are skipped -- the current-season file
    carries scheduled-but-unplayed rows, and blank trailing lines are common.
    """
    reader = csv.DictReader(io.StringIO(text))
    columns = set(reader.fieldnames or [])
    required = {"Div", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
    if not required.issubset(columns):
        raise RuntimeError(
            f"{season}/{div_code}.csv is not a results CSV "
            f"(missing columns: {sorted(required - columns)})"
        )

    rows = []
    for raw in reader:
        # The Div column is the guard against silently ingesting a different
        # league: the server offers unrelated files when one is missing.
        row_div = (raw.get("Div") or "").strip()
        if row_div and row_div != div_code:
            raise RuntimeError(
                f"{season}/{div_code}.csv contains rows for division "
                f"{row_div!r} -- wrong league, refusing to use it"
            )

        home = (raw.get("HomeTeam") or "").strip()
        away = (raw.get("AwayTeam") or "").strip()
        fthg = (raw.get("FTHG") or "").strip()
        ftag = (raw.get("FTAG") or "").strip()
        if not home or not away or not fthg or not ftag:
            continue
        try:
            row = {
                "div": div_code,
                "date": (raw.get("Date") or "").strip(),
                "played_on": parse_date(raw.get("Date")),
                "home": home,
                "away": away,
                "home_goals": int(fthg),
                "away_goals": int(ftag),
            }
        except ValueError:
            continue
        for key, names in _ODDS_COLUMNS.items():
            row[key] = _price(raw, names)
        rows.append(row)

    return rows

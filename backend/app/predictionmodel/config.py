"""Divisions, seasons and paths.

The ladder spans five tiers so that clubs promoted out of the National League
still carry a real rank rather than an invented one.
"""

import os
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Vendored into AccaPicks. The container runs as a non-root user on an
# ephemeral filesystem, so the in-repo default isn't reliably writable there.
# Overridable, falling back to the system temp dir rather than the repo.
CACHE_DIR = Path(
    os.getenv("PREDICTIONMODEL_CACHE_DIR")
    or (PROJECT_ROOT / "data" / "cache" if os.access(PROJECT_ROOT, os.W_OK)
        else Path(tempfile.gettempdir()) / "predictionmodel-cache")
)

# football-data.co.uk season codes: 2025/26 -> "2526"
LADDER_SEASON = "2526"   # finished season -> the GW1-10 ladder
CURRENT_SEASON = "2627"  # populates as the season runs -> the post-GW10 switch

# Tier order defines the ladder. Ladder offsets are derived from the ACTUAL
# number of teams in each table at runtime, never hardcoded, so a division
# changing size can't silently corrupt the ranks.
DIVISIONS = [
    {"code": "E0", "name": "Premier League", "odds_key": "soccer_epl"},
    {"code": "E1", "name": "Championship", "odds_key": "soccer_efl_champ"},
    {"code": "E2", "name": "League One", "odds_key": "soccer_england_league1"},
    {"code": "E3", "name": "League Two", "odds_key": "soccer_england_league2"},
    {"code": "EC", "name": "National League", "odds_key": None},
]

DIVISION_BY_CODE = {d["code"]: d for d in DIVISIONS}
DIVISION_BY_ODDS_KEY = {d["odds_key"]: d for d in DIVISIONS if d["odds_key"]}

# Divisions we surface matchups for. National League is ladder-only: it exists
# to rank promoted clubs, and AccaPicks doesn't carry NL fixtures.
TARGET_DIVISIONS = ["E0", "E1", "E2", "E3"]

TOP_N_PER_LEAGUE = 3

# How much a division is actually worth, in points per game, measured from
# clubs that changed division between seasons (scripts/division_gap.py).
# 10 seasons, COVID years excluded, n=48/48/64/32 per transition.
#
# The relegated-club and promoted-club estimates agreed closely at every tier
# (e.g. +0.89 vs +1.04 for Prem<->Championship), which is what makes these
# trustworthy rather than an artefact of selection bias.
#
# Added to a club's home/away PPG to put every division on one scale. Offsets
# apply to the division a club played in LAST season -- the whole point is
# comparing a promoted side's lower-division form against an established side's.
DIVISION_OFFSETS = {
    "E0": 2.75,
    "E1": 1.79,
    "E2": 1.02,
    "E3": 0.56,
    "EC": 0.00,
}

# "rank"     -- ordinal ladder gap, as originally specified
# "adjusted" -- division-adjusted home/away points per game
#
# Note the offsets only bite while the ladder comes from LAST season, when a
# fixture can pit a promoted club's lower-division form against an established
# club's. Once the ladder is built from the CURRENT season, both sides of a
# league fixture sit in the same division, so their offsets are identical and
# cancel -- "adjusted" degrades to plain home/away PPG on its own.
DEFAULT_METRIC = "adjusted"

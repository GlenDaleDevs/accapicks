"""Turning a fixture list into candidate weeks.

Pure functions, no database and no network — everything comes in as events and
goes out as date blocks, so this can be exercised against a live fixture list
from a script.

Two shapes of week:

  Saturday  the normal one. Anchored on the Saturday and spread into Friday,
            Sunday and Monday only where those days actually have fixtures, so
            the whole round is pickable even though the habit is a 3pm
            Saturday. The acca locks at the earliest kickoff anyone *picks*, so
            an unpicked Friday game costs nothing.

  Midweek   a full Premier League round on a Tue/Wed/Thu. A single rearranged
            fixture is not a round, hence MIN_PL_MIDWEEK — the EFL plays
            midweek constantly and must not trigger a week on its own.

An international break needs no special case: it simply has no fixtures, so it
produces no blocks.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# Kickoffs come back as UTC. Bucketing them by UTC date would put a 23:00 BST
# game on the following day.
UK_TZ = ZoneInfo("Europe/London")

PREMIER_LEAGUE = "soccer_epl"

# The four English leagues, in table order. Every auto-created week offers all
# of them; the Saturday anchor only cares that at least one has a fixture.
AUTO_WEEK_LEAGUES = [
    PREMIER_LEAGUE,
    "soccer_efl_champ",
    "soccer_england_league1",
    "soccer_england_league2",
]

SATURDAY = 5
MIDWEEK_DAYS = (1, 2, 3)  # Tue, Wed, Thu

# Days either side of the Saturday that belong to the same round.
WEEKEND_OFFSETS = (-1, 1, 2)  # Fri, Sun, Mon

# A round, not a rearranged game.
MIN_PL_MIDWEEK = 4

# AccaCreate and the Calendar both cap at 7. Blocks never reach 3 in practice.
MAX_DATES = 7

LOOKAHEAD_DAYS = 21


def _kickoff_date(commence_time):
    """UK calendar date for an ISO-8601 UTC kickoff, or None if unparseable."""
    if not commence_time:
        return None
    try:
        dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return dt.astimezone(UK_TZ).date()


def count_by_date(events_by_league):
    """({league: [event]}) -> (fixtures per date across all leagues,
    fixtures per date in the Premier League alone)."""
    all_counts = {}
    pl_counts = {}
    for league, events in (events_by_league or {}).items():
        for event in events or []:
            day = _kickoff_date(event.get("commence_time"))
            if day is None:
                continue
            all_counts[day] = all_counts.get(day, 0) + 1
            if league == PREMIER_LEAGUE:
                pl_counts[day] = pl_counts.get(day, 0) + 1
    return all_counts, pl_counts


def _saturday_blocks(all_counts, today, horizon):
    blocks = []
    for day in sorted(all_counts):
        if day.weekday() != SATURDAY or day < today or day > horizon:
            continue
        blocks.append({"anchor": day, "dates": _weekend_days(day, all_counts, today)})
    return blocks


def _weekend_days(anchor, all_counts, today):
    """Fri/Sat/Sun/Mon around a Saturday, keeping only days with fixtures.

    A Friday already gone by is dropped — the week must not claim a date its
    fixtures can no longer be picked on.
    """
    days = [anchor]
    for offset in WEEKEND_OFFSETS:
        day = anchor + timedelta(days=offset)
        if day >= today and all_counts.get(day):
            days.append(day)
    return sorted(days)


def _midweek_blocks(pl_counts, today, horizon):
    """Contiguous Tue/Wed/Thu runs carrying a full Premier League round."""
    candidates = sorted(
        day for day, count in pl_counts.items()
        if count and day.weekday() in MIDWEEK_DAYS and today <= day <= horizon
    )

    runs = []
    for day in candidates:
        if runs and day - runs[-1][-1] == timedelta(days=1):
            runs[-1].append(day)
        else:
            runs.append([day])

    return [
        {"anchor": run[0], "dates": run}
        for run in runs
        if sum(pl_counts[d] for d in run) >= MIN_PL_MIDWEEK
    ]


def find_week_blocks(events_by_league, today=None):
    """Candidate weeks from a fixture list, soonest first.

    Each block is {"anchor": date, "dates": ["YYYY-MM-DD", ...]}.
    """
    today = today or datetime.now(UK_TZ).date()
    horizon = today + timedelta(days=LOOKAHEAD_DAYS)

    all_counts, pl_counts = count_by_date(events_by_league)
    blocks = _saturday_blocks(all_counts, today, horizon)
    blocks += _midweek_blocks(pl_counts, today, horizon)
    blocks.sort(key=lambda b: b["anchor"])

    return [
        {"anchor": b["anchor"], "dates": [d.isoformat() for d in b["dates"][:MAX_DATES]]}
        for b in blocks
    ]


def weekend_dates_for(anchor, all_counts, today):
    """Dates a Saturday block should cover given the current fixture list.

    Used to widen a week that was created before the API listed the whole
    round. Returns ISO strings.
    """
    return [d.isoformat() for d in _weekend_days(anchor, all_counts, today)]


def is_saturday(day: date) -> bool:
    return day.weekday() == SATURDAY


def saturday_in(dates):
    """The Saturday among a set of ISO date strings, if there is one. Identifies
    a weekend week without needing a stored anchor."""
    for raw in sorted(dates or []):
        try:
            day = date.fromisoformat(raw)
        except (ValueError, TypeError):
            continue
        if is_saturday(day):
            return day
    return None

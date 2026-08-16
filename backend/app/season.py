"""Season scoping and week numbering.

`Acca.round_number` is a per-group counter that is never reset and never
reissued, which makes it a stable URL key but a poor label: a group in its
third season would be on "Week 34". The number people want to read is the
position within the *current* season, so that is computed here and rendered
instead, while round_number keeps doing the routing.

Accas before the group's season_start_date have no week number — they belong to
a previous season and keep showing their original one.
"""

from datetime import date

from . import models


def season_accas(db, group):
    """The group's accas that count toward the current season.

    The leaderboard, the acca-stats bar and member profiles all read the same
    bet pool, so they scope together or they contradict each other. A null
    season_start_date counts everything ever, which is what every group starts
    with — a migration must not wipe standings on its own.

    Accas with no first_match_date are pre-numbering legacy rows and always
    predate a season start.
    """
    query = db.query(models.Acca).filter(models.Acca.group_id == group.id)
    if group.season_start_date:
        query = query.filter(
            models.Acca.first_match_date.isnot(None),
            models.Acca.first_match_date >= group.season_start_date,
        )
    return query.all()


def chronological(accas):
    """Sorted the way weeks are paged through. round_number breaks ties but
    does not drive the order — accas can be created out of date order."""
    return sorted(
        accas,
        key=lambda a: (a.first_match_date or date.max, a.round_number or 0),
    )


def week_numbers(accas):
    """{acca_id: 1-based position within the season}."""
    return {acca.id: i for i, acca in enumerate(chronological(accas), start=1)}


def week_numbers_for_group(db, group_id):
    """Same, looked up from a group id. Returns ({}, None) if the group is gone."""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return {}, None
    return week_numbers(season_accas(db, group)), group


def label(db, acca) -> str:
    """Human label for notifications — "Week 3", falling back to the stored name
    for accas created before numbering existed."""
    numbers, _ = week_numbers_for_group(db, acca.group_id)
    number = numbers.get(acca.id) or acca.round_number
    return f"Week {number}" if number else acca.name

"""Opening the week without anyone having to run the wizard.

Watches the fixture list and, for every group with auto weeks switched on,
creates the next Saturday (or full midweek round) as a numbered week. An
international break produces no fixtures and therefore no week — no calendar of
breaks is needed anywhere.

Auto-created accas are identified by `created_by IS NULL`: nobody made them, so
there is no creator to record. That marker is also what keeps `extend_week` off
manually created accas, where the chosen dates are a deliberate decision.

Every group gets weeks — there is no opt-out. A group that has never had one
also gets its season boundary set here, to the first date of the first week
that opens, so the table starts counting from the group's real first week.

`groups.skipped_saturday` is the one deliberate exception: an admin deleting
an *open* auto-created week records its anchor Saturday there, and
`create_auto_weeks` refuses to recreate that block. Deleting a *locked* week
does not set it — that's the restart path, not a skip.
"""

import asyncio
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from . import models, odds_api
from .weekblocks import (
    AUTO_WEEK_LEAGUES,
    UK_TZ,
    count_by_date,
    find_week_blocks,
    is_saturday,
    saturday_in,
    weekend_dates_for,
)

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 30 * 60

# How far ahead a week opens. One day puts the Saturday week up on its Friday.
# (Trade-off: if the task is down BOTH Friday and Saturday the week is missed
# with no backfill — accepted, given the 30-min tick + run-on-every-deploy.)
# Midweek Prem rounds are never auto-created — make those by hand.
LEAD_DAYS = 1

# On the opening Friday, hold off until the morning so the "week is open" push
# doesn't land in the small hours. Saturday (or later) opens regardless.
OPEN_HOUR = 7  # 07:00 UK

ACTIVE_STATUSES = ("open", "locked")


def _today():
    return datetime.now(UK_TZ).date()


def _last_date(acca):
    dates = acca.match_dates or []
    if not dates:
        return None
    try:
        return date.fromisoformat(max(dates))
    except (ValueError, TypeError):
        return None


def _is_live(acca, today):
    """Still taking picks. An acca nobody picked in never locks, so status
    alone would call a week from three months ago live — the same reasoning as
    isExpired() on the frontend."""
    if acca.status != "open":
        return False
    last = _last_date(acca)
    return last is None or last >= today


def _block_name(block):
    anchor = block["anchor"]
    label = "Saturday" if is_saturday(anchor) else "Midweek"
    return f"{label} {anchor.day} {anchor.strftime('%b')}"


def fetch_events():
    """Fixture lists for the four English leagues, keyed by sport key."""
    return {league: odds_api.get_events(league) for league in AUTO_WEEK_LEAGUES}


def _taken_dates(accas):
    taken = set()
    for acca in accas:
        if acca.status in ACTIVE_STATUSES:
            taken |= set(acca.match_dates or [])
    return taken


def _create(db, group, block):
    round_number = group.next_round_number or 1
    group.next_round_number = round_number + 1

    acca = models.Acca(
        group_id=group.id,
        name=_block_name(block),
        round_number=round_number,
        first_match_date=date.fromisoformat(min(block["dates"])),
        status="open",
        match_dates=block["dates"],
        leagues=list(AUTO_WEEK_LEAGUES),
        bet_type="h2h",
        created_by=None,
    )
    db.add(acca)
    db.flush()

    logger.info(
        "Auto-created week %s for group %s covering %s",
        round_number, group.id, ", ".join(block["dates"]),
    )
    return acca


def _notify(db, acca, block):
    try:
        from .push import send_push_to_group
        from .season import label
        anchor = block["anchor"]
        # Name the group: a member in several groups opens the same-dated week
        # in each at once, so without the group name the pushes read as spammy
        # duplicates rather than one-per-group.
        group = db.query(models.Group).filter(models.Group.id == acca.group_id).first()
        group_name = group.name if group else "your group"
        send_push_to_group(
            db,
            acca.group_id,
            {
                "title": f"{label(db, acca)} is open · {group_name}",
                "body": f"{anchor.strftime('%a')} {anchor.day} {anchor.strftime('%b')} — get your pick in",
                "tag": f"week-{acca.id}",
                "url": f"/g/{acca.group_id}/acca/{acca.round_number}",
            },
        )
    except Exception as e:
        # A push failure must never cost the group its week.
        logger.error(f"Failed to notify group {acca.group_id} of new week: {e}")


def _start_season(group, block):
    """First week a group ever opens starts its season.

    Set from the block's earliest date, not its Saturday: a week that opens on
    a Friday has that Friday as its first_match_date, and a boundary on the
    Saturday would drop the very week that set it out of the season.
    """
    if group.season_start_date:
        return
    group.season_start_date = date.fromisoformat(min(block["dates"]))
    logger.info(
        "Season start for group %s set to %s by its first auto week",
        group.id, group.season_start_date,
    )


def create_auto_weeks(db: Session, blocks, today, now):
    """Open the next weekend week for every group.

    Weekend (Saturday-anchored) blocks only; midweek Prem rounds are left for
    manual creation. Opens on the block's Friday from OPEN_HOUR, so the push
    lands Friday morning rather than at midnight.
    """
    groups = db.query(models.Group).all()

    created = []
    for group in groups:
        accas = db.query(models.Acca).filter(models.Acca.group_id == group.id).all()
        if any(_is_live(acca, today) for acca in accas):
            continue

        taken = _taken_dates(accas)
        for block in blocks:
            if (block["anchor"] - today).days > LEAD_DAYS:
                break  # blocks are sorted, so nothing later qualifies either
            if not is_saturday(block["anchor"]):
                continue  # never auto-create a midweek round
            if group.skipped_saturday and block["anchor"] == group.skipped_saturday:
                continue  # the admin deleted this weekend's week on purpose
            if (block["anchor"] - today).days == 1 and now.hour < OPEN_HOUR:
                break  # the opening Friday, but too early — wait for the morning
            if taken & set(block["dates"]):
                continue
            _start_season(group, block)
            created.append((_create(db, group, block), block))
            break

    if created:
        db.commit()
        for acca, block in created:
            _notify(db, acca, block)
    return len(created)


def extend_weeks(db: Session, all_counts, today):
    """Widen an auto-created Saturday week whose Sunday or Monday fixtures were
    not yet published when it was opened. Add-only — never removes a date, so a
    pick can't be stranded."""
    open_accas = db.query(models.Acca).filter(
        models.Acca.status == "open",
        models.Acca.created_by.is_(None),
    ).all()

    extended = 0
    for acca in open_accas:
        current = list(acca.match_dates or [])
        # first_match_date can be the Friday, so the Saturday is found from the
        # dates rather than assumed to be the first of them.
        anchor = saturday_in(current)
        if anchor is None or anchor < today:
            continue

        wanted = weekend_dates_for(anchor, all_counts, today)
        additions = [d for d in wanted if d not in current]
        if not additions:
            continue

        # Another active acca may already own that Sunday.
        siblings = db.query(models.Acca).filter(
            models.Acca.group_id == acca.group_id,
            models.Acca.id != acca.id,
            models.Acca.status.in_(ACTIVE_STATUSES),
        ).all()
        if _taken_dates(siblings) & set(additions):
            continue

        acca.match_dates = sorted(current + additions)
        # A newly published Friday fixture moves the chronological sort key.
        acca.first_match_date = date.fromisoformat(acca.match_dates[0])
        extended += 1
        logger.info(
            "Extended week %s (group %s) with %s",
            acca.round_number, acca.group_id, ", ".join(additions),
        )

    if extended:
        db.commit()
    return extended


def cleanup_lapsed_weeks(db: Session, today):
    """Delete weeks whose fixtures have been and gone with nobody picking.

    An acca with no picks never gets a locks_at, so auto-lock never sees it and
    it sits open forever. Left alone they'd accumulate one per Saturday.
    """
    open_accas = db.query(models.Acca).filter(models.Acca.status == "open").all()

    deleted = 0
    for acca in open_accas:
        last = _last_date(acca)
        if last is None or last >= today:
            continue
        bet_count = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).count()
        if bet_count:
            continue
        db.delete(acca)
        deleted += 1
        logger.info(
            "Deleted lapsed week %s (group %s): no picks, last fixture %s",
            acca.round_number, acca.group_id, last,
        )

    if deleted:
        db.commit()
    return deleted


def run_once(db: Session):
    now = datetime.now(UK_TZ)  # one clock read — today and the hour can't straddle midnight
    today = now.date()
    cleanup_lapsed_weeks(db, today)

    events = fetch_events()
    all_counts, _ = count_by_date(events)
    blocks = find_week_blocks(events, today)

    extend_weeks(db, all_counts, today)
    create_auto_weeks(db, blocks, today, now)


async def auto_create_weeks():
    """Background task. Runs once at startup, then on a slow tick.

    Running first matters more than it looks: the task restarts on every
    deploy, and sleeping first meant a run of deploys under 30 minutes apart
    pushed week creation back indefinitely — an afternoon of shipping once
    kept a deleted week from reopening for an hour. The pass is cheap (the
    events feed is the free endpoint) and idempotent, so running it on every
    deploy is safe.
    """
    from .database import SessionLocal

    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_once, db)
        except Exception as e:
            logger.error(f"Auto week error: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)

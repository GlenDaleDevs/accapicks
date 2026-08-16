"""Opening the week without anyone having to run the wizard.

Watches the fixture list and, for every group with auto weeks switched on,
creates the next Saturday (or full midweek round) as a numbered week. An
international break produces no fixtures and therefore no week — no calendar of
breaks is needed anywhere.

Auto-created accas are identified by `created_by IS NULL`: nobody made them, so
there is no creator to record. That marker is also what keeps `extend_week` off
manually created accas, where the chosen dates are a deliberate decision.
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

# How far ahead a week opens. Four days puts the Saturday week up on Tuesday —
# late enough that the API is listing the whole weekend, early enough that
# there's a week to pick in well before kickoff.
LEAD_DAYS = 4

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
        send_push_to_group(
            db,
            acca.group_id,
            {
                "title": f"{label(db, acca)} is open",
                "body": f"{anchor.strftime('%a')} {anchor.day} {anchor.strftime('%b')} — get your pick in",
                "tag": f"week-{acca.id}",
                "url": f"/g/{acca.group_id}/acca/{acca.round_number}",
            },
        )
    except Exception as e:
        # A push failure must never cost the group its week.
        logger.error(f"Failed to notify group {acca.group_id} of new week: {e}")


def create_auto_weeks(db: Session, blocks, today):
    """Open the next week for every eligible group."""
    groups = db.query(models.Group).filter(models.Group.auto_weeks.is_(True)).all()

    created = []
    for group in groups:
        accas = db.query(models.Acca).filter(models.Acca.group_id == group.id).all()
        if any(_is_live(acca, today) for acca in accas):
            continue

        taken = _taken_dates(accas)
        for block in blocks:
            if (block["anchor"] - today).days > LEAD_DAYS:
                break  # blocks are sorted, so nothing later qualifies either
            if taken & set(block["dates"]):
                continue
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
    today = _today()
    cleanup_lapsed_weeks(db, today)

    events = fetch_events()
    all_counts, _ = count_by_date(events)
    blocks = find_week_blocks(events, today)

    extend_weeks(db, all_counts, today)
    create_auto_weeks(db, blocks, today)


async def auto_create_weeks():
    """Background task. Runs on a slow tick — fixture lists barely move."""
    from .database import SessionLocal

    while True:
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_once, db)
        except Exception as e:
            logger.error(f"Auto week error: {e}")
            db.rollback()
        finally:
            db.close()

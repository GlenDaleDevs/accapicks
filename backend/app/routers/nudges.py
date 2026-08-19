"""Nudging a groupmate who hasn't picked yet.

One push, once per target per acca — the unique constraint on the nudges
table is the anti-spam rule, enforced here rather than trusted to the UI.
"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..limiter import limiter
from ..timeutils import as_utc
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

UK_TZ = ZoneInfo("Europe/London")


@router.post("/accas/{acca_id}/nudge/{target_user_id}", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def nudge_member(
    request: Request,
    acca_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Remind one member to pick before the deadline (locks_at)."""
    if target_user_id == user_id:
        raise HTTPException(status_code=400, detail="You can't nudge yourself")

    acca = db.query(models.Acca).filter(models.Acca.id == acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

    # Both sides must be members of the acca's group
    member_ids = {
        m.user_id
        for m in db.query(models.GroupMember.user_id).filter(
            models.GroupMember.group_id == acca.group_id
        ).all()
    }
    if user_id not in member_ids:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    if target_user_id not in member_ids:
        raise HTTPException(status_code=404, detail="That user is not in this group")

    # A nudge only means something while picks are still open and a deadline
    # exists — locks_at is the earliest kickoff among the picks already made.
    locks_at = as_utc(acca.locks_at)
    if acca.status != "open" or not locks_at:
        raise HTTPException(status_code=400, detail="This week isn't taking nudges")
    if locks_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="The deadline has already passed")

    has_bet = db.query(models.Bet).filter(
        models.Bet.acca_id == acca_id,
        models.Bet.user_id == target_user_id,
    ).first()
    if has_bet:
        raise HTTPException(status_code=400, detail="They've already picked")

    db.add(models.Nudge(acca_id=acca_id, target_user_id=target_user_id, nudged_by=user_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="They've already been nudged this week")

    # Push is best-effort — the nudge stands (and the button stays gone)
    # whether or not the target has a subscribed device.
    try:
        from ..push import send_push
        nudger = db.query(models.User).filter(models.User.id == user_id).first()
        deadline = locks_at.astimezone(UK_TZ).strftime("%a %H:%M")
        send_push(
            db,
            target_user_id,
            {
                "title": f"{nudger.username if nudger else 'A groupmate'} nudged you",
                "body": f"No pick in {acca.name} yet — deadline is {deadline}",
                "tag": f"nudge-{acca_id}",
                "url": f"/g/{acca.group_id}/acca/{acca.round_number}",
            },
        )
    except Exception as e:
        logger.warning(f"Nudge push failed for user {target_user_id}: {e}")

    logger.info(f"User {user_id} nudged user {target_user_id} on acca {acca_id}")
    return {"message": "Nudge sent"}

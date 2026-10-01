"""Display-device API: a Raspberry Pi Pico W polls the group's current acca.

Each member can mint ONE device token for their own membership. Only its
sha256 is stored (group_members.device_token_hash); the plaintext is shown
once at creation. Re-minting replaces the hash, which revokes the old token.
"""
import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .. import models, season
from ..database import get_db
from ..devicestate import build_payload, pick_current
from ..leaderboard import leaderboard_rows
from ..limiter import limiter, get_real_ip
from ..timeutils import as_utc
from .auth import get_current_user
from .groups import _group_or_404

logger = logging.getLogger(__name__)

router = APIRouter()

TOKEN_RE = re.compile(r"^apk_[A-Za-z0-9_-]{43}$")  # "apk_" + token_urlsafe(32)
LAST_SEEN_REFRESH = timedelta(minutes=5)
NO_STORE = {"Cache-Control": "no-store"}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _bearer_token(request: Request):
    """The presented device token, or None if the header is missing/malformed."""
    scheme, _, value = request.headers.get("authorization", "").partition(" ")
    value = value.strip()
    if scheme.lower() != "bearer" or not TOKEN_RE.match(value):
        return None
    return value


def _device_key(request: Request) -> str:
    """Rate-limit key: the credential, not the IP.

    Per-IP limits are spoofable via X-Forwarded-For. A request with no usable
    token falls back to the IP, which is fine since it gets a 401 anyway.
    """
    token = _bearer_token(request)
    return f"device:{_hash_token(token)}" if token else get_real_ip(request)


def _membership(db, group_id, user_id):
    return db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id,
    ).first()


@router.post("/groups/{group_id}/device-token", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_device_token(
    request: Request,
    response: Response,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Mint this member's device token, replacing (revoking) any previous one."""
    _group_or_404(db, group_id, user_id)
    member = _membership(db, group_id, user_id)

    token = "apk_" + secrets.token_urlsafe(32)
    member.device_token_hash = _hash_token(token)
    member.device_last_seen_at = None
    db.commit()

    logger.info(f"Device token created: user_id={user_id} group_id={group_id}")
    response.headers["Cache-Control"] = "no-store"
    return {"token": token}  # plaintext, this once only


@router.delete("/groups/{group_id}/device-token", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def revoke_device_token(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Revoke this member's device token."""
    _group_or_404(db, group_id, user_id)
    member = _membership(db, group_id, user_id)

    member.device_token_hash = None
    member.device_last_seen_at = None
    db.commit()

    logger.info(f"Device token revoked: user_id={user_id} group_id={group_id}")


@router.get("/groups/{group_id}/devices")
@limiter.limit("20/minute")
def count_devices(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """How many members in the group have a display connected."""
    _group_or_404(db, group_id, user_id)
    connected = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.device_token_hash.isnot(None),
    ).count()
    return {"connected": connected}


def _unauthorized(request: Request, reason: str):
    # Never log the Authorization header or anything derived from it.
    logger.warning(f"Device auth failed: {reason} ip={get_real_ip(request)}")
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid device token",
        headers={"WWW-Authenticate": "Bearer", **NO_STORE},
    )


@router.get("/device/state")
# Stacked loose per-IP cap: the per-token key below gives every random guess its
# own bucket, so this is the only brake on a flood of unknown tokens.
@limiter.limit("120/minute", key_func=get_real_ip)
@limiter.limit("12/minute", key_func=_device_key)
def get_device_state(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Compact current-acca state for a display. Auth is the bearer token only."""
    if (os.getenv("ENVIRONMENT", "").lower() == "production"
            and request.headers.get("x-forwarded-proto", "https") != "https"):
        raise HTTPException(status_code=400, detail="HTTPS required", headers=NO_STORE)

    token = _bearer_token(request)
    if token is None:
        raise _unauthorized(request, "missing or malformed token")

    # Hash-then-indexed-lookup on the unique column is the standard pattern that
    # doesn't leak timing about the stored secret, which satisfies the
    # compare_digest rule in spirit. Unsalted sha256 is fine for a 256-bit
    # random token: there is nothing to brute-force.
    member = db.query(models.GroupMember).filter(
        models.GroupMember.device_token_hash == _hash_token(token)
    ).first()
    if member is None:
        raise _unauthorized(request, "unknown or revoked token")

    group = db.query(models.Group).filter(models.Group.id == member.group_id).first()
    if group is None:
        raise _unauthorized(request, f"group gone (user_id={member.user_id})")

    now = datetime.now(timezone.utc)

    # Skip the write on most polls; a minute-level last-seen is not needed.
    last_seen = as_utc(member.device_last_seen_at)
    if last_seen is None or now - last_seen > LAST_SEEN_REFRESH:
        try:
            member.device_last_seen_at = now
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Device last-seen update failed: {e}")

    response.headers["Cache-Control"] = "no-store"

    accas = db.query(models.Acca).filter(models.Acca.group_id == group.id).all()
    acca = pick_current(accas, now)
    if acca is None:
        return build_payload(now, None, None, set(), {}, [], [])

    members = db.query(models.GroupMember.user_id).filter(
        models.GroupMember.group_id == group.id
    ).all()
    member_ids = {m.user_id for m in members}
    users = db.query(models.User.id, models.User.username).filter(
        models.User.id.in_(list(member_ids))
    ).all()
    bets = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).all()

    # week_number is None for past-season accas; never fall back to round_number.
    week = season.week_numbers(season.season_accas(db, group)).get(acca.id)

    return build_payload(
        now, acca, week, member_ids, {u.id: u.username for u in users},
        bets, leaderboard_rows(db, group),
    )

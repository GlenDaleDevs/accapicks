from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import models, schemas, odds_api
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter
from ..timeutils import as_utc

router = APIRouter()


def _recalculate_locks_at(db: Session, acca: models.Acca, member_ids: list[int] | None = None):
    """Recalculate locks_at based on earliest commence_time of actual picks."""
    query = db.query(models.Bet).filter(
        models.Bet.acca_id == acca.id,
        models.Bet.commence_time.isnot(None),
    )
    if member_ids is not None:
        query = query.filter(models.Bet.user_id.in_(member_ids))
    bets = query.all()

    if bets:
        earliest = min(b.commence_time for b in bets)
        acca.locks_at = earliest
    else:
        acca.locks_at = None


# Add a bet to an acca
@router.post("/bets", response_model=schemas.BetResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_bet(
    request: Request,
    bet: schemas.BetCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Add a bet to an accumulator"""

    # Verify the acca exists
    acca = db.query(models.Acca).filter(models.Acca.id == bet.acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

    # Check if acca is locked
    if acca.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This acca is locked and no longer accepting picks"
        )

    # Also check locks_at time directly (background task runs every 60s)
    if acca.locks_at and datetime.now(timezone.utc) >= as_utc(acca.locks_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This acca is locked and no longer accepting picks"
        )

    # Verify user is a member of the group
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == acca.group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Get current member IDs for conflict checks
    member_ids = [m.user_id for m in db.query(models.GroupMember.user_id).filter(
        models.GroupMember.group_id == acca.group_id
    ).all()]

    # Enforce league restrictions if acca has configured leagues
    if bet.sport_key and acca.leagues:
        if bet.sport_key not in acca.leagues:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This pick is from a league not included in this acca"
            )

    # Check if user has already added a bet to this acca
    existing_bet = db.query(models.Bet).filter(
        models.Bet.acca_id == bet.acca_id,
        models.Bet.user_id == user_id
    ).first()

    if existing_bet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You've already added a bet to this acca"
        )

    # Fixture-level exclusion: block if any CURRENT MEMBER already picked this fixture
    if bet.event_id:
        fixture_conflict = db.query(models.Bet).filter(
            models.Bet.acca_id == bet.acca_id,
            models.Bet.event_id == bet.event_id,
            models.Bet.user_id.in_(member_ids)
        ).first()
        if fixture_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another member has already picked from this fixture"
            )
        # Clean up orphaned bets with same event_id (from ex-members)
        db.query(models.Bet).filter(
            models.Bet.acca_id == bet.acca_id,
            models.Bet.event_id == bet.event_id,
            ~models.Bet.user_id.in_(member_ids)
        ).delete(synchronize_session=False)

    # Check if same pick already exists from a CURRENT MEMBER.
    # Dedup decision: for a market pick (event_id present), the description
    # is now server-derived from event_id+pick_type (see verify_pick below)
    # and isn't known yet at this point in the request, so checking it against
    # the client's (untrusted) description would be both wrong and pointless.
    # It's also unnecessary — the fixture-level exclusion above already blocks
    # ANY other current member's bet on the same event_id regardless of
    # pick_type, which is a strict superset of an event_id+pick_type dedup.
    # So description-based dedup only runs for manual/legacy picks that have
    # no event_id, where the client description is still the only key we have.
    if not bet.event_id:
        duplicate_pick = db.query(models.Bet).filter(
            models.Bet.acca_id == bet.acca_id,
            models.Bet.description == bet.description,
            models.Bet.user_id.in_(member_ids)
        ).first()

        if duplicate_pick:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This pick has already been taken by another member"
            )
        # Clean up orphaned bets with same description (from ex-members)
        db.query(models.Bet).filter(
            models.Bet.acca_id == bet.acca_id,
            models.Bet.description == bet.description,
            ~models.Bet.user_id.in_(member_ids)
        ).delete(synchronize_session=False)

    # Convert odds to string if it's not already
    odds_str = str(bet.odds)

    # Parse commence_time safely
    parsed_commence_time = None
    if bet.commence_time:
        try:
            parsed_commence_time = datetime.fromisoformat(bet.commence_time.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid commence_time format"
            )

    # Validate commence_time is not in the past
    if parsed_commence_time and parsed_commence_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pick a match that has already started"
        )

    # Validate commence_time is not too far in the future
    if parsed_commence_time and parsed_commence_time > datetime.now(timezone.utc) + timedelta(days=14):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pick a match more than 14 days in the future"
        )

    # Server-verify market picks. Never trust client-supplied odds, team
    # columns or description for these — a forged odds value inflates
    # best_odds_won on the leaderboard, and forged/flipped team columns can
    # make settlement (settlement.py) score a losing pick as a win. This runs
    # after all the cheap checks above so rejected/duplicate spam never
    # reaches it. Runs *after* commence_time validation per the plan, since
    # that's a free check that should short-circuit first.
    description = bet.description
    home_team = bet.home_team
    away_team = bet.away_team
    if bet.event_id and bet.pick_type and bet.sport_key:
        verified = odds_api.verify_pick(bet.sport_key, bet.event_id, bet.pick_type)
        if verified is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odds no longer available for this match — reopen it from Fixtures"
            )
        odds_str = str(verified["odds"])
        home_team = verified["home_team"]
        away_team = verified["away_team"]
        description = verified["description"]

    new_bet = models.Bet(
        acca_id=bet.acca_id,
        user_id=user_id,
        description=description,
        odds=odds_str,
        event_id=bet.event_id,
        home_team=home_team,
        away_team=away_team,
        pick_type=bet.pick_type,
        sport_key=bet.sport_key,
        commence_time=parsed_commence_time,
    )

    db.add(new_bet)
    db.flush()  # Get new_bet into session so recalculate sees it
    _recalculate_locks_at(db, acca, member_ids)
    try:
        db.commit()
        db.refresh(new_bet)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate bet detected — you may have already picked or this selection is taken"
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create bet")

    # Send push notification to group members. The first pick of the week is
    # the "it's started" moment, so it gets its own wording.
    try:
        from ..push import send_push_to_group
        user_obj = db.query(models.User).filter(models.User.id == user_id).first()
        username = user_obj.username if user_obj else "Someone"
        is_first_pick = (
            db.query(models.Bet).filter(models.Bet.acca_id == acca.id).count() == 1
        )
        send_push_to_group(
            db,
            acca.group_id,
            {
                "title": "First pick is in!" if is_first_pick else "New Pick Added",
                "body": (
                    f"{username} kicked off {acca.name}: {new_bet.description} — get yours in"
                    if is_first_pick
                    else f"{username} picked {new_bet.description} in {acca.name}"
                ),
                "tag": f"bet-{acca.id}",
                "url": f"/groups/{acca.group_id}/accas/{acca.id}",
            },
            exclude_user_id=user_id,
        )
    except Exception:
        pass  # Push is best-effort, don't fail the bet creation

    # Get the user to include username in response
    user = db.query(models.User).filter(models.User.id == user_id).first()

    return {
        "id": new_bet.id,
        "acca_id": new_bet.acca_id,
        "user_id": new_bet.user_id,
        "username": user.username if user else "Unknown",
        "description": new_bet.description,
        "odds": new_bet.odds,
        "result": new_bet.result,
        "created_at": new_bet.created_at,
        "event_id": new_bet.event_id,
        "home_team": new_bet.home_team,
        "away_team": new_bet.away_team,
        "pick_type": new_bet.pick_type,
        "sport_key": new_bet.sport_key,
        "commence_time": new_bet.commence_time,
    }


# Remove a bet (only by the user who placed it, and only while acca is open)
@router.delete("/bets/{bet_id}", status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def delete_bet(
    request: Request,
    bet_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Remove your own bet from an acca (only while acca is open)"""

    bet = db.query(models.Bet).filter(models.Bet.id == bet_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    if bet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove your own picks"
        )

    acca = db.query(models.Acca).filter(models.Acca.id == bet.acca_id).first()
    if not acca or acca.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove picks from a locked or settled acca"
        )

    # Block deletion if the bet's match has already started
    if bet.commence_time and as_utc(bet.commence_time) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove a pick after its match has started"
        )

    db.delete(bet)
    db.flush()
    _recalculate_locks_at(db, acca)
    db.commit()

    return {"message": "Pick removed"}

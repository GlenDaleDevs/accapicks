from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter

router = APIRouter()


def _recalculate_locks_at(db: Session, acca: models.Acca):
    """Recalculate locks_at based on earliest commence_time of actual picks."""
    bets = db.query(models.Bet).filter(
        models.Bet.acca_id == acca.id,
        models.Bet.commence_time.isnot(None),
    ).all()

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
    if acca.locks_at and datetime.now(timezone.utc) >= acca.locks_at:
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

    # Fixture-level exclusion: block if any outcome from this fixture is already picked
    if bet.event_id:
        fixture_conflict = db.query(models.Bet).filter(
            models.Bet.acca_id == bet.acca_id,
            models.Bet.event_id == bet.event_id
        ).first()
        if fixture_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another member has already picked from this fixture"
            )

    # Check if the same pick already exists in this acca (no duplicate selections)
    duplicate_pick = db.query(models.Bet).filter(
        models.Bet.acca_id == bet.acca_id,
        models.Bet.description == bet.description
    ).first()

    if duplicate_pick:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This pick has already been taken by another member"
        )

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

    new_bet = models.Bet(
        acca_id=bet.acca_id,
        user_id=user_id,
        description=bet.description,
        odds=odds_str,
        event_id=bet.event_id,
        home_team=bet.home_team,
        away_team=bet.away_team,
        pick_type=bet.pick_type,
        sport_key=bet.sport_key,
        commence_time=parsed_commence_time,
    )

    db.add(new_bet)
    db.flush()  # Get new_bet into session so recalculate sees it
    _recalculate_locks_at(db, acca)
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
    if bet.commence_time and bet.commence_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove a pick after its match has started"
        )

    db.delete(bet)
    db.flush()
    _recalculate_locks_at(db, acca)
    db.commit()

    return {"message": "Pick removed"}

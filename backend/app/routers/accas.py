import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, odds_api
from ..database import get_db
from .auth import get_current_user

router = APIRouter()


# Helper to build acca response dict with parsed JSON fields
def _acca_to_dict(acca):
    return {
        "id": acca.id,
        "group_id": acca.group_id,
        "name": acca.name,
        "status": acca.status,
        "match_dates": acca.match_dates,
        "leagues": acca.leagues,
        "bet_type": acca.bet_type,
        "locks_at": acca.locks_at,
        "created_by": acca.created_by,
        "created_at": acca.created_at,
    }


# Create a new acca
@router.post("/accas", response_model=schemas.AccaResponse, status_code=status.HTTP_201_CREATED)
async def create_acca(
    acca: schemas.AccaCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Create a new accumulator for a group"""

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

    # Calculate locks_at from earliest fixture kickoff
    locks_at = None
    earliest_kickoff = None
    for league in acca.leagues:
        matches = await asyncio.to_thread(odds_api.get_football_matches, league)
        for match in matches:
            commence = match.get("commence_time", "")
            # commence_time is ISO 8601 e.g. "2026-02-08T15:00:00Z"
            match_date = commence[:10]  # "2026-02-08"
            if match_date in acca.match_dates:
                if earliest_kickoff is None or commence < earliest_kickoff:
                    earliest_kickoff = commence

    if earliest_kickoff:
        locks_at = datetime.fromisoformat(earliest_kickoff.replace("Z", "+00:00"))

    new_acca = models.Acca(
        group_id=acca.group_id,
        name=acca.name,
        status="open",
        match_dates=acca.match_dates,
        leagues=acca.leagues,
        bet_type=acca.bet_type,
        locks_at=locks_at,
        created_by=user_id,
    )

    db.add(new_acca)
    db.commit()
    db.refresh(new_acca)

    return _acca_to_dict(new_acca)


# Get all accas for a group
@router.get("/groups/{group_id}/accas", response_model=list[schemas.AccaResponse])
def get_group_accas(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get all accas for a specific group"""

    # Verify user is a member of the group
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    accas = db.query(models.Acca).filter(models.Acca.group_id == group_id).all()
    return [_acca_to_dict(a) for a in accas]


# Get a specific acca with all its bets (including usernames!)
@router.get("/accas/{acca_id}", response_model=schemas.AccaWithBets)
def get_acca(
    acca_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get an acca with all its bets"""

    acca = db.query(models.Acca).filter(models.Acca.id == acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

    # Verify user is a member of the group this acca belongs to
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == acca.group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Get all bets for this acca with user information
    bets = db.query(models.Bet).filter(models.Bet.acca_id == acca_id).all()

    # Batch-query users to avoid N+1
    user_ids = list({bet.user_id for bet in bets})
    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    # Enhance bets with usernames
    bet_responses = []
    for bet in bets:
        user = user_map.get(bet.user_id)
        bet_dict = {
            "id": bet.id,
            "acca_id": bet.acca_id,
            "user_id": bet.user_id,
            "username": user.username if user else "Unknown",
            "description": bet.description,
            "odds": bet.odds,
            "result": bet.result,
            "event_id": bet.event_id,
            "home_team": bet.home_team,
            "away_team": bet.away_team,
            "pick_type": bet.pick_type,
            "sport_key": bet.sport_key,
            "commence_time": bet.commence_time,
            "created_at": bet.created_at
        }
        bet_responses.append(bet_dict)

    # Convert to response format
    acca_dict = _acca_to_dict(acca)
    acca_dict["bets"] = bet_responses

    return acca_dict


# Compare bookmakers for an acca
@router.get("/accas/{acca_id}/compare-bookmakers")
async def compare_bookmakers(
    acca_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get bookmaker comparison for an acca's total odds"""

    # Get the acca
    acca = db.query(models.Acca).filter(models.Acca.id == acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

    # Verify user is a member
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == acca.group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Get all bets
    bets = db.query(models.Bet).filter(models.Bet.acca_id == acca_id).all()

    if not bets:
        raise HTTPException(status_code=400, detail="No bets in this acca yet")

    # Extract bet descriptions to compare
    bet_descriptions = [bet.description for bet in bets]

    # Try comparison with cached odds first
    comparison = odds_api.compare_bookmakers_for_acca(bet_descriptions)

    # If no cached odds found, fetch fresh odds for the acca's leagues
    if not comparison and acca.leagues:
        for league in acca.leagues:
            await asyncio.to_thread(odds_api.get_football_matches, league)

        # Try comparison again with fresh odds
        comparison = odds_api.compare_bookmakers_for_acca(bet_descriptions)

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail="No matching odds found for the bets in this acca"
        )

    return comparison

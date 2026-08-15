import asyncio
import logging
import os
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import func, nulls_last
from sqlalchemy.orm import Session
from .. import models, schemas, odds_api
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter
from ..normalization import normalize

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper to build acca response dict with parsed JSON fields
def _acca_to_dict(acca):
    return {
        "id": acca.id,
        "group_id": acca.group_id,
        "name": acca.name,
        "round_number": acca.round_number,
        "first_match_date": acca.first_match_date,
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
@limiter.limit("10/minute")
def create_acca(
    request: Request,
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

    # Limit open accas per group
    open_count = db.query(models.Acca).filter(
        models.Acca.group_id == acca.group_id,
        models.Acca.status == "open"
    ).count()
    if open_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 open accas per group. Settle or delete existing accas first."
        )

    # Check for date overlap with active accas in this group
    existing_accas = db.query(models.Acca).filter(
        models.Acca.group_id == acca.group_id,
        models.Acca.status.in_(["open", "locked"])
    ).all()

    new_dates = set(acca.match_dates)
    for existing in existing_accas:
        if existing.match_dates:
            overlap = new_dates & set(existing.match_dates)
            if overlap:
                sorted_overlap = sorted(overlap)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"An active acca already covers these date(s): {', '.join(sorted_overlap)}. Delete or settle the existing acca first."
                )

    first_match_date = date.fromisoformat(min(acca.match_dates))

    # Weeks must be created in date order. Without this, "Week 7" could start
    # before "Week 6" — the arrows would page through time in the wrong
    # direction and Phase 3's rank windows would cover the wrong bets.
    latest = db.query(func.max(models.Acca.first_match_date)).filter(
        models.Acca.group_id == acca.group_id
    ).scalar()
    if latest is not None and first_match_date < latest:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You've already got a week starting {latest.day} {latest.strftime('%b')}. "
                "Create weeks in date order."
            )
        )

    # Allocate from the group's high-water mark so a number is never reused
    # after an acca is deleted. Row lock is a no-op on SQLite, which is fine —
    # local dev is single-writer.
    group = db.query(models.Group).filter(
        models.Group.id == acca.group_id
    ).with_for_update().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    round_number = group.next_round_number or 1
    group.next_round_number = round_number + 1

    # locks_at is calculated dynamically from picked matches, not upfront
    new_acca = models.Acca(
        group_id=acca.group_id,
        name=acca.name,
        round_number=round_number,
        first_match_date=first_match_date,
        status="open",
        match_dates=acca.match_dates,
        leagues=acca.leagues,
        bet_type=acca.bet_type,
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

    # Chronological. Previously unordered, which week paging cannot tolerate.
    accas = db.query(models.Acca).filter(
        models.Acca.group_id == group_id
    ).order_by(
        nulls_last(models.Acca.first_match_date.asc()),
        nulls_last(models.Acca.round_number.asc()),
    ).all()
    return [_acca_to_dict(a) for a in accas]


# Get a specific acca with all its bets (including usernames!)
@router.get("/accas/{acca_id}", response_model=schemas.AccaWithBets)
@limiter.limit("30/minute")
def get_acca(
    request: Request,
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
@limiter.limit("20/minute")
async def compare_bookmakers(
    request: Request,
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

    # Get bets from current members only (exclude orphaned bets from ex-members)
    member_ids = [m.user_id for m in db.query(models.GroupMember.user_id).filter(
        models.GroupMember.group_id == acca.group_id
    ).all()]
    bets = db.query(models.Bet).filter(
        models.Bet.acca_id == acca_id,
        models.Bet.user_id.in_(member_ids)
    ).all()

    if not bets:
        raise HTTPException(status_code=400, detail="No bets in this acca yet")

    # Extract bets with odds to compare
    bets_with_odds = [(bet.description, float(bet.odds)) for bet in bets]

    # Try comparison with cached odds first
    comparison = odds_api.compare_bookmakers_for_acca(bets_with_odds)

    # If no cached odds found, fetch fresh odds for the acca's leagues
    if not comparison and acca.leagues:
        for league in acca.leagues:
            await asyncio.to_thread(odds_api.get_football_matches, league)

        # Try comparison again with fresh odds
        comparison = odds_api.compare_bookmakers_for_acca(bets_with_odds)

    if not comparison:
        raise HTTPException(
            status_code=404,
            detail="No matching odds found for the bets in this acca"
        )

    return comparison


# Delete acca endpoint
@router.delete("/accas/{acca_id}")
@limiter.limit("3/minute")
def delete_acca(
    request: Request,
    acca_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Delete an acca (only if open and user is creator or group admin)"""

    try:
        # Get acca
        acca = db.query(models.Acca).filter(models.Acca.id == acca_id).first()
        if not acca:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Acca not found"
            )

        # Verify user is either acca creator OR group admin
        membership = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == acca.group_id,
            models.GroupMember.user_id == user_id
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group"
            )

        is_creator = acca.created_by == user_id
        is_admin = membership.role == "admin"

        if not is_creator and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the acca creator or group admin can delete this acca"
            )

        # Verify acca is open
        if acca.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only delete accas with 'open' status"
            )

        # Delete all bets in the acca
        db.query(models.Bet).filter(models.Bet.acca_id == acca_id).delete(synchronize_session=False)

        # Delete the acca
        db.delete(acca)
        db.commit()

        return {"message": "Acca deleted successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete acca"
        )


# Diagnostic: debug settlement for a specific acca
@router.get("/accas/{acca_id}/debug-settlement")
@limiter.limit("5/minute")
def debug_settlement(
    request: Request,
    acca_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Debug why an acca isn't settling. Returns diagnostic info."""
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=404, detail="Not found")

    from datetime import timedelta
    from ..odds_api import get_scores

    acca = db.query(models.Acca).filter(models.Acca.id == acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

    # Verify membership
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == acca.group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")

    # Restrict to acca creator or group admin
    is_creator = acca.created_by == user_id
    is_admin = membership.role == "admin"
    if not is_creator and not is_admin:
        raise HTTPException(status_code=403, detail="Only the acca creator or group admin can access diagnostics")

    now = datetime.now(timezone.utc)
    all_bets = db.query(models.Bet).filter(models.Bet.acca_id == acca_id).all()

    debug = {
        "acca_id": acca.id,
        "acca_status": acca.status,
        "total_bets": len(all_bets),
        "bets": [],
        "scores_found": {},
        "issues": [],
    }

    for bet in all_bets:
        bet_info = {
            "id": bet.id,
            "description": bet.description,
            "result": bet.result,
            "event_id": bet.event_id,
            "sport_key": bet.sport_key,
            "home_team": bet.home_team,
            "away_team": bet.away_team,
            "pick_type": bet.pick_type,
            "commence_time": str(bet.commence_time) if bet.commence_time else None,
        }

        if not bet.event_id:
            bet_info["issue"] = "no event_id — not auto-settleable"
        elif not bet.sport_key:
            bet_info["issue"] = "no sport_key — cannot fetch scores"
        elif not bet.commence_time:
            bet_info["issue"] = "no commence_time"
        elif (now - bet.commence_time) < timedelta(hours=3):
            bet_info["issue"] = f"match too recent — {(now - bet.commence_time).total_seconds() / 3600:.1f}h since kickoff (need 3h)"
        else:
            bet_info["issue"] = None
            bet_info["hours_since_kickoff"] = round((now - bet.commence_time).total_seconds() / 3600, 1)

        debug["bets"].append(bet_info)

    # Try fetching scores for each sport_key
    sport_keys = set(b.sport_key for b in all_bets if b.sport_key)
    for sport_key in sport_keys:
        try:
            scores = get_scores(sport_key, days_from=7)
            matched = {}
            for bet in all_bets:
                if bet.sport_key == sport_key and bet.event_id:
                    score_data = next((s for s in scores if s['id'] == bet.event_id), None)
                    if score_data:
                        matched[bet.event_id] = {
                            "completed": score_data.get("completed"),
                            "scores": score_data.get("scores"),
                            "home_team_api": score_data.get("home_team"),
                            "away_team_api": score_data.get("away_team"),
                            "home_team_bet": bet.home_team,
                            "away_team_bet": bet.away_team,
                            "home_match_exact": score_data.get("home_team") == bet.home_team,
                            "away_match_exact": score_data.get("away_team") == bet.away_team,
                            "home_match_normalized": normalize(score_data.get("home_team", "")) == normalize(bet.home_team or ""),
                            "away_match_normalized": normalize(score_data.get("away_team", "")) == normalize(bet.away_team or ""),
                        }
                    else:
                        matched[bet.event_id] = "NOT_FOUND_IN_SCORES"
                        debug["issues"].append(f"event {bet.event_id} not found in {sport_key} scores ({len(scores)} results)")
            debug["scores_found"][sport_key] = {
                "total_scores_returned": len(scores),
                "event_matches": matched,
            }
        except Exception as e:
            logger.error(f"Debug settlement: error fetching scores for {sport_key}: {e}")
            debug["scores_found"][sport_key] = {"error": "Failed to fetch scores"}
            debug["issues"].append(f"Error fetching scores for {sport_key}")

    if not sport_keys:
        debug["issues"].append("No bets have sport_key set — settlement cannot fetch scores")

    return debug

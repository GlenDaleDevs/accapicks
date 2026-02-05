from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter()


# Add a bet to an acca
@router.post("/bets", response_model=schemas.BetResponse, status_code=status.HTTP_201_CREATED)
def create_bet(
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
    if acca.status == "locked":
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

    new_bet = models.Bet(
        acca_id=bet.acca_id,
        user_id=user_id,
        description=bet.description,
        odds=odds_str
    )

    db.add(new_bet)
    try:
        db.commit()
        db.refresh(new_bet)
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
        "created_at": new_bet.created_at
    }


# Remove a bet (only by the user who placed it, and only while acca is open)
@router.delete("/bets/{bet_id}", status_code=status.HTTP_200_OK)
def delete_bet(
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

    db.delete(bet)
    db.commit()

    return {"message": "Pick removed"}


# Update bet result (mark as won/lost/void)
@router.put("/bets/{bet_id}/result")
def update_bet_result(
    bet_id: int,
    body: schemas.BetResultUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Mark a bet as won/lost/void and update acca status if all settled"""
    result = body.result

    # Get the bet
    bet = db.query(models.Bet).filter(models.Bet.id == bet_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Bet not found")

    # Get the acca
    acca = db.query(models.Acca).filter(models.Acca.id == bet.acca_id).first()
    if not acca:
        raise HTTPException(status_code=404, detail="Acca not found")

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

    # Update bet result
    bet.result = result
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update bet result")

    # Check if all bets in acca are settled
    all_bets = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).all()
    all_settled = all(b.result in ["won", "lost", "void"] for b in all_bets)

    if all_settled:
        acca.status = "settled"
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to settle acca")

    return {"message": "Bet result updated", "acca_status": acca.status}

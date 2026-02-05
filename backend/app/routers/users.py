from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .auth import get_current_user

router = APIRouter()


# Get user's personal stats
@router.get("/users/me/stats")
def get_my_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get personal stats for the current user across all groups"""

    # Get all bets by this user
    bets = db.query(models.Bet).filter(models.Bet.user_id == user_id).all()

    stats = {
        "total_bets": len(bets),
        "won": len([b for b in bets if b.result == "won"]),
        "lost": len([b for b in bets if b.result == "lost"]),
        "void": len([b for b in bets if b.result == "void"]),
        "pending": len([b for b in bets if b.result is None])
    }

    # Calculate win rate
    settled = stats["won"] + stats["lost"]
    stats["win_rate"] = round((stats["won"] / settled * 100), 1) if settled > 0 else 0

    return stats

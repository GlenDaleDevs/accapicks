import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter

router = APIRouter()


def get_admin_user_ids() -> list[int]:
    """Parse ADMIN_USER_IDS from environment variable."""
    admin_ids = os.getenv("ADMIN_USER_IDS", "1")
    return [int(uid.strip()) for uid in admin_ids.split(",") if uid.strip()]


def require_admin(user_id: int = Depends(get_current_user)):
    """Dependency to verify user is an admin."""
    if user_id not in get_admin_user_ids():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user_id


@router.get("/affiliate/links")
def get_bookmaker_links(db: Session = Depends(get_db)):
    """Get all active bookmaker affiliate links (no auth required)"""
    links = db.query(models.BookmakerLink).filter(
        models.BookmakerLink.is_active == True
    ).all()

    result = {}
    for link in links:
        result[link.bookmaker_key] = {
            "url": link.url,
            "display_name": link.display_name
        }

    return result


@router.post("/affiliate/clicks")
@limiter.limit("30/minute")
def track_bookmaker_click(
    request: Request,
    data: schemas.BookmakerClickRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Track a bookmaker click (requires auth)"""

    click = models.BookmakerClick(
        bookmaker_key=data.bookmaker_key,
        acca_id=data.acca_id,
        source=data.source,
        user_id=user_id
    )

    db.add(click)
    db.commit()

    return {"status": "ok"}


@router.put("/affiliate/links/{bookmaker_key}")
def update_bookmaker_link(
    bookmaker_key: str,
    url: Optional[str] = None,
    display_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_admin)
):
    """Update a bookmaker affiliate link (admin only)"""

    link = db.query(models.BookmakerLink).filter(
        models.BookmakerLink.bookmaker_key == bookmaker_key
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Bookmaker link not found")

    if url is not None:
        link.url = url
    if display_name is not None:
        link.display_name = display_name
    if is_active is not None:
        link.is_active = is_active

    db.commit()
    db.refresh(link)

    return {
        "bookmaker_key": link.bookmaker_key,
        "url": link.url,
        "display_name": link.display_name,
        "is_active": link.is_active
    }


@router.get("/affiliate/stats")
def get_affiliate_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_admin)
):
    """Get affiliate click statistics (admin only)"""

    query = db.query(models.BookmakerClick)

    # Apply date filters if provided
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(models.BookmakerClick.clicked_at >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(models.BookmakerClick.clicked_at <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    clicks = query.all()

    # Group by bookmaker_key and count
    stats_map = {}
    for click in clicks:
        if click.bookmaker_key not in stats_map:
            stats_map[click.bookmaker_key] = {
                "bookmaker_key": click.bookmaker_key,
                "click_count": 0,
                "source_breakdown": {
                    "comparison": 0,
                    "betslip": 0
                }
            }

        stats_map[click.bookmaker_key]["click_count"] += 1

        if click.source in ("comparison", "betslip"):
            stats_map[click.bookmaker_key]["source_breakdown"][click.source] += 1

    return list(stats_map.values())

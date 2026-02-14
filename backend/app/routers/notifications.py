import os
import json
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")


@router.get("/notifications/vapid-key")
@limiter.limit("30/minute")
def get_vapid_key(request: Request):
    """Return the VAPID public key for push subscription."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications are not configured"
        )
    return {"vapid_key": VAPID_PUBLIC_KEY}


@router.post("/notifications/subscribe", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def subscribe_push(
    request: Request,
    body: schemas.PushSubscriptionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Save a push subscription for the current user."""
    subscription = body.subscription
    endpoint = subscription.get("endpoint", "")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Invalid subscription: missing endpoint")

    endpoint_hash = hashlib.sha256(endpoint.encode()).hexdigest()

    # Upsert: delete existing subscription with same endpoint, then create new
    existing = db.query(models.PushSubscription).filter(
        models.PushSubscription.user_id == user_id,
        models.PushSubscription.endpoint_hash == endpoint_hash,
    ).first()

    if existing:
        existing.subscription_json = json.dumps(subscription)
        db.commit()
        return {"message": "Subscription updated"}

    new_sub = models.PushSubscription(
        user_id=user_id,
        endpoint_hash=endpoint_hash,
        subscription_json=json.dumps(subscription),
    )
    db.add(new_sub)
    db.commit()

    logger.info(f"Push subscription created for user {user_id}")
    return {"message": "Subscription created"}


@router.delete("/notifications/unsubscribe")
@limiter.limit("10/minute")
def unsubscribe_push(
    request: Request,
    body: schemas.PushSubscriptionDelete,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Remove a push subscription for the current user."""
    endpoint_hash = hashlib.sha256(body.endpoint.encode()).hexdigest()

    deleted = db.query(models.PushSubscription).filter(
        models.PushSubscription.user_id == user_id,
        models.PushSubscription.endpoint_hash == endpoint_hash,
    ).delete(synchronize_session=False)

    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")

    logger.info(f"Push subscription removed for user {user_id}")
    return {"message": "Subscription removed"}

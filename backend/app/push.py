import os
import json
import logging
from datetime import datetime, timezone
from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session
from . import models

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:notifications@accapicks.com"}

if not VAPID_PRIVATE_KEY:
    logger.warning("VAPID_PRIVATE_KEY not configured — push notifications disabled")


def send_push(db: Session, user_id: int, payload: dict):
    """Send push notification to all of a user's subscriptions."""
    if not VAPID_PRIVATE_KEY:
        return

    subscriptions = db.query(models.PushSubscription).filter(
        models.PushSubscription.user_id == user_id
    ).all()

    for sub in subscriptions:
        try:
            subscription_info = json.loads(sub.subscription_json)
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            sub.last_used_at = datetime.now(timezone.utc)
        except WebPushException as e:
            if e.response and e.response.status_code == 410:
                # Subscription expired/unsubscribed — clean up
                logger.info(f"Removing expired push subscription {sub.id} for user {user_id}")
                db.delete(sub)
            else:
                logger.warning(f"Push failed for subscription {sub.id}: {e}")
        except Exception as e:
            logger.warning(f"Push error for subscription {sub.id}: {e}")

    try:
        db.commit()
    except Exception:
        db.rollback()


def send_push_to_group(db: Session, group_id: int, payload: dict, exclude_user_id: int = None):
    """Send push notification to all members of a group, optionally excluding one user."""
    if not VAPID_PRIVATE_KEY:
        return

    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id
    ).all()

    for member in members:
        if exclude_user_id and member.user_id == exclude_user_id:
            continue
        send_push(db, member.user_id, payload)

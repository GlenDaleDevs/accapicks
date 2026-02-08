import logging
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# Create a new group
@router.post("/groups", response_model=schemas.GroupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_group(
    request: Request,
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Create a new betting group"""

    # Limit groups per user
    membership_count = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user_id
    ).count()
    if membership_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can be in a maximum of 20 groups"
        )

    # Generate unique invite code with retry on collision
    for attempt in range(3):
        invite_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        new_group = models.Group(
            name=group.name,
            description=group.description,
            created_by=user_id,
            invite_code=invite_code
        )
        db.add(new_group)
        try:
            db.commit()
            db.refresh(new_group)
            break
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise HTTPException(status_code=500, detail="Failed to generate unique invite code")

    # Automatically add creator as admin member
    creator_member = models.GroupMember(
        group_id=new_group.id,
        user_id=user_id,
        role="admin"
    )

    db.add(creator_member)
    db.commit()

    return new_group


# Get all groups for current user
@router.get("/groups", response_model=list[schemas.GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get all groups the user is a member of"""

    # Get all group memberships for this user
    memberships = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user_id
    ).all()

    # If user has no memberships, return empty list
    if not memberships:
        return []

    # Get the actual groups
    group_ids = [m.group_id for m in memberships]
    groups = db.query(models.Group).filter(models.Group.id.in_(group_ids)).all()

    return groups


# Join a group using invite code
@router.post("/groups/join/{invite_code}")
@limiter.limit("10/minute")
def join_group(
    request: Request,
    invite_code: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Join a group using an invite code"""

    # Limit groups per user
    membership_count = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user_id
    ).count()
    if membership_count >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can be in a maximum of 20 groups"
        )

    # Find group by invite code
    group = db.query(models.Group).filter(models.Group.invite_code == invite_code).first()

    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check if user is already a member
    existing_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group.id,
        models.GroupMember.user_id == user_id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this group")

    # Limit members per group
    member_count = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group.id
    ).count()
    if member_count >= 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This group is full (maximum 50 members)"
        )

    # Add user as member
    new_member = models.GroupMember(
        group_id=group.id,
        user_id=user_id,
        role="member"
    )

    db.add(new_member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already a member of this group")

    return {"message": "Successfully joined group", "group": group.name}


# Get a single group by ID
@router.get("/groups/{group_id}", response_model=schemas.GroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get a single group by ID"""

    # Find the group
    group = db.query(models.Group).filter(models.Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify user is a member
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    return group


# Get members of a group
@router.get("/groups/{group_id}/members")
@limiter.limit("30/minute")
def get_group_members(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get all members of a group"""

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

    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id
    ).all()

    # Batch-query users to avoid N+1
    user_ids = [m.user_id for m in members]
    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    # Get user details for each member
    member_details = []
    for member in members:
        user = user_map.get(member.user_id)
        if user:
            member_details.append({
                "user_id": user.id,
                "username": user.username,
                "role": member.role,
                "joined_at": member.joined_at
            })

    return member_details


# Get group leaderboard
@router.get("/groups/{group_id}/leaderboard")
@limiter.limit("30/minute")
def get_group_leaderboard(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get leaderboard for a group showing user stats"""

    # Verify user is a member
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Start from all group members so everyone appears
    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id
    ).all()
    member_user_ids = [m.user_id for m in members]

    # Batch-query users
    users = db.query(models.User).filter(models.User.id.in_(member_user_ids)).all()
    user_map = {u.id: u for u in users}

    # Initialize stats for every member
    user_stats = {}
    for uid in member_user_ids:
        user_stats[uid] = {
            "total": 0,
            "won": 0,
            "lost": 0,
            "void": 0,
            "pending": 0,
            "won_bets": []
        }

    # Get all accas in this group
    accas = db.query(models.Acca).filter(models.Acca.group_id == group_id).all()
    acca_ids = [a.id for a in accas]

    # Accumulate bet stats
    if acca_ids:
        bets = db.query(models.Bet).filter(models.Bet.acca_id.in_(acca_ids)).all()

        for bet in bets:
            if bet.user_id not in user_stats:
                continue

            user_stats[bet.user_id]["total"] += 1

            if bet.result == "won":
                user_stats[bet.user_id]["won"] += 1
                user_stats[bet.user_id]["won_bets"].append(bet)
            elif bet.result == "lost":
                user_stats[bet.user_id]["lost"] += 1
            elif bet.result == "void":
                user_stats[bet.user_id]["void"] += 1
            else:
                user_stats[bet.user_id]["pending"] += 1

    # Build leaderboard
    leaderboard = []
    for uid, stats in user_stats.items():
        user = user_map.get(uid)
        if user:
            # Calculate win rate (excluding void and pending)
            settled = stats["won"] + stats["lost"]
            win_rate = (stats["won"] / settled * 100) if settled > 0 else 0

            # Calculate best_odds_won
            best_odds_won = 0.0
            for won_bet in stats["won_bets"]:
                try:
                    odds_value = float(won_bet.odds)
                    if odds_value > best_odds_won:
                        best_odds_won = odds_value
                except (ValueError, TypeError):
                    # Skip non-numeric odds
                    continue

            leaderboard.append({
                "user_id": user.id,
                "username": user.username,
                "total_bets": stats["total"],
                "won": stats["won"],
                "lost": stats["lost"],
                "void": stats["void"],
                "pending": stats["pending"],
                "win_rate": round(win_rate, 1),
                "best_odds_won": round(best_odds_won, 2)
            })

    # Sort by win_rate, won, -lost, best_odds_won (all descending)
    leaderboard.sort(key=lambda x: (x["win_rate"], x["won"], -x["lost"], x["best_odds_won"]), reverse=True)

    # Add rank field with proper tie handling
    for i, entry in enumerate(leaderboard):
        if i == 0:
            entry["rank"] = 1
        else:
            prev = leaderboard[i - 1]
            # Same rank if all tie-breaking fields are equal
            if (entry["win_rate"] == prev["win_rate"] and
                entry["won"] == prev["won"] and
                entry["lost"] == prev["lost"] and
                entry["best_odds_won"] == prev["best_odds_won"]):
                entry["rank"] = prev["rank"]
            else:
                entry["rank"] = i + 1

    return leaderboard


# Remove member endpoint (admin only)
@router.delete("/groups/{group_id}/members/{target_user_id}")
@limiter.limit("3/minute")
def remove_member(
    request: Request,
    group_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Remove a member from the group (admin only)"""

    # Cannot remove yourself
    if target_user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use leave-group to leave"
        )

    # Verify requesting user is a member
    requester_membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not requester_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Verify requesting user is admin
    if requester_membership.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove members"
        )

    # Find target user's membership
    target_membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == target_user_id
    ).first()

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user is not a member of this group"
        )

    # Cannot remove another admin
    if target_membership.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove another admin. They must leave voluntarily."
        )

    try:
        # Only delete bets from OPEN accas (preserve historical data in locked/settled)
        open_accas = db.query(models.Acca).filter(
            models.Acca.group_id == group_id,
            models.Acca.status == "open"
        ).all()
        if open_accas:
            open_acca_ids = [a.id for a in open_accas]
            db.query(models.Bet).filter(
                models.Bet.acca_id.in_(open_acca_ids),
                models.Bet.user_id == target_user_id
            ).delete(synchronize_session=False)

        # Delete the membership
        db.delete(target_membership)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )

    return {"message": "Member removed successfully"}


# Leave group endpoint
@router.delete("/groups/{group_id}/leave")
@limiter.limit("3/minute")
def leave_group(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Leave a group (destructive operation)"""

    try:
        # Verify user is a member
        membership = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.user_id == user_id
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group"
            )

        # Get the group
        group = db.query(models.Group).filter(models.Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )

        # Count other members
        other_members = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.user_id != user_id
        ).all()

        if not other_members:
            # User is sole member - delete everything
            # Delete all bets in group's accas
            acca_ids = [a.id for a in group.accas]
            if acca_ids:
                db.query(models.Bet).filter(models.Bet.acca_id.in_(acca_ids)).delete(synchronize_session=False)
            # Delete all accas
            db.query(models.Acca).filter(models.Acca.group_id == group_id).delete(synchronize_session=False)
            # Delete all memberships
            db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).delete(synchronize_session=False)
            # Delete group
            db.delete(group)
        else:
            # Other members exist
            # If user is admin, promote longest-serving member
            if membership.role == "admin":
                new_admin = min(other_members, key=lambda m: m.joined_at)
                new_admin.role = "admin"

                # Transfer Group.created_by if needed
                if group.created_by == user_id:
                    group.created_by = new_admin.user_id

                # Transfer Acca.created_by for accas in this group
                db.query(models.Acca).filter(
                    models.Acca.group_id == group_id,
                    models.Acca.created_by == user_id
                ).update({"created_by": new_admin.user_id}, synchronize_session=False)

            # Only delete bets from OPEN accas (preserve historical data in locked/settled)
            open_accas = db.query(models.Acca).filter(
                models.Acca.group_id == group_id,
                models.Acca.status == "open"
            ).all()
            if open_accas:
                open_acca_ids = [a.id for a in open_accas]
                db.query(models.Bet).filter(
                    models.Bet.acca_id.in_(open_acca_ids),
                    models.Bet.user_id == user_id
                ).delete(synchronize_session=False)

            # Delete the membership
            db.delete(membership)

        db.commit()
        return {"message": "Left group successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to leave group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave group"
        )

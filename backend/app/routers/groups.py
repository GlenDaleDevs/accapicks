import logging
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
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
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise HTTPException(status_code=500, detail="Failed to generate unique invite code")

    # Automatically add creator as admin member (same transaction)
    creator_member = models.GroupMember(
        group_id=new_group.id,
        user_id=user_id,
        role="admin"
    )
    db.add(creator_member)

    try:
        db.commit()
        db.refresh(new_group)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create group")

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
    group = db.query(models.Group).filter(func.upper(models.Group.invite_code) == invite_code.upper()).first()

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

    # Recalculate locks_at for open accas where rejoining user has orphaned bets
    open_accas = db.query(models.Acca).filter(
        models.Acca.group_id == group.id,
        models.Acca.status == "open"
    ).all()
    for open_acca in open_accas:
        has_orphaned = db.query(models.Bet).filter(
            models.Bet.acca_id == open_acca.id,
            models.Bet.user_id == user_id,
        ).first()
        if has_orphaned:
            # Recalculate including all current member bets
            all_bets = db.query(models.Bet).filter(
                models.Bet.acca_id == open_acca.id,
                models.Bet.commence_time.isnot(None),
            ).all()
            # Now all bets from this user are "un-orphaned" since they're a member again
            member_ids = [m.user_id for m in db.query(models.GroupMember.user_id).filter(
                models.GroupMember.group_id == group.id
            ).all()]
            member_bets = [b for b in all_bets if b.user_id in member_ids]
            if member_bets:
                open_acca.locks_at = min(b.commence_time for b in member_bets)
            else:
                open_acca.locks_at = None
    db.commit()

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


# Update group settings
@router.patch("/groups/{group_id}", response_model=schemas.GroupResponse)
@limiter.limit("10/minute")
def update_group(
    request: Request,
    group_id: int,
    update: schemas.GroupUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Update a group's settings. Admin only."""

    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    if membership.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a group admin can change these settings"
        )

    # Only what was actually sent, so a nullable field can be cleared without
    # that being mistaken for "field omitted". GroupUpdate carries no fields at
    # present — see its docstring.
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    db.commit()
    db.refresh(group)
    return group


def _group_or_404(db, group_id, user_id):
    """Fetch a group and confirm the caller is a member."""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

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
        # Recalculate locks_at for open accas, excluding removed user's bets
        open_accas = db.query(models.Acca).filter(
            models.Acca.group_id == group_id,
            models.Acca.status == "open"
        ).all()
        for open_acca in open_accas:
            remaining_bets = db.query(models.Bet).filter(
                models.Bet.acca_id == open_acca.id,
                models.Bet.commence_time.isnot(None),
                models.Bet.user_id != target_user_id,
            ).all()
            if remaining_bets:
                open_acca.locks_at = min(b.commence_time for b in remaining_bets)
            else:
                open_acca.locks_at = None

        # Delete the membership (bets are preserved as orphans)
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

            # Recalculate locks_at for open accas, excluding leaving user's bets
            open_accas = db.query(models.Acca).filter(
                models.Acca.group_id == group_id,
                models.Acca.status == "open"
            ).all()
            for open_acca in open_accas:
                remaining_bets = db.query(models.Bet).filter(
                    models.Bet.acca_id == open_acca.id,
                    models.Bet.commence_time.isnot(None),
                    models.Bet.user_id != user_id,
                ).all()
                if remaining_bets:
                    open_acca.locks_at = min(b.commence_time for b in remaining_bets)
                else:
                    open_acca.locks_at = None

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

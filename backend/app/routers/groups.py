import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter

router = APIRouter()


# Create a new group
@router.post("/groups", response_model=schemas.GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Create a new betting group"""

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

    # Add user as member
    new_member = models.GroupMember(
        group_id=group.id,
        user_id=user_id,
        role="member"
    )

    db.add(new_member)
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


# Get members of a group
@router.get("/groups/{group_id}/members")
def get_group_members(
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
def get_group_leaderboard(
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

    # Get all accas in this group
    accas = db.query(models.Acca).filter(models.Acca.group_id == group_id).all()
    acca_ids = [a.id for a in accas]

    if not acca_ids:
        return []

    # Get all bets for these accas
    bets = db.query(models.Bet).filter(models.Bet.acca_id.in_(acca_ids)).all()

    # Calculate stats per user
    user_stats = {}
    for bet in bets:
        if bet.user_id not in user_stats:
            user_stats[bet.user_id] = {
                "total": 0,
                "won": 0,
                "lost": 0,
                "void": 0,
                "pending": 0
            }

        user_stats[bet.user_id]["total"] += 1

        if bet.result == "won":
            user_stats[bet.user_id]["won"] += 1
        elif bet.result == "lost":
            user_stats[bet.user_id]["lost"] += 1
        elif bet.result == "void":
            user_stats[bet.user_id]["void"] += 1
        else:
            user_stats[bet.user_id]["pending"] += 1

    # Batch-query users to avoid N+1
    user_ids = list(user_stats.keys())
    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    # Build leaderboard
    leaderboard = []
    for uid, stats in user_stats.items():
        user = user_map.get(uid)
        if user:
            # Calculate win rate (excluding void and pending)
            settled = stats["won"] + stats["lost"]
            win_rate = (stats["won"] / settled * 100) if settled > 0 else 0

            leaderboard.append({
                "user_id": user.id,
                "username": user.username,
                "total_bets": stats["total"],
                "won": stats["won"],
                "lost": stats["lost"],
                "void": stats["void"],
                "pending": stats["pending"],
                "win_rate": round(win_rate, 1)
            })

    # Sort by win rate (then by total wins as tiebreaker)
    leaderboard.sort(key=lambda x: (x["win_rate"], x["won"]), reverse=True)

    return leaderboard

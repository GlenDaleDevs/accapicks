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

    # Calculate streaks per user
    # Build pick_history: user_id -> [(commence_time, result)] for settled bets only
    pick_history = {uid: [] for uid in member_user_ids}
    if acca_ids:
        for bet in bets:
            if (bet.user_id in pick_history
                    and bet.result in ("won", "lost")
                    and bet.commence_time is not None):
                pick_history[bet.user_id].append((bet.commence_time, bet.result))

    streaks = {}
    for uid, history in pick_history.items():
        if not history:
            streaks[uid] = {"streak_count": 0, "streak_type": "none"}
            continue
        # Sort descending by commence_time (most recent first)
        history.sort(key=lambda x: x[0], reverse=True)
        streak_type = "win" if history[0][1] == "won" else "loss"
        count = 0
        for _commence_time, result in history:
            entry_type = "win" if result == "won" else "loss"
            if entry_type == streak_type:
                count += 1
            else:
                break
        streaks[uid] = {"streak_count": count, "streak_type": streak_type}

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
                "best_odds_won": round(best_odds_won, 2),
                "streak_count": streaks.get(uid, {}).get("streak_count", 0),
                "streak_type": streaks.get(uid, {}).get("streak_type", "none")
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


# Get member picks
@router.get("/groups/{group_id}/members/{member_id}/picks")
@limiter.limit("30/minute")
def get_member_picks(
    request: Request,
    group_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get all picks for a specific member in a group"""

    # Verify requesting user is a member
    membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )

    # Verify target member exists as current member OR has bets in group accas
    target_membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == member_id
    ).first()

    # Get all accas in this group
    accas = db.query(models.Acca).filter(models.Acca.group_id == group_id).all()
    acca_ids = [a.id for a in accas] if accas else []

    # Check if target user has bets in this group
    has_bets = False
    if acca_ids:
        has_bets = db.query(models.Bet).filter(
            models.Bet.acca_id.in_(acca_ids),
            models.Bet.user_id == member_id
        ).first() is not None

    if not target_membership and not has_bets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Get target user details
    target_user = db.query(models.User).filter(models.User.id == member_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get all bets for this member in this group
    bets = []
    if acca_ids:
        bets = db.query(models.Bet).filter(
            models.Bet.acca_id.in_(acca_ids),
            models.Bet.user_id == member_id
        ).order_by(models.Bet.created_at.desc()).all()

    # Build acca map for efficient lookup
    acca_map = {a.id: a for a in accas}

    # Initialize summary stats
    summary = {
        "total_bets": len(bets),
        "won": 0,
        "lost": 0,
        "void": 0,
        "pending": 0,
        "win_rate": 0.0,
        "best_odds_won": 0.0
    }

    won_bets = []
    picks = []

    for bet in bets:
        # Count by result
        if bet.result == "won":
            summary["won"] += 1
            won_bets.append(bet)
        elif bet.result == "lost":
            summary["lost"] += 1
        elif bet.result == "void":
            summary["void"] += 1
        else:
            summary["pending"] += 1

        # Build pick entry
        acca = acca_map.get(bet.acca_id)
        picks.append({
            "bet_id": bet.id,
            "acca_id": bet.acca_id,
            "acca_name": acca.name if acca else None,
            "acca_round_number": acca.round_number if acca else None,
            "acca_status": acca.status if acca else None,
            "description": bet.description,
            "odds": bet.odds,
            "result": bet.result,
            "home_team": bet.home_team,
            "away_team": bet.away_team,
            "pick_type": bet.pick_type,
            "sport_key": bet.sport_key,
            "commence_time": bet.commence_time.isoformat() if bet.commence_time else None,
            "created_at": bet.created_at.isoformat() if bet.created_at else None
        })

    # Calculate win_rate
    settled = summary["won"] + summary["lost"]
    if settled > 0:
        summary["win_rate"] = round(summary["won"] / settled * 100, 1)

    # Calculate best_odds_won
    for won_bet in won_bets:
        try:
            odds_value = float(won_bet.odds)
            if odds_value > summary["best_odds_won"]:
                summary["best_odds_won"] = odds_value
        except (ValueError, TypeError):
            continue

    summary["best_odds_won"] = round(summary["best_odds_won"], 2)

    # Calculate longest winning streak
    settled_picks = [
        (bet.commence_time, bet.result)
        for bet in bets
        if bet.result in ("won", "lost") and bet.commence_time is not None
    ]
    settled_picks.sort(key=lambda x: x[0])  # chronological order
    longest_win_streak = 0
    current_win_streak = 0
    for _ct, result in settled_picks:
        if result == "won":
            current_win_streak += 1
            if current_win_streak > longest_win_streak:
                longest_win_streak = current_win_streak
        else:
            current_win_streak = 0
    summary["longest_win_streak"] = longest_win_streak

    return {
        "user_id": target_user.id,
        "username": target_user.username,
        "summary": summary,
        "picks": picks
    }


# Get group acca stats
@router.get("/groups/{group_id}/acca-stats")
@limiter.limit("30/minute")
def get_acca_stats(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """Get statistics about accas in a group"""

    # Verify requesting user is a member
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

    # Count accas by status
    total_accas = len(accas)
    won_accas = 0
    lost_accas = 0
    settled_accas = 0
    open_accas = 0
    locked_accas = 0

    for acca in accas:
        if acca.status == "won":
            won_accas += 1
            settled_accas += 1
        elif acca.status == "lost":
            lost_accas += 1
            settled_accas += 1
        elif acca.status == "settled":
            settled_accas += 1
        elif acca.status == "open":
            open_accas += 1
        elif acca.status == "locked":
            locked_accas += 1

    # Calculate success rate
    success_rate = 0.0
    if won_accas + lost_accas > 0:
        success_rate = round(won_accas / (won_accas + lost_accas) * 100, 1)

    return {
        "total_accas": total_accas,
        "won_accas": won_accas,
        "lost_accas": lost_accas,
        "settled_accas": settled_accas,
        "open_accas": open_accas,
        "locked_accas": locked_accas,
        "success_rate": success_rate
    }


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

"""Group statistics: leaderboard, member pick history, acca stats.

Split out of routers/groups.py, which had grown to a thousand lines — these
three endpoints and their ranking helper are the read-only stats half. All of
them scope to the group's season via season.py; per gotchas.md the season
boundary must be applied to all three together or they contradict each other.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .. import models, season
from ..database import get_db
from .auth import get_current_user
from ..limiter import limiter
from ..timeutils import as_utc
from .groups import _group_or_404

router = APIRouter()


def _ranked(member_user_ids, bets):
    """Rank members over a subset of bets, using the same sort key and tie
    handling as the leaderboard itself.

    Returns (rank_by_user, settled_count_by_user). The settled count is what
    lets the caller suppress meaningless movement: someone with no settled
    picks in a window sits in the big 0/0 tie block, and their position there
    is an artefact of dict ordering, not form.
    """
    stats = {uid: {"won": 0, "lost": 0, "best": 0.0} for uid in member_user_ids}
    for bet in bets:
        s = stats.get(bet.user_id)
        if s is None:
            continue
        if bet.result == "won":
            s["won"] += 1
            try:
                odds_value = float(bet.odds)
                if odds_value > s["best"]:
                    s["best"] = odds_value
            except (ValueError, TypeError):
                pass
        elif bet.result == "lost":
            s["lost"] += 1

    rows = []
    for uid, s in stats.items():
        settled = s["won"] + s["lost"]
        win_rate = (s["won"] / settled * 100) if settled > 0 else 0
        rows.append({
            "user_id": uid,
            "win_rate": round(win_rate, 1),
            "won": s["won"],
            "lost": s["lost"],
            "best_odds_won": round(s["best"], 2),
            "settled": settled,
        })

    rows.sort(key=lambda x: (x["win_rate"], x["won"], -x["lost"], x["best_odds_won"]), reverse=True)

    ranks, settled_counts = {}, {}
    for i, row in enumerate(rows):
        if i == 0:
            row["rank"] = 1
        else:
            prev = rows[i - 1]
            tied = (row["win_rate"] == prev["win_rate"] and row["won"] == prev["won"]
                    and row["lost"] == prev["lost"] and row["best_odds_won"] == prev["best_odds_won"])
            row["rank"] = prev["rank"] if tied else i + 1
        ranks[row["user_id"]] = row["rank"]
        settled_counts[row["user_id"]] = row["settled"]
    return ranks, settled_counts


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

    group = _group_or_404(db, group_id, user_id)

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

    # Season-scoped: everything downstream — stats, streaks and the movement
    # window — derives from these accas, so this is the only place the boundary
    # has to be applied.
    accas = season.season_accas(db, group)
    acca_ids = [a.id for a in accas]

    # Accumulate bet stats
    bets = []
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

    # ---- Position movement ----
    # Baseline is the most recent round for which *every* earlier round has
    # also settled. Accas settle when their last match resolves, so with
    # concurrent weeks round N can settle before N-1; taking max(settled)
    # would compare against a window containing an unsettled week.
    # Position, not round_number: accas can now be created out of date order (a
    # midweek one-off slotted in before an already-open Saturday week), so the
    # number no longer implies chronology. first_match_date does.
    ordered = season.chronological(a for a in accas if a.first_match_date is not None)
    position_by_acca = {a.id: i for i, a in enumerate(ordered)}
    settled_positions = {
        position_by_acca[a.id] for a in ordered
        if a.status in ("won", "lost", "settled")
    }
    fully_settled_prefix = []
    for position in range(len(ordered)):
        if position in settled_positions:
            fully_settled_prefix.append(position)
        else:
            break

    rank_change = {}
    # Fewer than two settled rounds means there is nothing to move *from*.
    if len(fully_settled_prefix) >= 2:
        now_cut = fully_settled_prefix[-1]
        prev_cut = fully_settled_prefix[-2]

        def window(cutoff):
            return [b for b in bets
                    if position_by_acca.get(b.acca_id) is not None
                    and position_by_acca[b.acca_id] <= cutoff]

        now_ranks, now_settled = _ranked(member_user_ids, window(now_cut))
        prev_ranks, prev_settled = _ranked(member_user_ids, window(prev_cut))

        for uid in member_user_ids:
            # Needs settled picks in BOTH windows. Otherwise a mid-season
            # joiner winning their first pick jumps 0% -> 100% and flashes a
            # full-table climb that means nothing.
            if now_settled.get(uid, 0) > 0 and prev_settled.get(uid, 0) > 0:
                rank_change[uid] = prev_ranks[uid] - now_ranks[uid]

    for entry in leaderboard:
        entry["rank_change"] = rank_change.get(entry["user_id"])

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
    """Get a member's picks for the current season in this group"""

    group = _group_or_404(db, group_id, user_id)

    # Verify target member exists as current member OR has bets in group accas
    target_membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == member_id
    ).first()

    # Season-scoped, so tapping a row that reads 3–1 shows three wins and a loss
    # rather than a career history that looks like a different person.
    accas = season.season_accas(db, group)
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
    week_numbers = season.week_numbers(accas)

    # Leg counts per acca, so the profile can explain *why* an acca lost when
    # this member's own pick won — "Acca lost — 4 of 5 landed".
    acca_legs = {}
    acca_landed = {}
    if acca_ids:
        leg_rows = db.query(
            models.Bet.acca_id,
            func.count(models.Bet.id),
            func.sum(case((models.Bet.result == "won", 1), else_=0)),
        ).filter(models.Bet.acca_id.in_(acca_ids)).group_by(models.Bet.acca_id).all()
        for acca_id, total, won in leg_rows:
            acca_legs[acca_id] = total or 0
            acca_landed[acca_id] = int(won or 0)

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
            "acca_week_number": week_numbers.get(bet.acca_id),
            "acca_status": acca.status if acca else None,
            "acca_legs": acca_legs.get(bet.acca_id, 0),
            "acca_landed": acca_landed.get(bet.acca_id, 0),
            "description": bet.description,
            "odds": bet.odds,
            "result": bet.result,
            "home_team": bet.home_team,
            "away_team": bet.away_team,
            "pick_type": bet.pick_type,
            "sport_key": bet.sport_key,
            # as_utc first: a naive value from SQLite would serialise without an
            # offset, which JavaScript reads as local time.
            "commence_time": as_utc(bet.commence_time).isoformat() if bet.commence_time else None,
            "created_at": as_utc(bet.created_at).isoformat() if bet.created_at else None
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
    """Get statistics about this season's accas in a group"""

    group = _group_or_404(db, group_id, user_id)

    # Same scope as the leaderboard — this bar sits on the same card, so the
    # two must not disagree about how many accas there have been.
    accas = season.season_accas(db, group)

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

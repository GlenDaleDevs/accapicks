"""Season-scoped group leaderboard rows.

Lives apart from routers/groupstats.py so the device router can reuse it
without importing another router. Starts from ALL members (0-bet ones
included), scopes bets through season.season_accas, and ranks with tie
handling; see gotchas.md on keeping the season boundary consistent.
"""
from . import models, season


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


def leaderboard_rows(db, group) -> list[dict]:
    """Full sorted leaderboard rows (rank and rank_change included) for a group."""

    # Start from all group members so everyone appears
    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group.id
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

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from . import models
from .odds_api import get_scores
from .normalization import normalize

logger = logging.getLogger(__name__)


def settle_locked_accas(db: Session):
    """
    Automatically settle locked accas by fetching scores from The-Odds-API.

    Process:
    1. Find all locked accas
    2. For each acca, get unsettled bets with event_id
    3. Fetch scores for those events (only if match finished 3+ hours ago)
    4. Compare actual result with bet pick_type
    5. Update bet results (won/lost)
    6. Check if all acca bets are settled, then update acca status

    Runs as a background task, commits after each acca to isolate failures.
    """
    now = datetime.now(timezone.utc)

    # Find all locked accas
    locked_accas = db.query(models.Acca).filter(models.Acca.status == "locked").all()

    for acca in locked_accas:
        try:
            # Get unsettled bets with event_id (auto-settleable bets)
            unsettled_bets = db.query(models.Bet).filter(
                models.Bet.acca_id == acca.id,
                models.Bet.result.is_(None),
                models.Bet.event_id.isnot(None),
                models.Bet.commence_time.isnot(None)
            ).all()

            # Auto-void legacy bets (no event_id) that are 7+ days old
            legacy_bets = db.query(models.Bet).filter(
                models.Bet.acca_id == acca.id,
                models.Bet.result.is_(None),
                models.Bet.event_id.is_(None),
            ).all()

            for bet in legacy_bets:
                if not bet.commence_time or (now - bet.commence_time) >= timedelta(days=7):
                    logger.info(f"Auto-voiding legacy bet {bet.id} (no event_id, acca {acca.id})")
                    bet.result = "void"

            if not unsettled_bets:
                # No unsettled auto-settleable bets — check if acca can be finalized
                all_bets = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).all()
                if all_bets and all(bet.result is not None for bet in all_bets):
                    non_void_bets = [bet for bet in all_bets if bet.result != "void"]
                    if not non_void_bets:
                        acca.status = "settled"
                    elif all(bet.result == "won" for bet in non_void_bets):
                        acca.status = "won"
                    elif any(bet.result == "lost" for bet in all_bets):
                        acca.status = "lost"
                    else:
                        acca.status = "settled"
                    db.commit()
                continue

            # Filter to only bets whose matches should be finished (3+ hours past kickoff)
            ready_bets = []
            for bet in unsettled_bets:
                time_since_kickoff = now - bet.commence_time
                if time_since_kickoff >= timedelta(hours=3):
                    ready_bets.append(bet)

            if not ready_bets:
                # No bets ready to settle yet
                continue

            # Collect unique sport_keys for ready bets
            sport_keys = set(bet.sport_key for bet in ready_bets if bet.sport_key)

            # Calculate days_from based on oldest ready bet (min 3, max 14)
            oldest_kickoff = min(bet.commence_time for bet in ready_bets)
            days_since_oldest = max(3, min(14, int((now - oldest_kickoff).total_seconds() / 86400) + 1))

            # Fetch scores for each sport
            scores_by_event = {}
            for sport_key in sport_keys:
                scores = get_scores(sport_key, days_from=days_since_oldest)
                for score_obj in scores:
                    scores_by_event[score_obj['id']] = score_obj

            # Process each ready bet
            for bet in ready_bets:
                score_data = scores_by_event.get(bet.event_id)

                if not score_data:
                    time_since_kickoff = now - bet.commence_time
                    if time_since_kickoff >= timedelta(hours=72):
                        logger.warning(f"Bet {bet.id} (event {bet.event_id}): no score data after {time_since_kickoff.total_seconds() / 3600:.0f}h")
                    else:
                        logger.info(f"Bet {bet.id} (event {bet.event_id}): awaiting score data ({time_since_kickoff.total_seconds() / 3600:.0f}h since kickoff)")
                    continue

                # Check if match is completed
                if not score_data.get('completed'):
                    # Auto-void if 48+ hours past kickoff and still not completed
                    time_since_kickoff = now - bet.commence_time
                    if time_since_kickoff >= timedelta(hours=48):
                        logger.warning(f"Bet {bet.id} (event {bet.event_id}): match not completed after 48h, voiding")
                        bet.result = "void"
                    continue

                # Extract scores
                scores_list = score_data.get('scores')
                if not scores_list or len(scores_list) < 2:
                    continue

                # Parse home and away scores
                home_score = None
                away_score = None

                for team_score in scores_list:
                    team_name = team_score.get('name', '')
                    score_value = team_score.get('score')

                    if score_value is None:
                        continue

                    try:
                        score_int = int(score_value)
                    except (ValueError, TypeError):
                        continue

                    # Match team name to home/away (normalized)
                    if normalize(team_name) == normalize(bet.home_team):
                        home_score = score_int
                    elif normalize(team_name) == normalize(bet.away_team):
                        away_score = score_int

                if home_score is None or away_score is None:
                    logger.warning(f"Could not parse scores for bet {bet.id} (event {bet.event_id})")
                    continue

                # Determine actual result
                if home_score > away_score:
                    actual_result = "home"
                elif away_score > home_score:
                    actual_result = "away"
                else:
                    actual_result = "draw"

                # Compare with bet pick_type
                if bet.pick_type == actual_result:
                    bet.result = "won"
                else:
                    bet.result = "lost"

            # After processing all ready bets, check if entire acca is settled
            all_bets = db.query(models.Bet).filter(models.Bet.acca_id == acca.id).all()

            if all(bet.result is not None for bet in all_bets):
                # All bets have a result - determine acca status
                non_void_bets = [bet for bet in all_bets if bet.result != "void"]

                if not non_void_bets:
                    # All bets voided (edge case)
                    acca.status = "settled"
                elif all(bet.result == "won" for bet in non_void_bets):
                    # All non-void bets won
                    acca.status = "won"
                elif any(bet.result == "lost" for bet in all_bets):
                    # Any bet lost means acca lost
                    acca.status = "lost"
                else:
                    # Mixed or unclear - mark as settled
                    acca.status = "settled"

            # Commit this acca's changes
            db.commit()

        except Exception as e:
            logger.error(f"Error settling acca {acca.id}: {e}")
            db.rollback()

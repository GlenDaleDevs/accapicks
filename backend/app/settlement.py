import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from . import models
from .odds_api import get_scores

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

            if not unsettled_bets:
                # No unsettled auto-settleable bets for this acca
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

            # Fetch scores for each sport
            scores_by_event = {}
            for sport_key in sport_keys:
                scores = get_scores(sport_key, days_from=3)
                for score_obj in scores:
                    scores_by_event[score_obj['id']] = score_obj

            # Process each ready bet
            for bet in ready_bets:
                score_data = scores_by_event.get(bet.event_id)

                if not score_data:
                    # Score not found - check if it's been >72 hours
                    time_since_kickoff = now - bet.commence_time
                    if time_since_kickoff >= timedelta(hours=72):
                        logger.warning(f"Bet {bet.id} (event {bet.event_id}) not settled after 72 hours. Manual review required.")
                    continue

                # Check if match is completed
                if not score_data.get('completed'):
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

                    # Match team name to home/away
                    if team_name == bet.home_team:
                        home_score = score_int
                    elif team_name == bet.away_team:
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

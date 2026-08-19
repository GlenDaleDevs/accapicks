"""Bookmaker comparison for an acca's total odds.

Split out of odds_api.py, which is the fetch/cache/format layer; this is the
consumer that walks the cached odds. It reads them only through
odds_api.fresh_cached_odds()/fresh_cached_btts(), so the caches stay private
to the fetch layer. Best-effort by design — the API is a third-party
aggregator with incomplete coverage (see gotchas.md).
"""
import logging

from . import odds_api

logger = logging.getLogger(__name__)


def compare_bookmakers_for_acca(bets_with_odds):
    """
    Compare total acca odds across all bookmakers for a list of bets.

    Args:
        bets_with_odds: List of (description, picked_odds) tuples

    Returns:
        Dictionary with bookmaker comparisons
    """
    if not bets_with_odds:
        return {}

    bet_descriptions = [desc for desc, _ in bets_with_odds]
    picked_odds = [odds for _, odds in bets_with_odds]

    # Parse team names from bet descriptions
    parsed_bets = []
    for bet_desc in bet_descriptions:
        bet_lower = bet_desc.lower().strip()

        # Check for BTTS bets first
        if bet_lower.startswith("btts yes - "):
            teams_part = bet_desc[len("BTTS Yes - "):]  # "TeamA vs TeamB"
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "btts",
                "outcome_name": "Yes",
                "team": None,
                "is_draw": False,
                "match_teams": teams_part
            })
            continue
        elif bet_lower.startswith("btts no - "):
            teams_part = bet_desc[len("BTTS No - "):]
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "btts",
                "outcome_name": "No",
                "team": None,
                "is_draw": False,
                "match_teams": teams_part
            })
            continue

        # Check for totals bets
        if bet_lower.startswith("over 2.5 goals - "):
            teams_part = bet_desc[len("Over 2.5 Goals - "):]
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "totals",
                "outcome_name": "Over",
                "team": None,
                "is_draw": False,
                "match_teams": teams_part
            })
            continue
        elif bet_lower.startswith("under 2.5 goals - "):
            teams_part = bet_desc[len("Under 2.5 Goals - "):]
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "totals",
                "outcome_name": "Under",
                "team": None,
                "is_draw": False,
                "match_teams": teams_part
            })
            continue

        # Otherwise, parse as h2h bet
        team_name = bet_desc.strip()
        if " to win" in bet_lower:
            team_name = bet_desc[:bet_lower.index(" to win")].strip()
        elif " win" == bet_lower[-4:]:
            team_name = bet_desc[:-4].strip()

        # Check if it's a draw bet
        is_draw = bet_lower in ["draw", "the draw"] or bet_lower.startswith("draw - ")
        draw_teams = None
        if is_draw and " - " in bet_desc:
            draw_teams = bet_desc.split(" - ", 1)[1]  # "TeamA vs TeamB"
        parsed_bets.append({
            "original": bet_desc,
            "market_type": "h2h",
            "outcome_name": "Draw" if is_draw else team_name,
            "team": team_name,
            "is_draw": is_draw,
            "match_teams": draw_teams
        })

    # Collect all cached matches across all sports
    all_matches = []
    for _sport_key, matches in odds_api.fresh_cached_odds():
        all_matches.extend(matches)

    if not all_matches:
        return {}

    # Find odds for each bet
    bet_odds_by_bookmaker = {}  # { bookmaker_key: { leg_index: price } }

    for leg_index, parsed_bet in enumerate(parsed_bets):
        market_type = parsed_bet["market_type"]
        outcome_name = parsed_bet["outcome_name"]
        team = parsed_bet.get("team")
        is_draw = parsed_bet.get("is_draw", False)

        # Find the match containing this bet
        matched_odds = None
        for match in all_matches:
            home = match.get("home_team", "")
            away = match.get("away_team", "")

            # For h2h bets, check if this match contains the team or draw
            # For btts/totals/draws, match by team names from bet description
            if market_type == "h2h" and not is_draw:
                if team.lower() not in [home.lower(), away.lower()]:
                    continue
            elif market_type in ("btts", "totals") or is_draw:
                # Match by team names from bet description
                match_teams = parsed_bet.get("match_teams", "")
                if " vs " in match_teams.lower():
                    bet_home, bet_away = match_teams.lower().split(" vs ", 1)
                    bet_home = bet_home.strip()
                    bet_away = bet_away.strip()
                    if not (bet_home == home.lower() and bet_away == away.lower()):
                        continue
                else:
                    continue

            # Extract odds from all bookmakers for this match
            for bookmaker in match.get("bookmakers", []):
                bookie_key = bookmaker.get("key")
                markets = bookmaker.get("markets", [])

                # Find the correct market based on market_type
                target_market = next((m for m in markets if m.get("key") == market_type), None)
                if not target_market:
                    continue

                outcomes = target_market.get("outcomes", [])

                # Find the specific outcome
                if market_type == "h2h":
                    if is_draw:
                        outcome = next((o for o in outcomes if o.get("name", "").lower() == "draw"), None)
                    else:
                        outcome = next((o for o in outcomes if o.get("name", "").lower() == team.lower()), None)
                elif market_type == "btts":
                    outcome = next((o for o in outcomes if o.get("name") == outcome_name), None)
                elif market_type == "totals":
                    # Match by name and point (2.5)
                    outcome = next((o for o in outcomes if o.get("name") == outcome_name and o.get("point") == 2.5), None)
                else:
                    outcome = None

                if outcome and "price" in outcome:
                    if bookie_key not in bet_odds_by_bookmaker:
                        bet_odds_by_bookmaker[bookie_key] = {}
                    bet_odds_by_bookmaker[bookie_key][leg_index] = outcome["price"]

            # If btts and no odds found in regular cache, check the per-event cache
            if market_type == "btts":
                event_id = match.get("id")
                btts_bookmakers = odds_api.fresh_cached_btts(event_id) if event_id else None
                if btts_bookmakers:
                    for bookmaker in btts_bookmakers:
                        bookie_key = bookmaker.get("key")
                        for mkt in bookmaker.get("markets", []):
                            if mkt.get("key") == "btts":
                                outcome = next((o for o in mkt.get("outcomes", []) if o.get("name") == outcome_name), None)
                                if outcome and "price" in outcome:
                                    if bookie_key not in bet_odds_by_bookmaker:
                                        bet_odds_by_bookmaker[bookie_key] = {}
                                    bet_odds_by_bookmaker[bookie_key][leg_index] = outcome["price"]

            # We matched the correct event via team filtering above — stop
            matched_odds = True
            break

        # If this bet couldn't be matched, we can't build a full acca
        if not matched_odds:
            continue

    # Calculate total acca odds — use estimates for missing legs
    result = {}
    num_legs = len(parsed_bets)

    for bookie_key, odds_dict in bet_odds_by_bookmaker.items():
        total_odds = 1.0
        estimated = False
        for i in range(num_legs):
            if i in odds_dict:
                total_odds *= odds_dict[i]
            else:
                total_odds *= picked_odds[i] * odds_api.COMPARISON_ESTIMATE_HAIRCUT
                estimated = True

        result[bookie_key] = {
            "total_odds": round(total_odds, 2),
            "available": True,
            "estimated": estimated
        }

    return result

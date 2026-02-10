import requests
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ODDS_API_KEY = os.getenv('ODDS_API_KEY')
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Simple in-memory cache: { sport_key: { "data": [...], "timestamp": float } }
_cache = {}
_scores_cache = {}  # Separate cache for scores
CACHE_TTL_SECONDS = int(os.getenv('ODDS_CACHE_TTL', '7200'))  # 2 hours default
SCORES_CACHE_TTL_SECONDS = 600  # 10 minutes for scores
ODDS_REGIONS = os.getenv('ODDS_REGIONS', 'uk')
ODDS_MARKETS = os.getenv('ODDS_MARKETS', 'h2h,btts,totals')

def get_football_matches(sport='soccer_epl'):
    """
    Get upcoming football matches with odds.
    Results are cached for 5 minutes to reduce API usage.

    sport options:
    - soccer_epl (Premier League)
    - soccer_spain_la_liga (La Liga)
    - soccer_germany_bundesliga (Bundesliga)
    - soccer_italy_serie_a (Serie A)
    - soccer_france_ligue_one (Ligue 1)
    """
    # Check cache
    if sport in _cache:
        age = time.time() - _cache[sport]["timestamp"]
        if age < CACHE_TTL_SECONDS:
            return _cache[sport]["data"]

    url = f'{ODDS_API_BASE_URL}/sports/{sport}/odds/'

    params = {
        'apiKey': ODDS_API_KEY,
        'regions': ODDS_REGIONS,
        'markets': ODDS_MARKETS,
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # Store in cache
        _cache[sport] = {"data": data, "timestamp": time.time()}
        return data
    except Exception as e:
        logger.error(f"Error fetching odds for {sport}: {e}")
        return []

def format_match_for_display(match, league=None):
    """Format a match into a readable structure"""
    home_team = match['home_team']
    away_team = match['away_team']
    commence_time = match['commence_time']

    # Get odds from first bookmaker (usually Bet365)
    bookmaker = match['bookmakers'][0] if match.get('bookmakers') else None

    if not bookmaker:
        return None

    # Initialize odds
    home_odds = None
    away_odds = None
    draw_odds = None
    btts_yes = None
    btts_no = None
    over_2_5 = None
    under_2_5 = None
    totals_line = None

    # Loop through markets to extract odds
    for market in bookmaker.get('markets', []):
        market_key = market.get('key')
        outcomes = market.get('outcomes', [])

        if market_key == 'h2h':
            # Extract h2h outcomes
            home_odds = next((o['price'] for o in outcomes if o['name'] == home_team), None)
            away_odds = next((o['price'] for o in outcomes if o['name'] == away_team), None)
            draw_odds = next((o['price'] for o in outcomes if o['name'] == 'Draw'), None)

        elif market_key == 'btts':
            # Extract btts outcomes
            btts_yes = next((o['price'] for o in outcomes if o['name'] == 'Yes'), None)
            btts_no = next((o['price'] for o in outcomes if o['name'] == 'No'), None)

        elif market_key == 'totals':
            # Extract totals outcomes (Over/Under 2.5)
            for outcome in outcomes:
                if outcome.get('point') == 2.5:
                    if outcome['name'] == 'Over':
                        over_2_5 = outcome['price']
                        totals_line = outcome.get('point')
                    elif outcome['name'] == 'Under':
                        under_2_5 = outcome['price']
                        if totals_line is None:
                            totals_line = outcome.get('point')

    result = {
        'id': match['id'],
        'home_team': home_team,
        'away_team': away_team,
        'commence_time': commence_time,
        'bookmaker': bookmaker['title'],
        'home_odds': home_odds,
        'away_odds': away_odds,
        'draw_odds': draw_odds,
        'btts_yes': btts_yes,
        'btts_no': btts_no,
        'over_2_5': over_2_5,
        'under_2_5': under_2_5,
        'totals_line': totals_line,
    }
    if league:
        result['league'] = league
    return result

def get_scores(sport, days_from=3):
    """
    Get scores for completed matches from The-Odds-API.
    Results are cached for 10 minutes.

    Args:
        sport: Sport key (e.g., 'soccer_epl')
        days_from: Number of days in the past to fetch scores for (default 3)

    Returns:
        List of score objects with: id, sport_key, home_team, away_team,
        commence_time, completed, scores
    """
    cache_key = f"{sport}_scores_{days_from}"

    # Check cache
    if cache_key in _scores_cache:
        age = time.time() - _scores_cache[cache_key]["timestamp"]
        if age < SCORES_CACHE_TTL_SECONDS:
            return _scores_cache[cache_key]["data"]

    url = f'{ODDS_API_BASE_URL}/sports/{sport}/scores/'

    params = {
        'apiKey': ODDS_API_KEY,
        'daysFrom': days_from
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # Store in cache
        _scores_cache[cache_key] = {"data": data, "timestamp": time.time()}
        return data
    except Exception as e:
        logger.error(f"Error fetching scores for {sport}: {e}")
        return []

def compare_bookmakers_for_acca(bets):
    """
    Compare total acca odds across all bookmakers for a list of bets.

    Args:
        bets: List of bet descriptions like "Arsenal to win", "Liverpool to win"

    Returns:
        Dictionary with bookmaker comparisons
    """
    if not bets:
        return {}

    # Parse team names from bet descriptions
    parsed_bets = []
    for bet_desc in bets:
        bet_lower = bet_desc.lower().strip()

        # Check for BTTS bets first
        if bet_lower.startswith("btts yes - "):
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "btts",
                "outcome_name": "Yes",
                "team": None,
                "is_draw": False
            })
            continue
        elif bet_lower.startswith("btts no - "):
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "btts",
                "outcome_name": "No",
                "team": None,
                "is_draw": False
            })
            continue

        # Check for totals bets
        if bet_lower.startswith("over 2.5 goals - "):
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "totals",
                "outcome_name": "Over",
                "team": None,
                "is_draw": False
            })
            continue
        elif bet_lower.startswith("under 2.5 goals - "):
            parsed_bets.append({
                "original": bet_desc,
                "market_type": "totals",
                "outcome_name": "Under",
                "team": None,
                "is_draw": False
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
        parsed_bets.append({
            "original": bet_desc,
            "market_type": "h2h",
            "outcome_name": "Draw" if is_draw else team_name,
            "team": team_name,
            "is_draw": is_draw
        })

    # Collect all cached matches across all sports
    all_matches = []
    for sport_key, cache_entry in _cache.items():
        if time.time() - cache_entry["timestamp"] < CACHE_TTL_SECONDS:
            all_matches.extend(cache_entry["data"])

    if not all_matches:
        return {}

    # Find odds for each bet
    bet_odds_by_bookmaker = {}  # { bookmaker_key: [odds1, odds2, ...] }

    for parsed_bet in parsed_bets:
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
            # For btts/totals, any match works (we'll match all bookmakers)
            if market_type == "h2h":
                if not (is_draw or team.lower() in [home.lower(), away.lower()]):
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
                        bet_odds_by_bookmaker[bookie_key] = []
                    bet_odds_by_bookmaker[bookie_key].append(outcome["price"])

            # For btts/totals, we've checked all bookmakers for this match
            if market_type in ("btts", "totals"):
                matched_odds = True
                break

            # For h2h, check if we found the match
            if market_type == "h2h" and (is_draw or team.lower() in [home.lower(), away.lower()]):
                matched_odds = True
                break

        # If this bet couldn't be matched, we can't build a full acca
        if not matched_odds:
            continue

    # Calculate total acca odds for bookmakers that have all bets
    result = {}
    num_bets = len(parsed_bets)

    for bookie_key, odds_list in bet_odds_by_bookmaker.items():
        if len(odds_list) == num_bets:
            # All bets available at this bookmaker - multiply odds together
            total_odds = 1.0
            for odds in odds_list:
                total_odds *= odds

            result[bookie_key] = {
                "total_odds": round(total_odds, 2),
                "available": True
            }

    return result

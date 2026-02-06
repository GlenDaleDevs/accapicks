import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv('ODDS_API_KEY')
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Simple in-memory cache: { sport_key: { "data": [...], "timestamp": float } }
_cache = {}
_scores_cache = {}  # Separate cache for scores
CACHE_TTL_SECONDS = int(os.getenv('ODDS_CACHE_TTL', '1800'))  # 30 minutes default
SCORES_CACHE_TTL_SECONDS = 600  # 10 minutes for scores
ODDS_REGIONS = os.getenv('ODDS_REGIONS', 'uk')
ODDS_MARKETS = os.getenv('ODDS_MARKETS', 'h2h')

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
        print(f"Error fetching odds for {sport}: {e}")
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

    markets = bookmaker['markets'][0]['outcomes']

    # Find odds for home, away, draw
    home_odds = next((o['price'] for o in markets if o['name'] == home_team), None)
    away_odds = next((o['price'] for o in markets if o['name'] == away_team), None)
    draw_odds = next((o['price'] for o in markets if o['name'] == 'Draw'), None)

    result = {
        'id': match['id'],
        'home_team': home_team,
        'away_team': away_team,
        'commence_time': commence_time,
        'bookmaker': bookmaker['title'],
        'home_odds': home_odds,
        'away_odds': away_odds,
        'draw_odds': draw_odds
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
    cache_key = f"{sport}_scores"

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
        print(f"Error fetching scores for {sport}: {e}")
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
        # Remove common suffixes like "to win", "win"
        team_name = bet_desc.strip()
        if " to win" in bet_lower:
            team_name = bet_desc[:bet_lower.index(" to win")].strip()
        elif " win" == bet_lower[-4:]:
            team_name = bet_desc[:-4].strip()

        # Check if it's a draw bet
        is_draw = bet_lower in ["draw", "the draw"]
        parsed_bets.append({"original": bet_desc, "team": team_name, "is_draw": is_draw})

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
        team = parsed_bet["team"]
        is_draw = parsed_bet["is_draw"]

        # Find the match containing this team or draw
        matched_odds = None
        for match in all_matches:
            home = match.get("home_team", "")
            away = match.get("away_team", "")

            # Check if this match contains the bet
            if is_draw or team.lower() in [home.lower(), away.lower()]:
                # Extract odds from all bookmakers for this match
                for bookmaker in match.get("bookmakers", []):
                    bookie_key = bookmaker.get("key")
                    markets = bookmaker.get("markets", [])

                    # Find h2h market
                    h2h_market = next((m for m in markets if m.get("key") == "h2h"), None)
                    if not h2h_market:
                        continue

                    outcomes = h2h_market.get("outcomes", [])

                    # Find the specific outcome for this bet
                    if is_draw:
                        outcome = next((o for o in outcomes if o.get("name", "").lower() == "draw"), None)
                    else:
                        outcome = next((o for o in outcomes if o.get("name", "").lower() == team.lower()), None)

                    if outcome and "price" in outcome:
                        if bookie_key not in bet_odds_by_bookmaker:
                            bet_odds_by_bookmaker[bookie_key] = []
                        bet_odds_by_bookmaker[bookie_key].append(outcome["price"])

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

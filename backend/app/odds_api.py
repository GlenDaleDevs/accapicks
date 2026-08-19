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
CACHE_TTL_SECONDS = int(os.getenv('ODDS_CACHE_TTL', '14400'))  # 4 hours default — the results market barely moves inside that
SCORES_CACHE_TTL_SECONDS = 600  # 10 minutes for scores
ODDS_REGIONS = os.getenv('ODDS_REGIONS', 'uk')
ODDS_MARKETS = os.getenv('ODDS_MARKETS', 'h2h,totals')

_btts_cache = {}  # { event_id: { "data": [...bookmakers], "timestamp": float } }
BTTS_CACHE_TTL_SECONDS = 86400  # 24 hours

_events_cache = {}  # { sport_key: { "data": [...events], "timestamp": float } }
EVENTS_CACHE_TTL_SECONDS = 3600  # fixture lists move slowly

COMPARISON_ESTIMATE_HAIRCUT = 0.97  # 3% reduction on estimated odds

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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Store in cache
        _cache[sport] = {"data": data, "timestamp": time.time()}
        return data
    except Exception as e:
        logger.error(f"Error fetching odds for {sport}: {e}")
        return []

def get_events(sport='soccer_epl'):
    """
    Get upcoming fixtures for a sport, without odds.

    The /events endpoint returns the same fixture list as /odds but costs zero
    API credits. Used by week auto-creation, which needs kickoff times only.

    Returns a list of {id, home_team, away_team, commence_time}.
    """
    if sport in _events_cache:
        age = time.time() - _events_cache[sport]["timestamp"]
        if age < EVENTS_CACHE_TTL_SECONDS:
            return _events_cache[sport]["data"]

    url = f'{ODDS_API_BASE_URL}/sports/{sport}/events'

    try:
        response = requests.get(url, params={'apiKey': ODDS_API_KEY}, timeout=10)
        response.raise_for_status()
        data = response.json()
        _events_cache[sport] = {"data": data, "timestamp": time.time()}
        return data
    except Exception as e:
        logger.error(f"Error fetching events for {sport}: {e}")
        # Serve stale rather than nothing: a transient API blip must not read as
        # "no fixtures this week", which is how an international break looks.
        if sport in _events_cache:
            return _events_cache[sport]["data"]
        return []


def format_match_for_display(match, league=None):
    """Format a match into a readable structure"""
    home_team = match['home_team']
    away_team = match['away_team']
    commence_time = match['commence_time']

    # Get h2h odds from first bookmaker in API response (e.g. Unibet for UK)
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

    # Extract h2h from first bookmaker
    for market in bookmaker.get('markets', []):
        if market.get('key') == 'h2h':
            outcomes = market.get('outcomes', [])
            home_odds = next((o['price'] for o in outcomes if o['name'] == home_team), None)
            away_odds = next((o['price'] for o in outcomes if o['name'] == away_team), None)
            draw_odds = next((o['price'] for o in outcomes if o['name'] == 'Draw'), None)
            break

    # Search all bookmakers for totals (first bookmaker may not offer it)
    totals_bookmaker = None
    for bk in match.get('bookmakers', []):
        for market in bk.get('markets', []):
            if market.get('key') == 'totals':
                for outcome in market.get('outcomes', []):
                    if outcome.get('point') == 2.5:
                        if outcome['name'] == 'Over' and over_2_5 is None:
                            over_2_5 = outcome['price']
                            totals_line = 2.5
                            totals_bookmaker = bk.get('title')
                        elif outcome['name'] == 'Under' and under_2_5 is None:
                            under_2_5 = outcome['price']
                            totals_line = 2.5
        if over_2_5 is not None and under_2_5 is not None:
            break

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
        'totals_bookmaker': totals_bookmaker,
    }
    if league:
        result['league'] = league
    return result

def get_btts_for_event(sport_key, event_id):
    """
    Get BTTS odds for a specific event (lazy-fetched, 24h cache).

    Args:
        sport_key: Sport key (e.g., 'soccer_epl')
        event_id: The-Odds-API event ID

    Returns:
        Dictionary with btts_yes and btts_no odds (can be None if not found)
    """
    # Purge expired entries from cache to prevent unbounded growth
    now = time.time()
    expired_keys = [eid for eid, entry in _btts_cache.items()
                    if now - entry["timestamp"] >= BTTS_CACHE_TTL_SECONDS]
    for eid in expired_keys:
        del _btts_cache[eid]

    # Check if we have fresh cached data
    if event_id in _btts_cache:
        age = now - _btts_cache[event_id]["timestamp"]
        if age < BTTS_CACHE_TTL_SECONDS:
            # Extract display odds from cached bookmakers
            bookmakers = _btts_cache[event_id]["data"]
            for bookmaker in bookmakers:
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "btts":
                        outcomes = market.get("outcomes", [])
                        btts_yes = next((o["price"] for o in outcomes if o["name"] == "Yes"), None)
                        btts_no = next((o["price"] for o in outcomes if o["name"] == "No"), None)
                        if btts_yes is not None or btts_no is not None:
                            return {"btts_yes": btts_yes, "btts_no": btts_no}

    # Not cached or expired - fetch from API
    url = f'{ODDS_API_BASE_URL}/sports/{sport_key}/events/{event_id}/odds'

    params = {
        'apiKey': ODDS_API_KEY,
        'markets': 'btts',
        'regions': 'uk',
        'oddsFormat': 'decimal'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        event_data = response.json()

        # Store bookmakers in cache
        bookmakers = event_data.get("bookmakers", [])
        _btts_cache[event_id] = {"data": bookmakers, "timestamp": time.time()}

        # Extract display odds
        for bookmaker in bookmakers:
            for market in bookmaker.get("markets", []):
                if market.get("key") == "btts":
                    outcomes = market.get("outcomes", [])
                    btts_yes = next((o["price"] for o in outcomes if o["name"] == "Yes"), None)
                    btts_no = next((o["price"] for o in outcomes if o["name"] == "No"), None)
                    if btts_yes is not None or btts_no is not None:
                        return {"btts_yes": btts_yes, "btts_no": btts_no}

        return {"btts_yes": None, "btts_no": None}

    except Exception as e:
        logger.error(f"Error fetching BTTS odds for event {event_id}: {e}")
        return {"btts_yes": None, "btts_no": None}

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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Store in cache
        _scores_cache[cache_key] = {"data": data, "timestamp": time.time()}
        return data
    except Exception as e:
        logger.error(f"Error fetching scores for {sport}: {e}")
        return []


def fresh_cached_odds():
    """(sport_key, matches) for every league whose paid-odds cache is live.

    The comparison module reads through this rather than touching _cache —
    the cache stays private to the fetch layer.
    """
    now = time.time()
    # Snapshot first: background refreshes insert into _cache from other
    # threads, and iterating a dict while it grows raises RuntimeError.
    return [(sport, entry["data"]) for sport, entry in list(_cache.items())
            if now - entry["timestamp"] < CACHE_TTL_SECONDS]


def fresh_cached_btts(event_id):
    """Cached per-event BTTS bookmakers, or None when absent or stale."""
    entry = _btts_cache.get(event_id)
    if entry and time.time() - entry["timestamp"] < BTTS_CACHE_TTL_SECONDS:
        return entry["data"]
    return None

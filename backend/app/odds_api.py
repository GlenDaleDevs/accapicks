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
# Opening Compare Bookmakers refreshes the acca's leagues if the cached odds are
# older than this, so the comparison is near-live. Bounded on purpose: at most
# one refetch per league per window, however many people open Compare, so it
# can't run the odds-API credits down. Tunable via env.
COMPARE_REFRESH_MAX_AGE = int(os.getenv('COMPARE_ODDS_MAX_AGE', '1800'))  # 30 min
SCORES_CACHE_TTL_SECONDS = 600  # 10 minutes for scores
ODDS_REGIONS = os.getenv('ODDS_REGIONS', 'uk')
ODDS_MARKETS = os.getenv('ODDS_MARKETS', 'h2h,totals')

_btts_cache = {}  # { event_id: { "data": [...bookmakers], "timestamp": float } }
BTTS_CACHE_TTL_SECONDS = 86400  # 24 hours

_events_cache = {}  # { sport_key: { "data": [...events], "timestamp": float } }
EVENTS_CACHE_TTL_SECONDS = 3600  # fixture lists move slowly

COMPARISON_ESTIMATE_HAIRCUT = 0.97  # 3% reduction on estimated odds

def get_football_matches(sport='soccer_epl', max_age=None):
    """
    Get upcoming football matches with odds, cached to reduce API usage.

    max_age: override the cache freshness threshold (seconds) for this call.
    Defaults to CACHE_TTL_SECONDS (4h). The Compare path passes the shorter
    COMPARE_REFRESH_MAX_AGE so an open there refetches odds older than the
    compare window while still being served from cache within it — a paid call
    happens only when the cache is genuinely older than the threshold asked for.

    sport options:
    - soccer_epl (Premier League)
    - soccer_spain_la_liga (La Liga)
    - soccer_germany_bundesliga (Bundesliga)
    - soccer_italy_serie_a (Serie A)
    - soccer_france_ligue_one (Ligue 1)
    """
    ttl = CACHE_TTL_SECONDS if max_age is None else max_age
    # Check cache
    if sport in _cache:
        age = time.time() - _cache[sport]["timestamp"]
        if age < ttl:
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
        # A paid call landed — log it so credit burn stays visible in Railway.
        logger.info("odds-API fetch: %s (%d matches)", sport, len(data))
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


def verify_pick(sport_key, event_id, pick_type):
    """Server-side source of truth for a bet's odds/teams/description.

    Never trust client-supplied odds, team columns or description for a market
    pick — a client can forge any of those independently to inflate its price
    or flip home/away so settlement scores it as a win. This re-derives all of
    them from the same cached market data the Fixtures tab rendered, keyed on
    (sport_key, event_id, pick_type).

    Returns {"odds": float, "home_team": str, "away_team": str,
    "description": str, "totals_line": float | None} on success, or None if
    the fixture/outcome can't be verified right now (cold cache, unpriced
    outcome, BTTS not cached). Callers must treat None as "reject the bet",
    never fall back to client data.
    """
    if pick_type in ("btts_yes", "btts_no"):
        # Cache-ONLY — get_btts_for_event fetches on a miss, which would cost
        # 1 API credit per bet attempt (cost-DoS). The frontend only shows the
        # BTTS chip after it has already warmed this cache via getBttsOdds.
        bookmakers = fresh_cached_btts(event_id)
        if not bookmakers:
            return None

        matches = get_football_matches(sport_key)
        match = next((m for m in matches if m.get('id') == event_id), None)
        if not match:
            return None
        formatted = format_match_for_display(match)
        if not formatted:
            return None

        btts_yes = None
        btts_no = None
        for bookmaker in bookmakers:
            for market in bookmaker.get("markets", []):
                if market.get("key") == "btts":
                    outcomes = market.get("outcomes", [])
                    if btts_yes is None:
                        btts_yes = next((o["price"] for o in outcomes if o["name"] == "Yes"), None)
                    if btts_no is None:
                        btts_no = next((o["price"] for o in outcomes if o["name"] == "No"), None)

        price = btts_yes if pick_type == "btts_yes" else btts_no
        if price is None:
            return None

        home_team = formatted['home_team']
        away_team = formatted['away_team']
        if pick_type == "btts_yes":
            description = f"BTTS Yes - {home_team} vs {away_team}"
        else:
            description = f"BTTS No - {home_team} vs {away_team}"

        return {
            "odds": float(price),
            "home_team": home_team,
            "away_team": away_team,
            "description": description,
            "totals_line": None,
        }

    if pick_type in ("home", "away", "draw", "over_2_5", "under_2_5"):
        matches = get_football_matches(sport_key)
        match = next((m for m in matches if m.get('id') == event_id), None)
        if not match:
            return None
        formatted = format_match_for_display(match)
        if not formatted:
            return None

        home_team = formatted['home_team']
        away_team = formatted['away_team']
        totals_line = formatted['totals_line']

        if pick_type == "home":
            price = formatted['home_odds']
            description = f"{home_team} to win"
        elif pick_type == "away":
            price = formatted['away_odds']
            description = f"{away_team} to win"
        elif pick_type == "draw":
            price = formatted['draw_odds']
            description = f"Draw - {home_team} vs {away_team}"
        elif pick_type == "over_2_5":
            price = formatted['over_2_5']
            description = f"Over {totals_line} Goals - {home_team} vs {away_team}"
        else:  # under_2_5
            price = formatted['under_2_5']
            description = f"Under {totals_line} Goals - {home_team} vs {away_team}"

        if price is None:
            return None

        return {
            "odds": float(price),
            "home_team": home_team,
            "away_team": away_team,
            "description": description,
            "totals_line": totals_line,
        }

    return None

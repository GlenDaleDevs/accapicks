"""Upcoming fixtures from The-Odds-API.

Uses the /events endpoint rather than /odds: it returns the same fixture list
but costs zero API credits, and this feature needs no prices.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from .config import DIVISION_BY_ODDS_KEY, TARGET_DIVISIONS, DIVISION_BY_CODE

load_dotenv()
logger = logging.getLogger(__name__)

BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_fixtures(days_ahead=8):
    """Return upcoming fixtures across the target divisions.

    Each fixture: {div, div_name, home, away, commence_time, event_id}
    """
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        raise RuntimeError("ODDS_API_KEY not set")

    cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    fixtures = []
    for code in TARGET_DIVISIONS:
        division = DIVISION_BY_CODE[code]
        sport_key = division["odds_key"]
        if not sport_key:
            continue

        url = f"{BASE_URL}/sports/{sport_key}/events"
        try:
            resp = requests.get(url, params={"apiKey": api_key}, timeout=20)
            resp.raise_for_status()
            events = resp.json()
        except Exception as exc:
            logger.error("fixture fetch failed for %s: %s", sport_key, exc)
            continue

        for event in events:
            commence = event.get("commence_time")
            if commence:
                try:
                    kickoff = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                except ValueError:
                    kickoff = None
                if kickoff and kickoff > cutoff:
                    continue

            fixtures.append({
                "div": code,
                "div_name": division["name"],
                "home": event.get("home_team"),
                "away": event.get("away_team"),
                "commence_time": event.get("commence_time"),
                "event_id": event.get("id"),
            })

    fixtures.sort(key=lambda f: f["commence_time"] or "")
    return fixtures

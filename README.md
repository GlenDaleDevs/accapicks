# AccaPicks

[![CI](https://github.com/GlenDaleDevs/accapicks/actions/workflows/ci.yml/badge.svg)](https://github.com/GlenDaleDevs/accapicks/actions/workflows/ci.yml)
[![Security Scan](https://github.com/GlenDaleDevs/accapicks/actions/workflows/security.yml/badge.svg)](https://github.com/GlenDaleDevs/accapicks/actions/workflows/security.yml)

**Live at [accapicks.com](https://accapicks.com)**

A social football accumulator game for groups of mates. Every week, each member of a group contributes one pick — built from real bookmaker odds — to a shared accumulator. The slip locks at the first kickoff, results settle automatically from live score data, and a season-long leaderboard keeps the bragging rights honest.

No money is staked through the app: picks are tracked against a notional stake, and bookmaker price comparisons carry clear affiliate/18+ disclosure. UK-focused (Premier League, Championship, League One, League Two).

## How it works

1. **Create or join a group** with a 6-character invite code (shareable via WhatsApp/Messenger).
2. **A week opens automatically** — a background task watches the real fixture calendar and opens each weekend's acca a day ahead, so nobody has to set anything up. International breaks simply produce no week.
3. **Everyone adds one pick** from live odds (match result or both-teams-to-score), browsing fixtures, form tables, standings, and ~12 seasons of head-to-head history.
4. **The slip locks at the first kickoff** among the actual picks — recalculated every time a pick changes.
5. **Results settle themselves** from live score data, with team-name normalization, void handling for abandoned fixtures, and push notifications when the acca wins or dies.
6. **The leaderboard tracks the season**, including members who never picked, with weekly movement indicators.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React 19, Vite, React Router 7, Framer Motion, installable PWA (service worker + web push) |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic, Alembic migrations |
| Database | PostgreSQL (SQLite in local dev) |
| Data feeds | The-Odds-API (live odds & scores), football-data.co.uk (results, form, H2H history) |
| Deployment | Docker on Railway, auto-deploy from `main` |

## Architecture notes

- **Automatic week creation** — `weekblocks.py` is a pure module (fixture lists in, anchored week blocks out; no DB, no network) driven by `autoweek.py` on a 30-minute tick. Kickoffs arrive as UTC and are bucketed through `Europe/London`, so BST/GMT boundaries and Friday-opening weekends are handled explicitly. Pure core + thin orchestration keeps the tricky calendar logic unit-testable.
- **Settlement engine** — a background task settles each leg once its match completes, normalizing team names across data sources, auto-voiding abandoned or unresolvable fixtures, and only settling the acca when every leg has a result. There are deliberately **no manual settlement endpoints** — results can't be edited, which keeps the leaderboard tamper-proof.
- **Lock semantics** — an acca's lock time derives from the earliest kickoff among *actual picks*, not the whole fixture list, and is recalculated on every pick add/remove and membership change.
- **Migration discipline** — an Alembic chain designed to run correctly on both a fresh database and production, with inspector guards documented in each migration.
- **API-quota frugality** — the free fixtures endpoint is used wherever prices aren't needed; odds and history responses are cached with explicit max-age policies; per-event markets are lazy-fetched.

## Security

Security has been treated as a first-class feature — full details in [docs/security.md](docs/security.md). Highlights:

- JWT auth with `jti`-based token blacklist (revocation on logout and password change), bcrypt hashing with timing-attack-resistant dummy hashes on failed lookups, and account lockout on repeated failures.
- Rate limiting on every auth and destructive endpoint, proxy-aware client IP handling.
- Security headers middleware (CSP, HSTS, X-Frame-Options, Referrer-Policy, Permissions-Policy), request size limits, server-side Pydantic validation everywhere, ORM-only data access.
- Three rounds of adversarial security auditing (most recent: 40 findings, zero critical/high), with fixes tracked and re-audited.
- CI runs `npm audit` and `pip-audit` on every push.

## Development

```bash
# Frontend (repo root)
npm install
npm run dev        # http://localhost:5173
npm run lint
npm run build

# Backend (from backend/)
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000
python -m pytest                # unit tests (pure logic modules)
python migrate.py               # Alembic migrations
```

The backend needs a `.env` (see `backend/.env.example`) with a The-Odds-API key for live odds.

This project is built solo with an AI-assisted workflow — the `.claude/` directory contains the project rules, learned-mistake log, and agent definitions that keep that workflow disciplined.

## License

Copyright © 2026. All rights reserved — source available for viewing and evaluation; see [LICENSE](LICENSE).

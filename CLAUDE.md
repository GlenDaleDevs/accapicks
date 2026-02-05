# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PickOneBet (AccaPicks) is a full-stack web app for collaborative sports betting accumulators. Users create/join groups, build accumulators (accas) from real match odds, and track results on a leaderboard.

- **Frontend:** React 19 + Vite (JavaScript/JSX)
- **Backend:** Python FastAPI + SQLAlchemy + SQLite
- **External API:** The-Odds-API for live match odds

## Commands

### Frontend (root directory)

```bash
npm install            # install dependencies
npm run dev            # dev server at http://localhost:5173
npm run build          # production build to /dist
npm run lint           # ESLint
```

### Backend (from backend/ directory)

```bash
venv\Scripts\activate              # activate virtualenv (Windows)
pip install <package>              # no requirements.txt exists; deps installed directly
uvicorn app.main:app --reload      # dev server at http://localhost:8000
python migrate.py                  # run database migrations
```

FastAPI auto-generated docs available at http://localhost:8000/docs when the backend is running.

## Architecture

### Frontend (`src/`)

- `App.jsx` — top-level component; manages auth state, navigation between views (groups list, group detail, acca detail), and JWT token in localStorage
- `api/client.js` — axios instance with base URL and auth interceptor; all API calls go through this
- `components/` — view components: `AuthView` (login/signup), `GroupsList`, `GroupDetail`, `AccaDetail`, `AccaWizard` (create acca flow), `FixtureGrid` (match selection), `BetCard`, `BookmakerComparison`, `Leaderboard`, `Calendar`
- `utils/constants.js` — league definitions (EPL, La Liga, Bundesliga, Serie A, Ligue 1) with sport keys and API mappings
- `utils/formatters.js` — date formatting and countdown helpers

### Backend (`backend/app/`)

- `main.py` — FastAPI app setup, CORS config, rate limiter (slowapi), background task that auto-locks accas every 60s
- `routes.py` — all API endpoints under `/api/` (auth, groups, accas, bets, odds)
- `models.py` — SQLAlchemy models: User, Group, GroupMember, Acca, Bet
- `schemas.py` — Pydantic request/response schemas
- `auth.py` — JWT creation/verification (30-min expiry), bcrypt password hashing
- `database.py` — SQLite engine and session management
- `odds_api.py` — The-Odds-API client with 30-minute response caching

### Key Data Flow

1. Users authenticate via JWT (stored in localStorage, sent as Bearer token)
2. Groups use 6-character invite codes for joining
3. Accas are created with selected leagues/dates, status progresses: open → locked → settled
4. Each user adds one bet per acca; acca auto-locks when first match starts (`locks_at` field)
5. Odds data fetched from The-Odds-API, cached 30 minutes to reduce API calls

## Environment Variables (backend/.env)

```
ODDS_API_KEY=<the-odds-api key>
SECRET_KEY=<32-byte hex string for JWT signing>
ALLOWED_ORIGINS=http://localhost:5173,https://accapicks.com,https://www.accapicks.com
```

## API Route Structure

- `POST /api/auth/signup` and `/api/auth/login` — auth (rate-limited: 5/min signup, 10/min login)
- `/api/groups` — CRUD + join via invite code + leaderboard
- `/api/accas` — create, list by group, get detail with bets, bookmaker comparison
- `/api/bets` — add/delete/update result (won/lost/void)
- `/api/odds/matches` and `/api/odds/matches/filtered` — fetch matches from The-Odds-API

## Agent Delegation

Always delegate tasks to the appropriate specialized agent: `react-frontend-dev` for `src/` changes, `fastapi-backend-dev` for `backend/app/` changes, `database-specialist` for schema/migration/query work, `odds-api-specialist` for The-Odds-API integration, `test-specialist` for writing/running tests, `devops-config` for build/deploy/config changes, `code-reviewer` for reviewing code. Prefer parallel agent launches when tasks are independent.

--

Post-Init Token Efficiency Addendum
Scope

Applies after initial project ingestion.
Assume the project structure is already known.

Communication Defaults:

Be concise by default.
Do not restate the task.
Avoid meta commentary (“Here’s what I’ll do”, “Let me know if…”).
Skip summaries unless explicitly requested.

Reasoning:
Perform analysis internally.
Do not expose chain-of-thought.
Provide conclusions, actions, or code only.

Questions:
Ask a clarifying question only if blocked.
Otherwise, make reasonable assumptions and proceed.

Code Changes:
Touch the minimum necessary files.
Do not re-describe existing code.
Prefer small, targeted edits over refactors.
Use existing patterns and utilities.

Output Format:
Prefer:
Short bullet lists
Diffs
File-scoped code blocks
Avoid long prose explanations.
No decorative formatting.

Explanations
Explain only non-obvious decisions.
Limit explanations to 1–3 short bullets.
Omit rationale for standard practices.

Reviews & Feedback
Focus on actionable issues only.
No stylistic nitpicks unless requested.
No “nice to have” suggestions by default.

Assumptions
Assume developer-level knowledge.
Assume familiarity with the codebase.
Assume speed > pedagogy.

Soft Overrides
If the user asks for:
“details”
“explanation”
“walkthrough”
“review”

→ comply, but remain concise.

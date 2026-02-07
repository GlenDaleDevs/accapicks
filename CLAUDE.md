# CLAUDE.md

## Developer Context

- Electrical & Electronic Engineering degree; moderate proficiency in C++, Python, and React
- Solo developer building this as a side project
- Prefers clean, readable code — split large files into smaller, focused modules
- Keep files under ~200 lines where practical; extract components/utilities when files grow
- Prefer simple, direct solutions over clever abstractions

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
3. Accas are created with selected leagues/dates, status progresses: open -> locked -> settled
4. Each user adds one bet per acca; acca auto-locks when first match starts (`locks_at` field)
5. Odds data fetched from The-Odds-API, cached 30 minutes to reduce API calls

## Environment Variables (backend/.env)

```
ODDS_API_KEY=<the-odds-api key>
SECRET_KEY=<32-byte hex string for JWT signing>
ALLOWED_ORIGINS=http://localhost:5173,https://accapicks.com,https://www.accapicks.com
RESEND_API_KEY=<resend api key for email verification>
```

## Deployment (Railway)

**Pre-deployment checklist:**
1. Verify Railway is pointed at correct branch (`main`)
2. Check all environment variables are set in Railway
3. Confirm DATABASE_URL uses public Postgres URL

**Custom domain setup:**
1. Add domain in Railway -> Settings -> Networking
2. Railway provides unique validation URLs (e.g., `r4qsmodn.up.railway.app`)
3. In Namecheap: ALIAS for `@`, CNAME for `www` -> Railway's URLs
4. Wait for green checkmarks before testing

**Resend (email) setup -- all records required:**
1. TXT `resend._domainkey` -> DKIM key (domain verification)
2. TXT `send` -> SPF record (`v=spf1 include:amazonses.com ~all`)
3. MX `send` -> `feedback-smtp.eu-west-1.amazonses.com` priority 10 (in Mail Settings -> Custom MX)
4. TXT `_dmarc` -> DMARC policy (optional but recommended)

**Important:** The MX record is required for Resend verification, not optional. Add it via Namecheap's Mail Settings section with host `send`.

## API Route Structure

- `POST /api/auth/signup` and `/api/auth/login` -- auth (rate-limited: 5/min signup, 10/min login)
- `/api/groups` -- CRUD + join via invite code + leaderboard
- `/api/accas` -- create, list by group, get detail with bets, bookmaker comparison
- `/api/bets` -- add/delete/update result (won/lost/void)
- `/api/odds/matches` and `/api/odds/matches/filtered` -- fetch matches from The-Odds-API

## Agent Workflow

### Agents
| Agent | Model | Role |
|---|---|---|
| `planner` | Opus | Scopes work, identifies files, proposes approach. Read-only. |
| `critic` | Opus | Devil's advocate — challenges the plan before implementation. Read-only. |
| `frontend-dev` | Sonnet | Implements frontend code under `src/` |
| `backend-dev` | Sonnet | Implements backend code under `backend/app/` |
| `database` | Sonnet | Schema design, models, migrations |
| `odds-api` | Sonnet | The-Odds-API integration |
| `code-reviewer` | Sonnet | Reviews written code for bugs/security. Read-only. |
| `tester` | Sonnet | Writes and runs tests |
| `devops` | Sonnet | Build, deploy, config files |
| `web-design-planner` | Sonnet | Visual design direction and UI/UX recommendations |
| `legal-gambling-compliance` | Sonnet | UK gambling law, GDPR, legal documents |
| `annoying-user` | Opus | Adversarial tester — acts as a user trying to break the app. Read-only. |

### Pipeline (for non-trivial changes)
1. **planner** -- scopes the work, identifies affected files, defines agent tasks
2. **critic** -- challenges the plan, finds gaps, suggests improvements
3. **Implementation agents** (frontend-dev, backend-dev, database, etc.) -- run in parallel where independent
4. **code-reviewer** -- reviews all changes for bugs, security, consistency
5. **tester** -- writes/runs tests for new code

### The `annoying-user` agent
Use the `critic` subagent type with an adversarial user testing prompt. The agent should think like an impatient, creative, slightly malicious user who:
- Tries to bypass validation (empty fields, huge inputs, special characters, SQL injection attempts)
- Races conditions (double-clicking buttons, submitting forms twice, opening multiple tabs)
- Abuses business logic (joining own group twice, betting after lock, manipulating odds)
- Tests edge cases (empty groups, zero bets, deleted data, expired tokens)
- Breaks navigation (back button, direct URL access, deep links while logged out)
- Tries mobile-specific exploits (copy-paste into validated fields, autofill bypasses)

Invoke with: `Task(subagent_type="critic", prompt="Act as an annoying user trying to break AccaPicks. Read [specific files] and find ways a user could...")`

### Skip to step 3 for:
- Single-file bug fixes
- Copy/text changes
- Config tweaks
- Changes where the approach is obvious

### Always run in parallel when possible:
- Frontend + backend for full-stack features
- Code review + test writing (after implementation)
- Multiple independent implementation agents

## Commit Style

- Start with a verb: Add, Fix, Update, Remove, Refactor
- First line: short summary (under 72 chars), no period
- Body (if needed): bullet points explaining what and why
- Always include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- Don't commit `.env`, credentials, or large binaries
- Stage specific files, not `git add -A`

## Output Rules

- No preambles ("Here's what I'll do"), no summaries, no meta commentary
- No restating the task
- For code changes: output the edit, not a description of the edit
- For bug fixes: state root cause in one line, then fix
- Explain only non-obvious decisions, in 1-3 bullets max
- Prefer: short bullet lists, diffs, file-scoped code blocks
- Ask a clarifying question only if truly blocked; otherwise assume and proceed
- Assume developer-level knowledge and codebase familiarity

**Soft overrides:** If asked for "details", "explanation", "walkthrough", or "review" -- comply but stay concise.

## Code Style Rules

- Keep files focused and small (~200 lines max); split when growing
- Small, targeted edits over broad refactors
- Use existing patterns and utilities; don't reinvent
- No unnecessary abstractions, feature flags, or over-engineering
- Touch only the minimum necessary files

## Rules (learned from mistakes)

- Always save assessments, feature plans, and multi-item lists to a .txt file in the project root — context compaction will lose them otherwise
- Always follow the planner → critic → implement pipeline for non-trivial changes. If you think a task is simple enough to skip planning, ask the user first — don't skip silently
- After implementing code review fixes, always build (`npm run build`) before committing to catch syntax/import errors
- When adding new acca/bet statuses or enum values in the backend, check that the frontend filters and badge displays handle ALL possible values (e.g. "won", "lost", "settled" — not just "settled")
- Case sensitivity matters everywhere: login, signup, email lookups, username checks — always use func.lower() or .lower() for user-facing string comparisons
- Mobile keyboard behaviour is controlled by HTML input attributes: use `type="email"` for email-only fields, `type="text"` + `inputMode="email"` for fields that accept email OR other text (like username). Never use `type="email"` on a field that accepts non-email input
- When deleting user data (account deletion, leave group, remove member), consider the cascade effect on related data like acca status — deleting bets can leave accas in an inconsistent state
- The-Odds-API sport keys for English lower leagues: `soccer_efl_champ` (Championship), `soccer_england_league1` (League One), `soccer_england_league2` (League Two)

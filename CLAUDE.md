# CLAUDE.md

## Developer Context

- Solo developer, side project
- Prefers clean, readable code — split large files into smaller, focused modules
- Keep files under ~200 lines; extract components/utilities when files grow
- Prefer simple, direct solutions over clever abstractions

## Project Overview

PickOneBet (AccaPicks) — full-stack web app for collaborative sports betting accumulators. Users create/join groups, build accas from real match odds, track results on a leaderboard.

- **Frontend:** React 19 + Vite (JSX) in `src/`
- **Backend:** Python FastAPI + SQLAlchemy + PostgreSQL in `backend/app/`
- **External API:** The-Odds-API for live match odds
- **Deploy:** Railway (Docker), auto-deploys from `main` branch

## Commands

```bash
# Frontend (root directory)
npm install && npm run dev       # dev server at localhost:5173
npm run build                    # production build to /dist
npm run lint                     # ESLint

# Backend (from backend/ directory)
venv\Scripts\activate            # activate virtualenv (Windows)
uvicorn app.main:app --reload    # dev server at localhost:8000
python migrate.py                # run Alembic migrations
```

## Commit Style

- **Auto commit and push** after every set of edits — don't wait to be asked
- Start with a verb: Add, Fix, Update, Remove, Refactor
- First line: short summary (under 72 chars), no period
- Always include `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- Stage specific files, not `git add -A`

## Output Rules

- No preambles, summaries, or meta commentary
- For code changes: output the edit, not a description of the edit
- For bug fixes: state root cause in one line, then fix
- Explain only non-obvious decisions, in 1-3 bullets max
- Ask a clarifying question only if truly blocked; otherwise assume and proceed
- **Soft override:** If asked for "details", "explanation", or "review" — comply but stay concise

## Planning

- **Always use plan mode** (`EnterPlanMode`) for non-trivial changes before implementing
- Plan mode lets you explore the codebase, design the approach, and get user approval first
- Skip plan mode only for: single-file bug fixes, copy/text changes, config tweaks, obvious one-liners

## Web Design

Current design system for the `web-design-planner` agent to reference:

- **Theme:** Dark mode, sports/betting aesthetic
- **Colors:** Dark backgrounds (#1a1a2e, #16213e), accent green (#4ade80), amber for warnings
- **Typography:** Clean sans-serif, bold headings, tabular numbers for odds/stats
- **Components:** Card-based layouts, rounded corners, subtle shadows, glass-morphism effects
- **Mobile-first:** All layouts must work on mobile; bottom nav on mobile, sidebar on desktop
- **Animations:** Subtle transitions only — no flashy animations that feel like a casino
- **Tone:** Modern, clean, trustworthy — not garish or gambling-site cliche

## Code Style

- Small, targeted edits over broad refactors
- Use existing patterns and utilities; don't reinvent
- No unnecessary abstractions, feature flags, or over-engineering
- Touch only the minimum necessary files

# AccaPicks — Where We Are

## Current Stage
Late development — deployed to production on Railway, security hardening complete, working through feature backlog.

## What's Done
- Full-stack app deployed (React 19 + Vite / FastAPI + PostgreSQL / Railway)
- Core acca system (create/join groups, build accas, pick from live odds, track results, leaderboard)
- Open acca slot UI redesign (paper betting slip aesthetic, fixture exclusion, "Picked by" banners)
- Bet slip with ticks/crosses for won/lost/void, kickoff times
- Invite friends (WhatsApp + Messenger + copy link)
- Bookmaker comparison (top 5 by default, show-all expand)
- Security hardening (token blacklist, account lockout, rate limiter fix, CSP/HSTS, manual settle removed)
- Security audit (40 findings, 0 critical/high remaining)
- Settlement system (auto-settle, auto-void legacy/cancelled bets, team name normalization, 14-day window)
- Background polling fix (no more bet slip flickering)
- Auth/landing page polish (CSS variables, design tokens, 100dvh, ultra-small mobile breakpoint, alerts inside form, footer with Terms/Privacy/18+ notice)
- Landing page redesign (Midjourney floodlit pitch background, vertical features, compact form, goal visible)
- Bet preservation on leave/rejoin (orphaned bets, member-aware locks_at/conflicts/bookmaker comparison)
- PWA support (installable app, service worker precaching, auto-reload on update)
- Push notifications (subscribe/unsubscribe, bet creation + settlement triggers, security hardened)
- npm audit clean (minimatch override, GitHub Actions --omit=dev)
- **UI overhaul (2026-08-15)** — FPL-style 4-tab navigation (Acca/Fixtures/Table/More), group switcher in a
  global header, week-numbered accas with paging, four distinct acca states, pinned odds/returns, first modal
  in the codebase, reworked league table, movement arrows. 8 commits, **unpushed**. Plan:
  `.claude/plans/glittery-coalescing-naur.md`

## What's Left
### Blocking / do first
- [x] ~~Push the UI-overhaul commits~~ — shipped and deployed to accapicks.com (through `e5f687e`)
- [x] ~~Fix the migration chain~~ — done in `b6a2f2c`, runnable from an empty database
- [ ] Verify the overhaul on a real phone (iOS PWA safe areas, tab bar, modal, 360px column widths)

### Next season (PL kicks off w/c 2026-08-22) — natural clean-slate moment
- [x] ~~**Auto-create weeks**~~ — done 2026-08-16. Anchored on the Saturday, spreading into Fri/Sun/Mon
      where fixtures exist; a full PL midweek round (≥4 fixtures) also gets a week. Four English leagues.
      International breaks resolve themselves — no fixtures, no week. On by default, toggle in Group
      Settings, push when a week opens, empty lapsed weeks deleted. Manual creation stays for one-offs,
      which is why the create-in-date-order 409 had to go.
      Still to do: **verify in a browser before Saturday** (nothing visual was checked), and decide
      whether Friday-only weeks or a shorter `LEAD_DAYS` are wanted — a week currently opens 4 days out,
      so the opening weekend appears on Tue 18 Aug.
- [ ] **Fresh league table for the new season.** Needs a season boundary concept — today the leaderboard
      counts every bet ever. Cheapest version: only count accas with round_number >= a per-group
      season_start_round.
- [x] ~~Decide what to do with the lapsed pre-season weeks~~ — deleted automatically once their last
      fixture has passed with no picks (`autoweek.cleanup_lapsed_weeks`).

### Quick wins (1 session each)
- [ ] Install `eslint-plugin-react` so JSX-only identifiers stop reading as unused (13 pre-existing lint errors)
- [ ] Join-a-group flow: the invite link already works end-to-end; what's missing is invite context on the
      auth screen ("You've been invited to Mr Worldwide"). Deferred from the overhaul plan §7
- [ ] Pick a football stats API for Favourable Matchups — none is in use; The-Odds-API has no standings/form.
      Candidates: API-Football (covers League One/Two with home/away splits), football-data.org (cleaner,
      but free tier likely stops at Championship)
- [ ] Apply new colour palette to CSS variables (palette chosen, waiting for logo/assets)
- [ ] Generate logo (Weavy/Midjourney/Looka) and additional background assets
- [ ] Debug push notifications in production (VAPID keys, test end-to-end)
- [ ] General polish pass — remaining pages (group list/detail, acca/bet slip, fixture grid, bookmaker comparison, leaderboard, profile/settings)

### Medium effort (1-2 sessions)
- [ ] Add Framer Motion micro-animations (page transitions, card entrances, leaderboard count-ups)
- [ ] Desktop landing page polish (test background on wide viewports, possibly landscape variant)
- [ ] Bookmaker comparison UI refresh (add logos, card-based redesign)
- [ ] Affiliate link setup (research programs, sign up, populate BookmakerLink table, add disclosure)

### Large effort (2-4 sessions)
- [ ] More bet types — Phase 1: Over/Under 2.5 (add totals market to API, frontend tabs, settlement logic)
- [ ] More bet types — Phase 2: BTTS (check API availability, binary settlement)

### Future (multi-session projects)
- [ ] Last Man Standing mode (new game mode: LMSGame, LMSRound, LMSPick models, elimination rounds)
- [ ] Bet Builder feature (single-fixture multi-market bets, needs API research for SGM odds)

## Blockers / Open Questions
- Affiliate programs: need manual research on which bookmakers accept low-traffic affiliates
- Bet Builder: depends on The-Odds-API same-game multi availability (may be limited)
- Last Man Standing: fully independent, no blockers — just needs dedicated sessions

## Last Updated
2026-08-16

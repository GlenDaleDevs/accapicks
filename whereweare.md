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
- [ ] **Decide whether to push the 8 UI-overhaul commits** — `main` auto-deploys to accapicks.com. The
      `add_round_numbers` migration will run on production Postgres and rename every acca to "Week N"
- [ ] **Fix the migration chain** — `1129e7a0814d` duplicates `op.create_table('users')` from the initial
      migration, so a fresh database cannot migrate. Only survives because production was built by
      `create_all()` and stamped
- [ ] Verify the overhaul on a real phone (iOS PWA safe areas, tab bar, modal, 360px column widths)

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
2026-08-15

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
- [x] ~~**Fresh league table for the new season.**~~ — done 2026-08-16. `groups.season_start_date`, set
      by an admin in Group Settings, scopes the leaderboard, the accas-won bar and member profiles
      together. Keyed on `first_match_date`, not `round_number`, which is no longer chronological.
      Null on every existing group, so **you have to set it** (21 Aug 2026) or the table keeps counting
      last season. Week strip is deliberately not scoped — old weeks stay browsable.
- [x] ~~Decide what to do with the lapsed pre-season weeks~~ — deleted automatically once their last
      fixture has passed with no picks (`autoweek.cleanup_lapsed_weeks`).

### Open threads (2026-08-18) — read these first if picking up elsewhere
- [ ] **Did the auto week fire?** Today is the first day the Saturday block falls inside `LEAD_DAYS = 4`.
      Expect an acca covering Fri 21 – Mon 24 Aug, labelled **Week 1**, plus a push to the group.
      If it didn't: check `groups.auto_weeks` is true, that no other open acca was blocking it, and the
      Railway logs for `Auto week error`
- [ ] **Confirm `season_start_date` is 21 Aug 2026 or earlier, not the 22nd.** The week's
      `first_match_date` is the Friday opener, so a boundary on the 22nd would drop Week 1 out of the
      season entirely and it would read "past season"
- [ ] **Nothing shipped since 15 Aug has been seen in a browser** — the Chrome extension won't connect
      (`list_connected_browsers` returns empty, so it isn't pairing with the account at all). Unverified:
      the Group Settings toggles, the reworded no-week card, the week strip label, and the restacked
      pick rows. Specific thing to judge: whether five stacked pick rows push the returns bar too low
- [ ] **Genuine midweek rounds group with the following weekend in the Fixtures tab.** `fixturelist.py`
      anchors each game week on the Tuesday (Tue→Mon), so a Thu/Fri/Sat/Sun/Mon round holds together —
      but a real Tue/Wed round falls at the start of the *next* window rather than standing alone.
      No midweek rounds until the cups start, so it can wait. `weekblocks._midweek_blocks` already
      distinguishes a round (4+ PL fixtures) from a rearranged game — reuse that rather than a new rule

### Quick wins (1 session each)
- [ ] Install `eslint-plugin-react` so JSX-only identifiers stop reading as unused (13 pre-existing lint errors)
- [ ] Join-a-group flow: the invite link already works end-to-end; what's missing is invite context on the
      auth screen ("You've been invited to Mr Worldwide"). Deferred from the overhaul plan §7
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
2026-08-18

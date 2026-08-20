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
- **Fixtures & Standings rebuild (2026-08-19)** — Favourable Matchups removed (it read as tipping) and
  replaced by two data views built from the football-data results the ladder already fetched: a **Form**
  tab (overall/home/away tables, this season or last) and a **Fixtures** list of one game week at a time,
  with results behind a week stepper. Each side carries its league position and five form dots —
  Results / BTTS / Over 2.5, each available overall or home-and-away. `GET /odds/standings` and
  `GET /odds/fixtures`, both background-cached, no new paid feed.
- **More tab removed (2026-08-19)** — bottom nav is Acca/Fixtures/Table; group actions, Settings, Log out
  and the compliance copy moved into a header menu. Groups get their own page at `/groups`.
- **Weeks always open automatically (2026-08-19)** — the toggle and `groups.auto_weeks` are gone, and the
  season boundary is derived from the first week a group opens rather than being set by hand.
- **PWA install button (2026-08-19)** — on the login page, native prompt on Android, instructions on iOS.
- **Service worker actually updates now (2026-08-19)** — see the fix below; this was why nothing shipped
  since 15 Aug had been seen.
- **Dependency audits clean (2026-08-19)** — npm and pip-audit both pass with nothing ignored.
- **Nudge (2026-08-19 pm)** — a Nudge button on unpicked members' rows once a deadline exists
  (`locks_at` = earliest picked kickoff); sends that member a push with the UK-time deadline, then the
  button becomes "Nudged". Once per target per acca, enforced by a unique constraint (`nudges` table,
  `add_nudges` migration) — refreshing or racing another member gets a 409, so no notification spam.
- **Cleanup pass (2026-08-19 pm)** — Group Settings rebuilt as a header-menu modal (rename, season
  start date, remove member — the admin surface lost with the More tab); dead code swept (routes.py
  tombstone, never-called /users/me/stats, orphaned getMatches); groups.py split into groups +
  groupstats routers and the bookmaker comparison moved out of odds_api into bookmakers.py behind
  two cache accessors; App.jsx split into useAuthSession/useGroups/usePwaUpdate hooks (327 → 128
  lines). Lint: **0 errors, 0 warnings**. AuthView deliberately not split — one mode-machine, five
  forms sharing state; splitting adds prop-drilling, not clarity.
- **Fixtures tab is the one picking surface (2026-08-19 pm)** — the modal picker is gone; "Add your
  pick" navigates to the Fixtures tab, which now joins cached bookmaker odds onto the current week's
  rows (one division per request, `?league=`, nothing fetched for past weeks or empty divisions) and
  hosts the old FixtureCard inline under a tapped row. Odds cache TTL default 2h → 4h. Taken fixtures
  read "Picked by X"; a pick lands you back on your slip. `useCurrentAcca` hook; AccaTab 364 → ~290
  lines. Verified end-to-end against a stubbed odds feed: exactly one paid call per league per TTL
  window, zero on past weeks.
- **UI overhaul (2026-08-15)** — FPL-style 4-tab navigation (Acca/Fixtures/Table/More), group switcher in a
  global header, week-numbered accas with paging, four distinct acca states, pinned odds/returns, first modal
  in the codebase, reworked league table, movement arrows. Shipped and deployed. Plan:
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
      Since verified end-to-end (browser, sandbox, and twice in prod on 19 Aug — deletion, recreation
      and push all observed). `LEAD_DAYS` is now 3, and the pass runs at startup, so a deploy can never
      delay a week opening.
- [x] ~~**Fresh league table for the new season.**~~ — done 2026-08-16. `groups.season_start_date`, set
      by an admin in Group Settings, scopes the leaderboard, the accas-won bar and member profiles
      together. Keyed on `first_match_date`, not `round_number`, which is no longer chronological.
      Null on every existing group, so **you have to set it** (21 Aug 2026) or the table keeps counting
      last season. Week strip is deliberately not scoped — old weeks stay browsable.
- [x] ~~Decide what to do with the lapsed pre-season weeks~~ — deleted automatically once their last
      fixture has passed with no picks (`autoweek.cleanup_lapsed_weeks`).

### Open threads (2026-08-19) — read these first if picking up elsewhere
- [ ] **National League (Carlisle mates) — decision pending one experiment.** The-Odds-API stops at
      League Two (confirmed in their docs), so NL needs another source. Results/form already flow in
      free via football-data.co.uk's `EC` file (ladder-only today, `predictionmodel/config.py`). Two
      odds candidates: (a) football-data.co.uk `fixtures.csv` — free, same team vocabulary, but a
      rolling short-horizon file (Thu download held only Friday's 3 games); **check Saturday morning
      whether EC rows appear** when the NL plays. (b) API-Football — user has an account, NL current
      season confirmed available (free tier is current-season-only, which is all we need); new
      integration + new name reconciliation + non-commercial terms to weigh. Fallbacks that always
      work: EC stats-only in the Fixtures/Standings tabs, and the FA Cup via The-Odds-API for
      occasional live Carlisle odds. Settlement for any NL route rides the EC results file with the
      existing normalization. Decision after Saturday's download
- [x] ~~BookmakerComparison is orphaned~~ — rehomed 2026-08-19 (pm) at the foot of the pick slip
      (`acca/CompareBookmakers.jsx`): button-triggered as before (a backend cache miss can cost
      credits), open accas with picks only, links/click-tracking intact
- [ ] **Legacy `GET /odds/matches/filtered` is unreachable from the new UI but kept alive** — installed
      PWAs run the old shell until their service worker cycles; remove the endpoint once prod has been
      on the new build for a while
- [x] ~~Check `ODDS_CACHE_TTL` on Railway~~ — confirmed clear 2026-08-20, 4h default applies; deploys
      green. Credit baseline before opening weekend: 43/500
- [x] ~~`locks_at_timestamptz` migration runs on next deploy~~ — ran in prod 2026-08-19 (pm): the
      Dockerfile gates uvicorn on `alembic upgrade head`, and every deploy after the commit came up
      (weeks recreated, pushes delivered), so the chain including it completed. Same for `add_nudges`
- [x] ~~The `drop_auto_weeks` migration has not run anywhere real~~ — verified 2026-08-19 (pm) against
      real PostgreSQL 16: the full chain runs from an empty database, and the prod path (DB stamped at
      `add_season_start` with `auto_weeks` present → `upgrade head`) drops the column cleanly. Also
      confirmed the Dockerfile runs `alembic upgrade head` *before* uvicorn imports the app, so
      `create_all()` can never pre-empt the initial migration on a fresh database
- [x] ~~FastAPI 0.128 → 0.141 and starlette 0.50 → 1.3.1 are unverified at runtime~~ — verified
      2026-08-19 (pm) in a sandbox that *can* build `http-ece`: the app boots, lifespan and background
      tasks start, and real requests exercised signup → verify → login → groups → leaderboard →
      logout, token blacklist (revoked token rejected), 1MB size limit (413), login rate limit (429),
      security headers + CSP on every response, CORS preflight, and the new `/odds/standings` and
      `/odds/fixtures` endpoints (200). Also proved the `d843af3` VAPID fix end-to-end: with fresh
      per-send claims, an FCM push and an Apple push each get a JWT for their own audience, while the
      old shared dict pinned both to whichever service was hit first
- [x] ~~Push test~~ — **closed 2026-08-19 (pm): the iPhone received the push.** The full chain is
      confirmed live: re-subscribe after toggling, per-send VAPID claims, 12h TTL, and the
      run-at-startup autoweek pass recreating the week after a deploy
- [ ] **Confirm the group's `season_start_date` is 21 Aug 2026 or earlier, not the 22nd** — now a
      30-second job in the new Group Settings (header menu, admin only). A week's
      `first_match_date` is its Friday opener, so a boundary on the 22nd drops Week 1 out of the season.
      Groups without a date now get one automatically from their first week's earliest date — which is
      the Friday, deliberately — but any group that already had one keeps it unexamined
- [ ] **Genuine midweek rounds group with the following weekend in the Fixtures tab.** `fixturelist.py`
      anchors each game week on the Tuesday (Tue→Mon), so a Thu/Fri/Sat/Sun/Mon round holds together —
      but a real Tue/Wed round falls at the start of the *next* window rather than standing alone.
      No midweek rounds until the cups start, so it can wait. `weekblocks._midweek_blocks` already
      distinguishes a round (4+ PL fixtures) from a rearranged game — reuse that rather than a new rule
- [ ] **Home/Away form dots are mostly blank until ~week 5.** Not a bug: the home side of a round-2
      fixture is usually a club that played away in round 1, so it has no home record yet. An empty
      record renders a dash. Self-resolving; revisit only if it still looks sparse in late September
- [ ] **Position and form on past weeks are "as of now", not as of that week.** Look back at August in
      October and you'll see October's table position beside an August result. Doable — the rows are all
      there — but more work than it's worth unless it grates

### Resolved on 2026-08-19
- [x] ~~Will the opening weekend produce the right week?~~ — simulated `find_week_blocks` with the
      real shape of the opening round (Fri 21 → Mon 24): one block, anchored Sat 22, all four dates
      included — the Friday opener is in. With `LEAD_DAYS = 3` it qualifies from Wed 19, matching the
      push-test expectation below
- [x] ~~Nothing shipped since 15 Aug has been seen in a browser~~ — root cause found and fixed: with
      `strategies: 'injectManifest'`, vite-plugin-pwa does **not** inject the SKIP_WAITING handler, so
      `updateServiceWorker(true)` posted a message nothing listened for. The new worker sat in "waiting"
      forever and every open tab kept the old precached shell. Fixed in `src/sw.js`; the tab has since
      been reviewed extensively on a phone
- [x] ~~Did the auto week fire?~~ — it did, and weeks no longer depend on a per-group toggle at all
- [x] ~~Repo had two branches~~ — `main` is now the default and `master` (six months stale, fully
      contained in `main`) has been deleted

### Quick wins (1 session each)
- [x] ~~Install `eslint-plugin-react`~~ — done 2026-08-19 (pm). Lint is at **0 errors** (2 deliberate
      exhaustive-deps warnings left in App.jsx — the SW-registration and invite-join effects need a
      careful look, not a dep-array sweep). npm audit is clean again too: new advisories had landed
      against babel/brace-expansion/ajv/fast-uri/vite since the morning's pass; all fixed
      non-breaking, vite 7.3.1 → 7.3.6
- [x] ~~Join-a-group flow: invite context on the auth screen~~ — done 2026-08-19 (pm). A public,
      rate-limited `GET /groups/invite/{code}` resolves the parked invite to a name and member count;
      the auth screen shows "You've been invited to X — N mates are already in" and defaults to
      signup. A dead code drops the parked invite so signup isn't followed by a failed-join toast.
      Full journey verified: link → banner → signup → verify → landed in the group as a member
- [ ] Apply new colour palette to CSS variables (palette chosen, waiting for logo/assets)
- [ ] Generate logo (Weavy/Midjourney/Looka) and additional background assets
- [x] ~~Debug push notifications in production~~ — the 19 Aug saga: per-send VAPID claims, 12h TTL,
      startup autoweek pass; closed by a real iPhone delivery
- [ ] General polish pass — remaining pages (groups page, acca/bet slip, fixtures rows, bookmaker comparison, leaderboard, settings)

### Medium effort (1-2 sessions)
- [ ] Add Framer Motion micro-animations (page transitions, card entrances, leaderboard count-ups)
- [ ] Desktop landing page polish (test background on wide viewports, possibly landscape variant)
- [ ] Bookmaker comparison UI refresh (add logos, card-based redesign)
- [ ] Affiliate link setup (research programs, sign up, populate BookmakerLink table, add disclosure)

### Large effort (2-4 sessions)
- [x] ~~More bet types — Over/Under 2.5 and BTTS~~ — already live end-to-end, the backlog was stale:
      both are pickable under "More bets" on a fixture row, priced (totals from the bulk call, BTTS
      lazily at 1 credit/event, 24h cache), and settlement.py settles all four pick types

### Future (multi-session projects)
- [ ] Last Man Standing mode (new game mode: LMSGame, LMSRound, LMSPick models, elimination rounds)
- [ ] Bet Builder feature (single-fixture multi-market bets, needs API research for SGM odds)

## Blockers / Open Questions
- Affiliate programs: need manual research on which bookmakers accept low-traffic affiliates
- Bet Builder: depends on The-Odds-API same-game multi availability (may be limited)
- Last Man Standing: fully independent, no blockers — just needs dedicated sessions

## Next session
Saturday 22 Aug is the opening weekend — first live run of auto-settlement for the new season
(including BTTS/O-U picks if anyone uses More bets). Keep it light and watch: settlement results,
odds-API credit usage (dashboard), and that nudges/pushes behave with real traffic. After that:
affiliate research + comparison UI refresh, logo/palette, or start Last Man Standing.

## Last Updated
2026-08-19 (evening) — session wrap; day log in whatwevedonetoday.md

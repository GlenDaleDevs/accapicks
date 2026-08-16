# Done — 2026-08-15

Updated as tasks are completed during the session.

## UI Overhaul — all four phases complete (8 commits, unpushed)

### Phase 1 — Navigation shell
- [x] Planned the full restructure (`.claude/plans/glittery-coalescing-naur.md`), ran it through `critic`, revised on 7 criticals
- [x] `AppContext` — first shared state container; replaces prop-drilling from `App.jsx`
- [x] Shell: `AppShell` (layout route), `GlobalHeader`, `GroupSwitcher`, `TabBar`
- [x] Routes moved to `/g/:groupId/{acca,fixtures,table,more}` with `useOutlet` page transitions
- [x] Legacy `/groups/*` redirects — settlement pushes deep-link there and those payloads are on devices
- [x] `/` resolver validates `lastGroupId` against the fetched list; cleared on logout and cross-tab logout
- [x] Settings, Logout and the 18+/BeGambleAware footer rehomed into More; `.page-logout-footer` deleted
- [x] `viewport-fit=cover` + safe-area insets; cookie banner above the tab bar; toasts raised to z-index 1100
- [x] Removed the duplicated leaderboard from the Acca tab and the app-level leaderboard fan-out
- [x] Deleted dead code: `TopBar`, `MiniLeaderboard`, `BetCard`, `handleRemoveMember`, `isCurrentUserAdmin`, `loadLeaderboard`

### Fixtures tab placeholder
- [x] Fourth tab with the real All | Favourable (Beta) segmented control, both panels stating work in progress. No fabricated numbers.

### Phase 2 — Acca tab
- [x] Migration `add_round_numbers`: `accas.round_number`, `accas.first_match_date`, `groups.next_round_number`
- [x] Monotonic allocation — a deleted week leaves a gap, its number is never reissued
- [x] 409 if a week would start before the group's latest, making round order == chronological order by construction
- [x] `round_number` exposed in all four payloads (not just `AccaResponse`), `ORDER BY` added to `get_group_accas`
- [x] Four distinct states via `utils/accaState`, plus an "Awaiting results" reading
- [x] Picked count intersects bets with *current* members, so orphaned ex-member bets don't read as Complete
- [x] Week strip with arrows + contextual line; pinned combined odds and £10 returns
- [x] First modal in the codebase: portal, backdrop, scroll lock, focus trap, Escape, aria-modal
- [x] Polling extended to in-play accas (previously open-only, so live results never arrived)
- [x] Deleted `GroupDetail`, `AccaDetail`, `BetSlip` (1,435 lines → ~600)

### Phase 3 — Table + profile
- [x] `Picks` column (`2–1`) + streak inline with the name: fixed tracks 272px → 144px, fixing `Brewi…`
- [x] Streak badge threshold >0 → >=2, matching the row glow that was already >=2
- [x] "Group Record: 0W-3L" → "Accas won 0/3"; column header → "Picks"
- [x] Movement arrows from `round_number` — no snapshot table, no `settled_at`
- [x] Arrows suppressed unless settled picks exist in both windows; column omitted when nothing to compare
- [x] Profile: own pick is the headline, muted strip reads "Acca lost — 4 of 5 landed"

### Shipped to production
- [x] All of the above pushed and deployed (accapicks.com)
- [x] **Lapsed weeks fix** — an acca nobody picked in never locks (auto_lock_accas ignores null locks_at), so it
      sat at "open" months past its fixtures. The tab landed on one and offered picks that could never be made.
      Added an EXPIRED state; "Start week N" becomes prominent when no live week exists
- [x] **Favourable Matchups wired to the real model** — vendored PredictionModel into
      `backend/app/predictionmodel`, refreshed on a 6h background task, served from
      `GET /api/odds/favourable`. Records only, no probabilities, 0.75 differential threshold,
      "Based on 2025/26 home and away form" stated on the card

## Bugs found and fixed along the way
- [x] **Silent password-reset failure** — `send_password_reset_email` returned `None` on failure while `forgot_password` only converted *exceptions* to errors, so the API reported "code sent" when nothing was sent
- [x] **Naive/aware datetime crash on SQLite** — 15 sites. Verify email returned a 500 the UI showed as "Verification Failed"; also broke adding/removing picks, the 60s auto-lock task and the 300s settlement task. Added `timeutils.as_utc`
- [x] **API datetimes had no UTC offset** — JS parsed them as local, so a 14:00 UTC kickoff showed 14:00 instead of 15:00 BST and the countdown was an hour out. Added a `UtcDatetime` serialiser
- [x] Local env repaired: venv was missing 8 packages; local DB was empty on a Feb schema

## Known issues (not fixed)
- **`npm run lint` was already failing before this session** — `eslint-plugin-react` isn't installed, so JSX-only identifiers like `motion` read as unused. Down from 18 to 13 errors; none in new files
- **The migration chain can't run from scratch** — `1129e7a0814d` calls `op.create_table('users')`, duplicating the initial migration. Survives only because production was built by `create_all()` and stamped. **A fresh Railway database would fail to migrate today**
- Stray zero-byte `accapicks.db` at the repo root; `env.py` resolves the sqlite path relative to CWD, so Alembic run from the root targets a different file than the app

## Not verified
- Anything visual: browser extension wasn't connected. Tab bar on iOS PWA safe areas, the four state treatments, modal focus trap, column widths at 360px, movement arrows (need two settled weeks)

---

# Done — 2026-08-16

## Auto-created weeks

Weeks now open by themselves, anchored to the fixture list. Plan:
`C:\Users\glend\.claude\plans\soft-knitting-blanket.md`

- [x] `odds_api.get_events()` — the `/events` endpoint, **zero API credits**, 1h cache, serves stale
      on error so an API blip can't look like an international break
- [x] `weekblocks.py` — pure block detection, no DB or network. A Saturday block spreads into Fri/Sun/Mon
      only where fixtures exist; a midweek block needs ≥4 PL fixtures on a contiguous Tue/Wed/Thu run,
      so the EFL's constant midweek games don't trigger a week on their own
- [x] International breaks need no calendar: no fixtures, no blocks
- [x] `autoweek.py` — creation, extension and lapsed-week cleanup on a 30-min background task
- [x] Auto-created accas are marked by `created_by IS NULL`, which is also what keeps the extension
      pass off manually created ones where the dates were a deliberate choice
- [x] Extension widens a week whose Sunday/Monday fixtures weren't published when it was created,
      and moves `first_match_date` if a Friday appears. Add-only — never strands a pick
- [x] Empty lapsed weeks are deleted once their last fixture has passed. Clears the pre-season ones too
- [x] Push on open: "Week N is open — Sat 22 Aug", via the existing `send_push_to_group`
- [x] `groups.auto_weeks` (migration `add_auto_weeks`), `PATCH /groups/{id}` (admin only), toggle in
      Group Settings, and the no-week card reworded when it's on

## Week ordering relaxed

- [x] **Dropped the create-in-date-order 409.** Auto-creation means a Saturday week is usually already
      open, so slotting a midweek Champions League acca in before it would have been impossible
- [x] Leaderboard movement windows now key off chronological position (`first_match_date`) instead of
      `round_number`, which no longer implies chronology
- [x] Champions League added to the league lists

## Fixed along the way

- [x] **`VALID_SPORT_KEYS` existed twice** — `schemas.py` and `routers/odds.py` — and had drifted.
      Adding Champions League to one still 422'd on the other. `odds.py` now imports from `schemas.py`
- [x] Friday fixtures were excluded from the weekend block on a defensive argument that didn't hold.
      Caught it because the season opener is Friday 21 Aug and would have been unpickable

## Verified

- Block detection against the live fixture list: opening weekend resolves to
  Fri 21 – Mon 24 Aug, one block, no spurious midweek from the lone Thursday EFL game
- Creation / idempotency / extension / out-of-order manual acca / lapsed cleanup, against a throwaway DB
- Endpoints end-to-end: `auto_weeks` defaults on, PATCH toggles it, out-of-order acca returns 201 and
  the list comes back chronological (Week 2 on 19 Aug ahead of Week 1 on 22 Aug)
- Full Alembic chain from an empty database, including `add_auto_weeks`
- `npm run build` clean; `npm run lint` still 13 errors, all pre-existing, none in touched files

## Not verified

- **Nothing visual.** The Group Settings toggle and the reworded no-week card have not been looked at
  in a browser — no local account to log in with. Worth an eye before Saturday
- The push notification itself (VAPID keys still unverified in production — pre-existing)

## Fresh league table for the new season

- [x] `groups.season_start_date` (migration `add_season_start`), nullable. **Left null on every existing
      group** — a migration must not wipe standings on its own, so nothing changes until an admin sets it
- [x] One helper, `_season_accas()`, applied in all three places that read the same bet pool:
      the leaderboard, the acca-stats bar and the member profile. Scoping one and not the others would
      have had a row reading 3–1 open onto a career history
- [x] Filtering the accas is the only change the leaderboard needed — stats, streaks and the movement
      window all derive from them
- [x] `GroupUpdate` is now a genuine partial update (`exclude_unset`), so `season_start_date: null`
      clears the boundary instead of reading as "field omitted", and setting one field keeps the other
- [x] Date input in Group Settings, admin only, with a Clear button
- [x] "Counting from 21 Aug 2026" on the table and the profile — an empty table is alarming until you
      know why it's empty
- [x] Also extracted `_group_or_404()`, replacing four copies of the same fetch-and-check-membership block

## Verified (season boundary)

Three settled accas seeded — two in May, one on 22 Aug — then read back through the real endpoints:

| | table | accas | profile |
|---|---|---|---|
| No boundary | 2–1 (66.7%) | 3 | 2–1, 3 picks |
| Boundary 1 Aug | 0–1 (0.0%) | 1 | 0–1, 1 pick |
| Cleared | 2–1 (66.7%) | 3 | 2–1, 3 picks |

All three agree at every setting. Partial PATCH confirmed both ways: setting `auto_weeks` alone keeps
`season_start_date` and vice versa. Full Alembic chain from empty. Build clean, lint still 13
pre-existing errors.

## Known gap

The **week strip still pages back through last season** — only the table, stats bar and profiles are
season-scoped. Browsing old weeks is arguably right, but if it reads oddly the same helper would do it.

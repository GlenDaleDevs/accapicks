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

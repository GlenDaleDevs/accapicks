# Done — 2026-08-15

Updated as tasks are completed during the session.

## UI Overhaul — Phase 1: Navigation shell

- [x] Planned the full 4-phase FPL-style tab restructure (`.claude/plans/glittery-coalescing-naur.md`), ran it through `critic`, revised
- [x] Added `AppContext` — first shared state container in the app, replaces prop-drilling from `App.jsx`
- [x] Added `src/utils/routes.js` route builders so path strings live in one place
- [x] Built the shell: `AppShell` (layout route), `GlobalHeader`, `GroupSwitcher` dropdown, `TabBar`
- [x] Restructured routing onto `/g/:groupId/{acca,table,more}` with a layout route + `useOutlet` page transitions
- [x] Legacy redirects for `/groups/*` — settlement push notifications deep-link there and those payloads are already on devices
- [x] `/` resolver validates `lastGroupId` against the fetched group list (stops user B landing in user A's group on a shared device); cleared on logout and cross-tab logout
- [x] Rehomed Settings + Logout + the 18+/BeGambleAware footer into the More tab; deleted `.page-logout-footer`
- [x] Added `viewport-fit=cover` and `env(safe-area-inset-bottom)`; cookie banner kept above the tab bar; toasts raised to z-index 1100 for the Phase 2 modal
- [x] Removed the duplicated leaderboard from the Acca tab (Table tab owns standings now)
- [x] Dropped the app-level leaderboard fan-out across every group — only the visible group is fetched now
- [x] Deleted dead components: `TopBar.jsx`, `MiniLeaderboard.jsx`, `BetCard.jsx`, plus dead `handleRemoveMember` / `isCurrentUserAdmin` / `loadLeaderboard` in `GroupDetail`

### Verified
- `npm run build` passes
- All new/changed modules transform cleanly under Vite dev
- Lint: no errors in any new file

### Not yet verified — needs a browser
- Tab bar / group switcher behaviour, safe-area clearance on iOS PWA, background images on More + Acca, legacy redirect round-trip
- Browser extension wasn't connected this session

## Notes
- `npm run lint` was **already failing before this work** — `eslint-plugin-react` isn't installed, so JSX-only identifiers like `motion` are reported unused in `PageTransition.jsx`, `ToastContainer.jsx` and others. 18 pre-existing errors remain; worth fixing separately.
- Football stats API for Favourable Matchups: **none currently in use.** The-Odds-API has no standings/form data. Candidates to evaluate: API-Football (api-sports.io) for League One/Two coverage with home/away splits; football-data.org is cleaner but its free tier likely stops at Championship.

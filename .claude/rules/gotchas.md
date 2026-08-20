# Gotchas

## The-Odds-API /events costs zero credits
`GET /v4/sports/{sport}/events` returns the same fixture list as `/odds` (ids, teams, kickoff times)
without prices, and does not consume a credit. Use it for anything that only needs to know *what is
being played and when* — `odds_api.get_events()` and `predictionmodel/fixtures.py` both rely on this.
It only lists about one round of football ahead, so don't plan on a long lookahead.

## Round numbers are no longer chronological
Accas can be created out of date order (a midweek one-off slotted in before an already-open Saturday
week), so `round_number` is an identity and URL key only. Anything that needs "which week came first"
must sort on `first_match_date` — see the leaderboard's movement window in `routers/groups.py`.

## round_number routes, week_number labels
`Acca.round_number` is a per-group counter that never resets or reissues — it is the URL key
(`/g/:groupId/acca/:roundNumber`) and nothing else. What the UI shows is `week_number`, the position
within the current season, computed in `season.py`. Never render `round_number` directly; use
`weekLabel`/`weekLabelShort` from `src/utils/week.js`.

Consequence: week numbers compact over deletions. A group that skips a Saturday gets that empty acca
deleted, leaving a `round_number` gap, but the following week still reads as the next week of the
season. Accas from a previous season have a null `week_number` and keep their original number,
labelled "past season".

## The season boundary must be applied to all three stats endpoints
`get_group_leaderboard`, `get_acca_stats` and `get_member_picks` read the same bet pool. Scoping one
and not the others makes them contradict each other — a table row reading 3–1 opening onto a career
history looks like a bug. They all go through `_season_accas()` in `routers/groups.py`; use it for any
new endpoint that aggregates bets.

## Auto-created accas are marked by created_by IS NULL
There is no `is_auto` column. `autoweek.py` uses a null creator as the marker, which is also what stops
its extension pass from widening a manually created acca whose dates were a deliberate choice. Side
effect: only a group admin can delete an auto-created week, since there's no creator to match.

<!-- Add entries as you discover them. These save future sessions from repeating mistakes. -->
<!-- Format: ## Short title \n What happens and why, plus the workaround. -->

## background-attachment: fixed is broken on iOS
iOS Safari silently ignores `background-attachment: fixed`. Use regular `background` with position offsets instead.

## FileResponse doesn't auto-detect WebP content-type
FastAPI's `FileResponse` won't set `image/webp` automatically. Pass `media_type="image/webp"` explicitly or browsers may reject the image.

## PWA precache globPatterns must include all asset types
When adding new file types to `public/` (e.g. `.webp`), update `vite.config.js` globPatterns or the service worker won't cache them.

## npm overrides can break packages across major versions
Forcing `ajv>=8.18.0` broke eslint because `@eslint/eslintrc` requires ajv v6 API. Always run lint + build after adding overrides.

## Agent commits don't always push
Backend-dev agent committed but didn't push. Always verify with `git log origin/main` after delegating to agents.

## body background-color breaks negative z-index pseudo-elements
Adding `background-color` to `body` causes `position: fixed; z-index: -2` pseudo-elements to paint behind it. Framer Motion opacity transitions mask the issue temporarily (opacity < 1 creates a stacking context). Fix: add `isolation: isolate` to the pseudo-element's parent container.

## Elements outside page containers get hidden by fixed backgrounds
Historical: `.groups-page`/`.group-detail-page` used `position: fixed; inset: 0` pseudo-elements for
photo backgrounds (removed 2026-08-20 — photo lives on the landing page only now). If a fixed
full-bleed background comes back anywhere, sibling elements (e.g. footer) need
`position: relative; z-index: 1` or they get covered.

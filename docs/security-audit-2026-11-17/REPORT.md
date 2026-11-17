# AccaPicks security audit report (phase 1)

- **Date:** 17 November 2026. **Commit:** `29d41e8`.
- **Standard:** the security, backend and testing rules of `fullstack-auth-starter`.
- **Proofs:** "Proven" means a test in [audit_proofs.py](audit_proofs.py) shows it on a throwaway local PostgreSQL 16. Nothing touched the live site.

**Secrets:** I scanned all 361 commits on every branch. None found; the only matches were the placeholders in `backend/.env.example`.

## Gaps, worst first

| # | Status | Item | Where | What it means for users | Proven? |
|---|---|---|---|---|---|
| 1 | Missing | Outside calls have a time limit (push notifications) | `push.py`, `schemas.py`, `settlement.py` | Any member can take the whole site down. Any `https://` address is accepted as a push endpoint, including internal ones, and sending to it has no time limit. A server that never answers makes picks and nudges hang. If it's hit during settlement, every request hangs. | Yes: stuck for more than 15–30 s; internal host accepted |
| 2 | Missing | A pick can't be changed after kick-off | `routers/bets.py`, `odds_api.verify_pick` | The kick-off time comes from the browser. A hand-made request can pick a match that has already been played, and it gets settled as won. A pick can also be deleted after kick-off. | Yes: a match 100 minutes in settled **won** |
| 3 | Partly | Logout, password change and password reset end sessions | `routers/auth.py` | Logout works. Changing a password signs out only the device you're on. Resetting it signs out nobody, so someone who has taken over an account stays in for up to 30 days. | Yes |
| 4 | Missing | Same root cause as #2 | `routers/bets.py` | A fake "kicks off in 1 minute" locks the week for everybody. | Yes |
| 5 | Missing | Same root cause as #2 | `routers/bets.py`, `settlement.py` | A pick sent without the league skips the server check. Any odds are stored, and the week can never settle. | Yes: still unsettled 60 days later |
| 6 | Partly | Code cooldown, daily limit and guess limit | `routers/auth.py` | There are 5 guesses per code, but fresh codes are unlimited. With enough internet addresses, an attacker could guess a reset code and take the account. | Yes |
| 7 | Missing | Background work stays off the event loop | `main.py` | Lock, settle and clean-up run where every request is answered. A slow odds API stalls the whole site. | Yes: 2.1 s stall |
| 8 | Partly | Joining a group | `routers/groups.py` | The invite code never changes, so a removed member can rejoin straight away. | Yes |
| 9 | Missing | Not on the checklist: email confirmation needs only the code | `routers/auth.py` | With a second sign-up on the same pending address, the owner's code confirms the other person's account and password. | Yes |
| 10 | Partly | Content-Security-Policy and where the token is sent | `main.py`, `index.html`, `client.js` | `'unsafe-inline'` scripts are allowed and `index.html` has an inline script. Google Analytics can read the token. The token is set on `axios.defaults`. Not leaking today; a weaker safety net. | Header seen |
| 11 | Missing | One answer whether or not an account exists | `routers/auth.py` | Locked login gets 403, not 401. Forgot-password errors or is slower only for real accounts. Reset-password messages differ. | Yes |
| 12 | Missing | Refuse a placeholder or short `SECRET_KEY` | `auth.py` | The app starts with the public example key, or a one-letter one. | Yes |
| 13 | Partly | Constant-time comparison; passwords over 72 bytes | `routers/auth.py`, `auth.py` | A non-ASCII code gives a 500. An old bcrypt account with a password over 72 bytes gives a 500. | Yes |
| 14 | Partly | No full emails in logs | `routers/auth.py` | A failed login logs the full email address that was typed. | Yes |
| 15 | Partly | One "who is signed in" check | `routers/auth.py` | A deleted account's token is still accepted. | Yes |
| 16 | Partly | Someone else's data answers 404 | all routers | It answers 403, which confirms the id exists. | Yes |
| 17 | Partly | Every endpoint rate-limited | all routers | Six read endpoints are unlimited: `/auth/me`, `/groups`, `/groups/{id}`, `/groups/{id}/accas`, `/affiliate/links`, `/affiliate/stats`. | Yes |
| 18 | Partly | Small leftovers | various | `bookmaker_key` has no length limit. Delete-account ignores the lockout. Middleware uses `@app.middleware`. Some dependencies aren't pinned. | Read in code |

## Already in place

- **Group isolation (the most important):** membership is checked on the server for every group query. 16 cross-group attempts were all refused. *(Proven.)*
- **Picks:** nobody can change another member's pick.
- **Admin powers:** group admin comes from the membership role, set by the server. Site admin comes from the `ADMIN_USER_IDS` setting only.
- **Odd ids:** on PostgreSQL, large, negative, zero or non-number ids always get a clean 404 or 422. *(Proven.)*
- **Sign-in protections:** dummy hash on unknown accounts, `compare_digest`, `jti` blacklist, and lockout after 10 tries for 15 minutes on login and password change.
- **No raw SQL from input, and no `dangerouslySetInnerHTML`.**
- **Service worker:** never caches `/api/`.
- **Static files:** `../` path traversal is blocked.
- **Secrets:** environment variables only; git history clean.
- **Dependencies:** `npm audit --omit=dev`: 0. `pip-audit`: 0.
- **Time limits:** odds API 10 s, football-data 30 s, Resend 30 s.
- **Migrations:** build cleanly from an empty database.

## Outside parties

- **In the browser:** Google Fonts, plus Google Analytics/Tag Manager after consent. Google Analytics can read the token.
- **Links out:** WhatsApp and Messenger share links, BeGambleAware, GamCare, and bookmaker homepages.
- **From the server:** The Odds API, football-data.co.uk, Resend, and browser push services.

## Other findings

- **Tests:** there are 138 unit tests of pure logic. There are no API tests and no cross-group test.
- **Betting links:** these are not affiliate links. They're plain homepage URLs from a seed migration, marked "Ad", opened with `noopener`, and editable only by a site admin. It's worth checking the UK licence status of Marathonbet, Betsson, Mr Green and LiveScore Bet EU.
- **18+ notice:** the age box is enforced on the server. The 18+ / BeGambleAware footer shows on the auth, groups, app-shell and settings screens.
- **Deployment:** Docker on Railway, auto-deployed from `main`. The container runs `alembic upgrade head` on every start, so a merged migration runs on the live database during deploy. Take the backup before merging.
- **Backups:** nothing in the repository makes them. Take one with `pg_dump "<DATABASE_PUBLIC_URL>" -Fc -f accapicks-YYYY-MM-DD.dump`. Restore it into a fresh database with `pg_restore --no-owner -d "<new database URL>" <file>`, then point `DATABASE_URL` at it.
- **Can't be checked from the code:** whether `ENVIRONMENT=production` is set in Railway. It hides `/docs` and the debug-settlement endpoint.

## Fix order (agreed with the owner after the report)

Sign-up is open to anyone, so the order is:

1. **Push notifications and background tasks (#1, #7).** Medium. No database change.
2. **Pick integrity (#2, #4, #5).** Small to medium. No database change.
3. **Sessions end on password change and reset (#3).** Medium. Needs a new migration and a fresh backup first.

Then the code limits (#6). One fix per pull request, each with a test that fails without it.

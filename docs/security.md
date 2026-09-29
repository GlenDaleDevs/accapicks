# Security

Security has been treated as a feature of this project rather than an afterthought: the measures below were built iteratively across three rounds of adversarial auditing (pen-test-style passes over auth, groups, betting logic, and the frontend), with every critical and high finding fixed and re-audited.

## Authentication

- **JWT with revocation.** Tokens carry a `jti` claim and are checked against a blacklist on every authenticated request; logout and password change blacklist the current token immediately rather than letting it ride to expiry.
- **bcrypt password hashing**, with a dummy hash run on failed user lookups so response timing can't be used to enumerate accounts.
- **Account lockout** — repeated failed attempts lock the account for a cooldown period, applied to login *and* password change (a stolen token doesn't get a free brute-force of the current password).
- **Constant-time comparison** (`hmac.compare_digest`) for verification codes and other secret comparisons.
- Email verification with attempt limits on code entry.

## Authorization & input validation

- Every endpoint resolves group membership server-side before touching group data; admin-only actions check the membership role, never client-supplied claims.
- All input validated server-side with Pydantic schemas; the ORM is used exclusively (no raw SQL with user input).
- User-supplied text is sanitized against stored XSS; the React frontend never uses `dangerouslySetInnerHTML`.
- Invite codes are stripped to alphanumerics and length-capped server-side.

## Settlement integrity

The leaderboard is the product, so bet results are deliberately **not editable by anyone**:

- No manual settlement endpoints exist — results come only from the automated settlement engine reading live score data.
- Deleting an in-play acca is blocked once any leg has a result, so a losing week can't be erased.
- Unresolvable bets (abandoned matches, legacy data) are auto-voided by policy, not by hand.
- Diagnostic endpoints are restricted to the acca creator or group admin and redact internal errors.

## Transport & headers

- Security headers middleware: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and `HSTS` (only when behind HTTPS, so local dev isn't broken).
- Request body size limit on mutating requests as defence in depth.
- Registered ahead of CORS so headers apply to every response (Starlette middleware is LIFO).

## Rate limiting

- All auth endpoints, destructive endpoints, and database-touching status endpoints are rate-limited.
- The limiter keys on the *first* IP in `X-Forwarded-For` (the client), not the last (the proxy).

## Operations

- Swagger/ReDoc disabled in production.
- `.dockerignore` excludes env files, local databases, and build artefacts from images.
- `npm audit` and `pip-audit` run in CI on every push (`.github/workflows/security.yml`).
- Security events (failed logins, lockouts, blacklisted-token use, settlement anomalies) are logged with user IDs but never passwords, tokens, or full email addresses.

## Audit history

Three audit rounds were run against the deployed app, each a fresh adversarial pass (auth exploits, IDOR, injection, business-logic abuse, race conditions, API abuse):

| Round | Outcome |
|---|---|
| V1 | Initial audit — findings drove the token blacklist, lockout, rate-limiter and header work above |
| V2 | Fix verification + new pass over group/betting logic |
| V3 | 40 findings, **0 critical / 0 high**; remaining items were edge-case warnings and UX suggestions, several of which (lock-time recalculation on membership change, admin transfer, acca deletion, double-submit guards) have since been implemented |

The standing rules distilled from these audits live in `.claude/rules/security.md` and are applied to all new code.

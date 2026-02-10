# Security Rules

Rules derived from security audits. Follow these when writing any new code.

## Authentication & Tokens

- All new JWT tokens must include a `jti` claim for revocation support
- Always check the token blacklist in auth dependencies before granting access
- Password changes and logout must blacklist the current token
- Never store secrets in frontend code — only `VITE_*` env vars are exposed to the browser
- Use `hmac.compare_digest()` for any secret comparison (verification codes, tokens)
- Always run a dummy bcrypt on failed lookups to prevent timing-based user enumeration
- Account lockout: 10 failed attempts = 15-min lockout. Apply to login AND password change

## Input Validation

- All user input validated server-side via Pydantic schemas — never trust client-only validation
- Use SQLAlchemy ORM for all queries — no raw SQL with user input
- Sanitize/strip HTML from user text input to prevent stored XSS
- Invite codes: regex-strip non-alphanumeric, enforce max 6 chars server-side
- Validate Content-Length header with try/except (can be non-numeric)
- Validate date query params with regex `^\d{4}-\d{2}-\d{2}$` — don't rely on string comparison alone

## Headers & Middleware

- Security headers middleware must be registered BEFORE CORS in code (Starlette LIFO order)
- Required headers: X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy, Permissions-Policy
- HSTS only when `x-forwarded-proto: https` (don't break local dev)
- CSP must include all external origins: Google Fonts, Google Analytics, Google Tag Manager
- Request size limit (1MB) on POST/PUT/PATCH as defense-in-depth

## Rate Limiting

- Rate limiter must use FIRST IP in X-Forwarded-For (`split(",")[0]`), not last — last is the proxy
- All auth endpoints must be rate-limited (signup: 5/min, login: 10/min, logout: 10/min)
- Destructive endpoints (delete account, leave group) should be rate-limited
- Admin-only endpoints still need rate limits — don't skip just because auth is required
- Health/status endpoints must be rate-limited if they hit the database

## Settlement

- **No manual settlement endpoints** — all bet results determined by auto-settlement only
- Never expose endpoints that let users mark bets as won/lost — this is a leaderboard manipulation vector
- Team name matching uses normalized comparison (`backend/app/normalization.py`) — always guard against empty strings
- Legacy bets (no `event_id`) are auto-voided after 7 days — no manual intervention path
- Cancelled/abandoned matches (48h+ incomplete) are auto-voided
- Score lookup window is 14 days max — sufficient for delayed results without API abuse
- Debug/diagnostic endpoints must be restricted to acca creator or group admin
- Debug endpoints must redact internal errors — log full error server-side, return generic message to client

## Logging

- Log security events: failed logins, failed password changes, account lockouts, blacklisted token usage
- Log both the attempt AND the lockout trigger (separate log lines)
- Include user_id in security logs where available
- Never log passwords, tokens, or full email addresses
- Settlement: log at INFO for <72h missing scores, WARNING for 72h+ stale matches

## Production

- Swagger/ReDoc disabled when `ENVIRONMENT=production`
- .dockerignore must exclude .env, *.db, node_modules, __pycache__
- Run `npm audit` and `pip-audit` before major deploys
- `Base.metadata.create_all()` runs before Alembic — always use `IF NOT EXISTS` guards in migrations
- Environment variables with admin/privilege implications must default to empty, never to a valid ID

## Frontend

- JWT stored in localStorage (acceptable given no XSS vectors, 30-min expiry)
- Call backend logout endpoint BEFORE clearing localStorage on logout
- React JSX auto-escapes — never use `dangerouslySetInnerHTML`
- Always use `type="email"` only on email-only fields, not mixed input fields

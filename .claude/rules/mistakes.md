# Rules (learned from mistakes)

**Every time a bug or mistake is encountered, add a new rule here immediately.**

- Always save assessments, feature plans, and multi-item lists to a .txt file — context compaction will lose them
- Always follow the plan > critic > implement pipeline for non-trivial changes. Ask the user before skipping
- Always delegate implementation to agents — don't implement directly in main conversation
- After code review fixes, always `npm run build` before committing to catch syntax/import errors
- When adding new enum values in the backend, check that the frontend handles ALL possible values
- Case sensitivity matters everywhere — always use `func.lower()` or `.lower()` for user-facing string comparisons
- Mobile keyboard: use `type="email"` for email-only fields, `type="text"` + `inputMode="email"` for mixed fields
- When deleting user data, consider cascade effects on related data (e.g. deleting bets can leave accas inconsistent)
- The-Odds-API sport keys: `soccer_efl_champ` (Championship), `soccer_england_league1` (League One), `soccer_england_league2` (League Two)
- Leaderboards must include members with 0 bets — start from members list, not from bets
- `locks_at` must be calculated from earliest kickoff of **actually picked** matches, not all matches. Recalculate on every bet add/remove
- Railway deploy logs only show build/startup — for runtime debugging, return debug info in API response and check via DevTools
- `Base.metadata.create_all()` runs before Alembic migrations — use `IF NOT EXISTS` guards in migrations that create tables

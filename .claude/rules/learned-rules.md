# Learned Rules

Rules accumulated from mistakes via the `/improve` command. Each rule was learned the hard way.

- PROBLEM: Added a league to `VALID_SPORT_KEYS` in `routers/odds.py` but an identical set existed in `schemas.py`, so acca creation still 422'd -> RULE: Before editing a constant, grep for its name across the whole backend — if it appears twice, consolidate to one definition rather than updating both
- PROBLEM: Excluded Friday fixtures from the auto-created weekend on a defensive argument, and the season opener is a Friday -> RULE: When a rule excludes data, check it against the *next real* input before shipping — not against the hypothetical it was written for
- PROBLEM: Deleting `GroupDetail`/`AccaDetail` in the UI overhaul silently removed the only caller of `deleteAcca`, leaving the endpoint unreachable for a month -> RULE: When deleting a component, grep `src/api/client.js` for every function it called and confirm each still has a caller — an orphaned client function is a feature that quietly vanished

<!-- Format: - PROBLEM: [what went wrong] -> RULE: [the fix] -->
<!-- Example: - PROBLEM: Edited file without reading it first -> RULE: ALWAYS read a file before modifying it -->

<!-- Generic rules now live in C:\Users\glend\.claude\rules\shared-learned-rules.md -->
<!-- Only project-specific rules go here -->


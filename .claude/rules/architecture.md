# Architecture

<!-- Fill this in as the project takes shape. Delete sections that don't apply. -->

## Directory Structure
<!-- e.g. src/ — application code, lib/ — shared utilities -->

## Key Components
<!-- How the main pieces connect. Data flow, entry points. -->

### Automatic week creation
`weekblocks.py` → `autoweek.py` → background task in `main.py` (30-minute tick).

- `weekblocks.py` is pure: fixture lists in, `{anchor, dates}` blocks out. No DB, no network, so it can
  be driven from a script against live fixtures.
- `autoweek.run_once()` does cleanup → extend → create, in that order.
- Only groups with `groups.auto_weeks` are touched. `LEAD_DAYS = 4` controls how early a week opens.
- Kickoffs come back as UTC and are bucketed through `ZoneInfo("Europe/London")`, which is why `tzdata`
  is a requirement — Windows has no system zone database.

## Database / State
<!-- Schema overview, ORM details, state management approach -->

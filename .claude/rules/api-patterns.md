# API Patterns

<!-- Fill in when the project has API endpoints. Delete if not applicable. -->

## Endpoints
<!-- Route conventions, versioning, naming -->

## Auth
<!-- Auth method, token handling, middleware -->

## Error Responses
<!-- Standard error format, status codes, error types -->

## Request Validation
<!-- Where and how input is validated -->

- `schemas.VALID_SPORT_KEYS` is the single whitelist of league keys. `routers/odds.py` imports it —
  do not redeclare it there, they drifted once already.
- Group settings changes go through `PATCH /groups/{group_id}` with `schemas.GroupUpdate`, admin only
  (`membership.role == "admin"`), rate limited at 10/minute. It is a genuine partial update — fields
  are applied via `model_dump(exclude_unset=True)`, so a nullable field can be explicitly cleared by
  sending `null` without that being confused for "omitted". New optional fields must follow this.
- `_group_or_404(db, group_id, user_id)` fetches a group and checks membership in one step. Use it
  instead of hand-rolling the query-then-403 block again.

# Security audit, 17 November 2026

- **Audited commit:** `29d41e8` ("Send Samsung Internet users to Chrome to install the app"), then the tip of `main`.
- **Reference standard:** `.claude/rules/security.md`, `backend.md` and `testing.md` in `GlenDaleDevs/fullstack-auth-starter`.
- **Report:** [REPORT.md](REPORT.md), with gaps ranked worst first and the order of fixes.
- **Proofs:** [audit_proofs.py](audit_proofs.py), 24 tests that show each finding on a throwaway local database.

This folder is documents only. Nothing the app runs reads it. The Docker image copies only `backend/`, `alembic/` and the built `dist/`. CI's backend job runs `pytest` from `backend/`, whose `testpaths = tests` doesn't reach this folder. The proof file's name also doesn't match `test_*.py`.

## What the proofs mean

Each proof asserts the behaviour **as found at audit time**:

- For a gap, the proof passing means the gap is still there. Once a gap is fixed, its proof is expected to **fail**, and that's the sign the fix worked. The permanent regression test for each fix goes in `backend/tests/` with the fix itself.
- Two are marked `CHECK`: `test_cross_group_isolation` and `test_odd_ids`. They show protections that already worked, so they should keep passing.

## How to run them

> **Never point these at the live database.** Every test drops and recreates every table. The file
> refuses to run unless `DATABASE_URL` is on `127.0.0.1`, `localhost`, or SQLite.

1. Start a throwaway PostgreSQL, the same type as production. For example, with Docker:
   ```bash
   docker run --rm -d --name audit-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 55432:5432 postgres:16
   ```
2. Install the backend packages into a virtualenv:
   ```bash
   pip install -r backend/requirements.txt -r backend/requirements-dev.txt httpx
   ```
3. Run the proofs from `backend/`. Use any long random `SECRET_KEY`; leave the email and push keys unset.
   ```bash
   cd backend
   DATABASE_URL=postgresql://postgres@127.0.0.1:55432/postgres \
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
   python -m pytest -s -p no:cacheprovider ../docs/security-audit-2026-11-17/audit_proofs.py
   ```
   `-s` prints a `PROOF` or `CHECK` line for each finding. At the audited commit, all 24 pass in about 30 seconds.
4. When you've finished: `docker stop audit-pg`.

On Windows, run step 3 in Git Bash or WSL, or set the two variables with `set` first.

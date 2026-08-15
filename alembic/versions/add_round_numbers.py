"""add acca round numbers and first match date

Revision ID: add_round_numbers
Revises: add_push_subscriptions
Create Date: 2026-08-15

Adds the "Week N" identity:
  - accas.round_number     display identity + stable URL key
  - accas.first_match_date chronological sort key (created_at is NOT chronological)
  - groups.next_round_number monotonic high-water mark, never decremented

Column adds are guarded with an inspector check rather than IF NOT EXISTS:
Base.metadata.create_all() runs before Alembic in this project, so on a fresh
database the columns already exist by the time this runs. SQLite also has no
ADD COLUMN IF NOT EXISTS.
"""
from typing import Sequence, Union
from datetime import date

from alembic import op
import sqlalchemy as sa

revision: str = 'add_round_numbers'
down_revision: Union[str, None] = 'add_push_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set:
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _indexes(table: str) -> set:
    bind = op.get_bind()
    return {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()

    acca_cols = _columns("accas")
    if "round_number" not in acca_cols:
        op.add_column("accas", sa.Column("round_number", sa.Integer(), nullable=True))
    if "first_match_date" not in acca_cols:
        op.add_column("accas", sa.Column("first_match_date", sa.Date(), nullable=True))

    if "next_round_number" not in _columns("groups"):
        op.add_column(
            "groups",
            sa.Column("next_round_number", sa.Integer(), nullable=False, server_default="1"),
        )

    acca_indexes = _indexes("accas")
    if "ix_accas_round_number" not in acca_indexes:
        op.create_index("ix_accas_round_number", "accas", ["round_number"])
    if "ix_accas_first_match_date" not in acca_indexes:
        op.create_index("ix_accas_first_match_date", "accas", ["first_match_date"])

    # ---- Backfill ----
    # match_dates is JSON; parse in Python rather than relying on JSON functions
    # that differ between SQLite and Postgres.
    rows = bind.execute(
        sa.text("SELECT id, group_id, match_dates, created_at FROM accas")
    ).fetchall()

    parsed = []
    for row in rows:
        raw = row.match_dates
        if isinstance(raw, str):
            import json
            try:
                raw = json.loads(raw)
            except ValueError:
                raw = None
        first = None
        if raw:
            try:
                first = date.fromisoformat(min(raw))
            except (ValueError, TypeError):
                first = None
        parsed.append((row.id, row.group_id, first, row.created_at))

    # Number per group in chronological order, tie-breaking on created_at.
    # Accas with no parseable dates sort last so they can't shift real weeks.
    by_group = {}
    for acca_id, group_id, first, created_at in parsed:
        by_group.setdefault(group_id, []).append((acca_id, first, created_at))

    for group_id, accas in by_group.items():
        accas.sort(key=lambda a: (a[1] is None, a[1] or date.max, a[2] or ""))
        for index, (acca_id, first, _created) in enumerate(accas, start=1):
            bind.execute(
                sa.text(
                    "UPDATE accas SET round_number = :rn, first_match_date = :fmd WHERE id = :id"
                ),
                {"rn": index, "fmd": first, "id": acca_id},
            )
        # Next allocation continues past the highest number handed out.
        bind.execute(
            sa.text("UPDATE groups SET next_round_number = :nxt WHERE id = :gid"),
            {"nxt": len(accas) + 1, "gid": group_id},
        )


def downgrade() -> None:
    acca_indexes = _indexes("accas")
    if "ix_accas_first_match_date" in acca_indexes:
        op.drop_index("ix_accas_first_match_date", table_name="accas")
    if "ix_accas_round_number" in acca_indexes:
        op.drop_index("ix_accas_round_number", table_name="accas")

    if "next_round_number" in _columns("groups"):
        op.drop_column("groups", "next_round_number")

    acca_cols = _columns("accas")
    if "first_match_date" in acca_cols:
        op.drop_column("accas", "first_match_date")
    if "round_number" in acca_cols:
        op.drop_column("accas", "round_number")

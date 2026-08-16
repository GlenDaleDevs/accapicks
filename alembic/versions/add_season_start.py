"""add groups.season_start_date

Revision ID: add_season_start
Revises: add_auto_weeks
Create Date: 2026-08-16

The season boundary for the league table. Deliberately left NULL on every
existing group: a migration must not silently wipe a group's standings. Each
group's admin sets the date themselves, and until they do nothing changes.

Guarded with an inspector check rather than IF NOT EXISTS — Base.metadata
.create_all() runs before Alembic in this project, so on a fresh database the
column already exists by the time this runs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_season_start'
down_revision: Union[str, None] = 'add_auto_weeks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set:
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    if "season_start_date" not in _columns("groups"):
        op.add_column("groups", sa.Column("season_start_date", sa.Date(), nullable=True))


def downgrade() -> None:
    if "season_start_date" in _columns("groups"):
        op.drop_column("groups", "season_start_date")

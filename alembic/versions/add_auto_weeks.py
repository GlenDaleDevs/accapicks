"""add groups.auto_weeks

Revision ID: add_auto_weeks
Revises: add_round_numbers
Create Date: 2026-08-16

Switches on automatic week creation for every existing group. The column is
guarded with an inspector check rather than IF NOT EXISTS: Base.metadata
.create_all() runs before Alembic in this project, so on a fresh database the
column already exists by the time this runs. SQLite also has no
ADD COLUMN IF NOT EXISTS.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_auto_weeks'
down_revision: Union[str, None] = 'add_round_numbers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set:
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    if "auto_weeks" not in _columns("groups"):
        op.add_column(
            "groups",
            sa.Column("auto_weeks", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    if "auto_weeks" in _columns("groups"):
        op.drop_column("groups", "auto_weeks")

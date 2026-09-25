"""add groups.skipped_saturday

Revision ID: add_skipped_saturday
Revises: add_pick_notifications
Create Date: 2026-09-25

Anchor Saturday of a week the admin deleted while it was still open and
auto-created. The auto-week task checks this before recreating a weekend, so
a deliberately-skipped week doesn't reappear 30 minutes later. Only the most
recent skip is kept; a past date here is inert.

Guarded with an inspector check rather than IF NOT EXISTS — Base.metadata
.create_all() runs before Alembic in this project, so on a fresh database the
column already exists by the time this runs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_skipped_saturday'
down_revision: Union[str, None] = 'add_pick_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set:
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    if "skipped_saturday" not in _columns("groups"):
        op.add_column("groups", sa.Column("skipped_saturday", sa.Date(), nullable=True))


def downgrade() -> None:
    if "skipped_saturday" in _columns("groups"):
        op.drop_column("groups", "skipped_saturday")

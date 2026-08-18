"""drop groups.auto_weeks

Weeks now open automatically for every group, so the per-group opt-out is gone.
Nothing reads the column any more; dropping it stops it drifting out of sync
with behaviour.

Revision ID: drop_auto_weeks
Revises: add_season_start
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'drop_auto_weeks'
down_revision: Union[str, None] = 'add_season_start'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table):
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    # Base.metadata.create_all() runs before Alembic, so guard rather than
    # assume the column is there.
    if "auto_weeks" in _columns("groups"):
        op.drop_column("groups", "auto_weeks")


def downgrade() -> None:
    if "auto_weeks" not in _columns("groups"):
        op.add_column(
            "groups",
            sa.Column("auto_weeks", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

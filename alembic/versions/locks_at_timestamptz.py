"""accas.locks_at: varchar -> timestamptz on chain-built databases

The initial schema (2d7e70c20e78) creates locks_at as a String, and the
revision meant to convert it (1129e7a0814d) early-returns whenever the users
table exists — which, on a fresh chain run, it always does, because the
initial migration just created it. So any database built purely from the
chain keeps locks_at as varchar while the model says DateTime(timezone=True),
and the accas list 500s on response validation as soon as a pick sets a lock
time. Production never hit this because its column predates the chain.

Revision ID: locks_at_timestamptz
Revises: drop_auto_weeks
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'locks_at_timestamptz'
down_revision: Union[str, None] = 'drop_auto_weeks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _locks_at_type():
    bind = op.get_bind()
    col = next(c for c in sa.inspect(bind).get_columns("accas")
               if c["name"] == "locks_at")
    return col["type"]


def upgrade() -> None:
    # Guarded: production's column is already timestamptz, and SQLite dev
    # databases neither need nor support the cast.
    if op.get_bind().dialect.name != "postgresql":
        return
    if isinstance(_locks_at_type(), (sa.String, sa.Text)):
        op.execute(
            "ALTER TABLE accas ALTER COLUMN locks_at "
            "TYPE TIMESTAMP WITH TIME ZONE USING locks_at::timestamptz"
        )


def downgrade() -> None:
    # No-op: a datetime column satisfies every reader the varchar did.
    return

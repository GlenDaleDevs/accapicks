"""add push subscriptions table

Revision ID: add_push_subscriptions
Revises: void_legacy_bets
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_push_subscriptions'
down_revision: Union[str, None] = 'void_legacy_bets'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            endpoint_hash VARCHAR NOT NULL,
            subscription_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_used_at TIMESTAMPTZ,
            CONSTRAINT uq_push_sub_user_endpoint UNIQUE (user_id, endpoint_hash)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_push_subscriptions_id ON push_subscriptions (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_push_subscriptions_user_id ON push_subscriptions (user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS push_subscriptions")

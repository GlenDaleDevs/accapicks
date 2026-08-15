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
    # Was raw SQL using SERIAL / TIMESTAMPTZ / NOW(), which are Postgres-only
    # and made a from-scratch SQLite rebuild impossible. op.create_table renders
    # correctly for both dialects; the inspector guard keeps the original
    # IF NOT EXISTS behaviour.
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "push_subscriptions" not in inspector.get_table_names():
        op.create_table(
            "push_subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(),
                      sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("endpoint_hash", sa.String(), nullable=False),
            sa.Column("subscription_json", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("user_id", "endpoint_hash", name="uq_push_sub_user_endpoint"),
        )

    existing_indexes = {i["name"] for i in sa.inspect(bind).get_indexes("push_subscriptions")}
    if "ix_push_subscriptions_id" not in existing_indexes:
        op.create_index("ix_push_subscriptions_id", "push_subscriptions", ["id"])
    if "ix_push_subscriptions_user_id" not in existing_indexes:
        op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS push_subscriptions")

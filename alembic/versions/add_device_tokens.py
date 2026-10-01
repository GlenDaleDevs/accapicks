"""add group_members.device_token_hash and device_last_seen_at

Revision ID: add_device_tokens
Revises: add_skipped_saturday
Create Date: 2026-10-01

Each group member can hold one revocable token for an IoT display.
device_token_hash is the sha256 hex of an `apk_...` token (the raw token is
never stored); device_last_seen_at records the display's last request. They
live on the membership row so the token dies with it — leaving, removal or
account deletion revokes it with no extra bookkeeping.

Guarded with inspector checks rather than IF NOT EXISTS — Base.metadata
.create_all() runs before Alembic in this project, so on a fresh database the
columns and the unique index (from unique=True, index=True on the model)
already exist by the time this runs.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'add_device_tokens'
down_revision: Union[str, None] = 'add_skipped_saturday'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_group_members_device_token_hash"


def _columns(table: str) -> set:
    bind = op.get_bind()
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _indexes(table: str) -> set:
    bind = op.get_bind()
    return {i["name"] for i in sa.inspect(bind).get_indexes(table)}


def upgrade() -> None:
    cols = _columns("group_members")
    if "device_token_hash" not in cols:
        op.add_column("group_members", sa.Column("device_token_hash", sa.String(length=64), nullable=True))
    if "device_last_seen_at" not in cols:
        op.add_column("group_members", sa.Column("device_last_seen_at", sa.DateTime(timezone=True), nullable=True))
    if INDEX_NAME not in _indexes("group_members"):
        op.create_index(INDEX_NAME, "group_members", ["device_token_hash"], unique=True)


def downgrade() -> None:
    if INDEX_NAME in _indexes("group_members"):
        op.drop_index(INDEX_NAME, table_name="group_members")
    cols = _columns("group_members")
    if "device_last_seen_at" in cols:
        op.drop_column("group_members", "device_last_seen_at")
    if "device_token_hash" in cols:
        op.drop_column("group_members", "device_token_hash")

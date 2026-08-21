"""add pick notifications table

One row per (acca, user) who has already had a "made a pick" push sent for
them. The unique constraint enforces one notification per picker per acca,
ever, so a re-pick (delete + re-create the bet) never re-fires the push.
The row deliberately survives bet deletion.

Revision ID: add_pick_notifications
Revises: add_nudges
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'add_pick_notifications'
down_revision: Union[str, None] = 'add_nudges'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Base.metadata.create_all() can run before Alembic on some paths, so
    # guard rather than assume the table is absent.
    if "pick_notifications" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        'pick_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('acca_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['acca_id'], ['accas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('acca_id', 'user_id', name='uq_pick_notif_acca_user'),
    )
    op.create_index(op.f('ix_pick_notifications_id'), 'pick_notifications', ['id'], unique=False)
    op.create_index(op.f('ix_pick_notifications_acca_id'), 'pick_notifications', ['acca_id'], unique=False)


def downgrade() -> None:
    if "pick_notifications" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_index(op.f('ix_pick_notifications_acca_id'), table_name='pick_notifications')
        op.drop_index(op.f('ix_pick_notifications_id'), table_name='pick_notifications')
        op.drop_table('pick_notifications')

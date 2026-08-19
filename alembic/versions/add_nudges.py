"""add nudges table

One row per (acca, target) — a member reminding another to pick. The unique
constraint is the anti-spam rule.

Revision ID: add_nudges
Revises: locks_at_timestamptz
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'add_nudges'
down_revision: Union[str, None] = 'locks_at_timestamptz'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Base.metadata.create_all() can run before Alembic on some paths, so
    # guard rather than assume the table is absent.
    if "nudges" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        'nudges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('acca_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('nudged_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['acca_id'], ['accas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['nudged_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('acca_id', 'target_user_id', name='uq_nudge_acca_target'),
    )
    op.create_index(op.f('ix_nudges_id'), 'nudges', ['id'], unique=False)
    op.create_index(op.f('ix_nudges_acca_id'), 'nudges', ['acca_id'], unique=False)


def downgrade() -> None:
    if "nudges" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_index(op.f('ix_nudges_acca_id'), table_name='nudges')
        op.drop_index(op.f('ix_nudges_id'), table_name='nudges')
        op.drop_table('nudges')

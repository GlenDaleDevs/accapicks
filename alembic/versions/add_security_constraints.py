"""add security constraints

Revision ID: add_security_constraints
Revises: add_settlement_fields
Create Date: 2026-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_security_constraints'
down_revision: Union[str, None] = 'add_settlement_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add security columns to users table
    op.add_column('users', sa.Column('verification_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # Add unique constraints to bets table
    op.create_unique_constraint('uq_bet_acca_user', 'bets', ['acca_id', 'user_id'])
    op.create_unique_constraint('uq_bet_acca_description', 'bets', ['acca_id', 'description'])

    # Add unique constraint to group_members table
    op.create_unique_constraint('uq_groupmember_group_user', 'group_members', ['group_id', 'user_id'])


def downgrade() -> None:
    # Drop unique constraints
    op.drop_constraint('uq_groupmember_group_user', 'group_members', type_='unique')
    op.drop_constraint('uq_bet_acca_description', 'bets', type_='unique')
    op.drop_constraint('uq_bet_acca_user', 'bets', type_='unique')

    # Drop security columns from users table
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'verification_attempts')

"""add token blacklist table

Revision ID: add_token_blacklist
Revises: add_security_constraints
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_token_blacklist'
down_revision: Union[str, None] = 'add_security_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'blacklisted_tokens' not in inspector.get_table_names():
        op.create_table(
            'blacklisted_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('jti', sa.String(), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('blacklisted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_blacklisted_tokens_id', 'blacklisted_tokens', ['id'])
        op.create_index('ix_blacklisted_tokens_jti', 'blacklisted_tokens', ['jti'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_blacklisted_tokens_jti', table_name='blacklisted_tokens')
    op.drop_index('ix_blacklisted_tokens_id', table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens')

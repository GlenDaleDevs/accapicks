"""add email verification fields

Revision ID: add_email_verification
Revises: 1129e7a0814d
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_email_verification'
down_revision: Union[str, None] = '1129e7a0814d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('verification_code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('verification_code_expires', sa.DateTime(timezone=True), nullable=True))

    # Set existing users as verified (they signed up before this feature)
    op.execute("UPDATE users SET email_verified = true WHERE email_verified IS NULL")


def downgrade() -> None:
    op.drop_column('users', 'verification_code_expires')
    op.drop_column('users', 'verification_code')
    op.drop_column('users', 'email_verified')

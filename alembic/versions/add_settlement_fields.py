"""add settlement fields

Revision ID: add_settlement_fields
Revises: add_bookmaker_affiliate
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_settlement_fields'
down_revision: Union[str, None] = 'add_bookmaker_affiliate'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add settlement fields to bets table (all nullable for backward compatibility)
    op.add_column('bets', sa.Column('event_id', sa.String(), nullable=True))
    op.add_column('bets', sa.Column('home_team', sa.String(), nullable=True))
    op.add_column('bets', sa.Column('away_team', sa.String(), nullable=True))
    op.add_column('bets', sa.Column('pick_type', sa.String(), nullable=True))
    op.add_column('bets', sa.Column('sport_key', sa.String(), nullable=True))
    op.add_column('bets', sa.Column('commence_time', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove settlement fields from bets table
    op.drop_column('bets', 'commence_time')
    op.drop_column('bets', 'sport_key')
    op.drop_column('bets', 'pick_type')
    op.drop_column('bets', 'away_team')
    op.drop_column('bets', 'home_team')
    op.drop_column('bets', 'event_id')

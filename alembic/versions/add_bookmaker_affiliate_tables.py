"""add bookmaker affiliate tables

Revision ID: add_bookmaker_affiliate
Revises: add_email_verification
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_bookmaker_affiliate'
down_revision: Union[str, None] = 'add_email_verification'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bookmaker_links table
    op.create_table(
        'bookmaker_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bookmaker_key', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookmaker_links_id'), 'bookmaker_links', ['id'], unique=False)
    op.create_index(op.f('ix_bookmaker_links_bookmaker_key'), 'bookmaker_links', ['bookmaker_key'], unique=True)

    # Create bookmaker_clicks table
    op.create_table(
        'bookmaker_clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bookmaker_key', sa.String(), nullable=False),
        sa.Column('acca_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookmaker_clicks_id'), 'bookmaker_clicks', ['id'], unique=False)
    op.create_index(op.f('ix_bookmaker_clicks_bookmaker_key'), 'bookmaker_clicks', ['bookmaker_key'], unique=False)

    # Seed bookmaker_links from constants.js
    # Deduplicated: removed "888sport" (keep sport888) and "livescorebet" (keep livescorebet_eu)
    bookmakers = [
        ("bet365", "Bet365", "https://www.bet365.com"),
        ("williamhill", "William Hill", "https://www.williamhill.com"),
        ("paddypower", "Paddy Power", "https://www.paddypower.com"),
        ("betfair", "Betfair", "https://www.betfair.com"),
        ("unibet_uk", "Unibet", "https://www.unibet.co.uk"),
        ("betway", "Betway", "https://www.betway.com"),
        ("ladbrokes_uk", "Ladbrokes", "https://www.ladbrokes.com"),
        ("coral", "Coral", "https://www.coral.co.uk"),
        ("skybet", "Sky Bet", "https://www.skybet.com"),
        ("betvictor", "BetVictor", "https://www.betvictor.com"),
        ("betfred", "Betfred", "https://www.betfred.com"),
        ("boylesports", "BoyleSports", "https://www.boylesports.com"),
        ("matchbook", "Matchbook", "https://www.matchbook.com"),
        ("betfair_ex_uk", "Betfair Exchange", "https://www.betfair.com/exchange"),
        ("betfair_sb_uk", "Betfair", "https://www.betfair.com/sport"),
        ("livescorebet_eu", "LiveScore Bet", "https://www.livescorebet.com"),
        ("sport888", "888sport", "https://www.888sport.com"),
        ("marathonbet", "Marathon Bet", "https://www.marathonbet.co.uk"),
        ("virginbet", "Virgin Bet", "https://www.virginbet.com"),
        ("betuk", "Bet UK", "https://www.bet.co.uk"),
        ("betsson", "Betsson", "https://www.betsson.com"),
        ("mrgreen", "Mr Green", "https://www.mrgreen.com"),
        ("supabets", "Supa Bets", "https://www.supabets.co.uk"),
        ("spreadex", "Spreadex", "https://sports.spreadex.com"),
        ("betdaq", "Betdaq", "https://www.betdaq.com"),
        ("gentingbet", "Genting Bet", "https://www.gentingbet.co.uk"),
        ("tonybet", "Tony Bet", "https://www.tonybet.com"),
        ("nordicbet", "Nordic Bet", "https://www.nordicbet.com"),
        ("smarkets", "Smarkets", "https://www.smarkets.com"),
        ("casumo", "Casumo", "https://www.casumo.com"),
        ("grosvenor", "Grosvenor", "https://www.grosvenorcasinos.com"),
        ("leovegas", "LeoVegas", "https://www.leovegas.com"),
    ]

    # Insert bookmaker links
    for bookmaker_key, display_name, url in bookmakers:
        op.execute(
            f"INSERT INTO bookmaker_links (bookmaker_key, display_name, url, is_active) "
            f"VALUES ('{bookmaker_key}', '{display_name}', '{url}', true)"
        )


def downgrade() -> None:
    op.drop_index(op.f('ix_bookmaker_clicks_bookmaker_key'), table_name='bookmaker_clicks')
    op.drop_index(op.f('ix_bookmaker_clicks_id'), table_name='bookmaker_clicks')
    op.drop_table('bookmaker_clicks')
    op.drop_index(op.f('ix_bookmaker_links_bookmaker_key'), table_name='bookmaker_links')
    op.drop_index(op.f('ix_bookmaker_links_id'), table_name='bookmaker_links')
    op.drop_table('bookmaker_links')

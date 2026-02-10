"""void legacy bets without event_id

Revision ID: void_legacy_bets
Revises: add_token_blacklist
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'void_legacy_bets'
down_revision: Union[str, None] = 'add_token_blacklist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Void all legacy bets (no event_id, no result yet)
    op.execute("""
        UPDATE bets SET result = 'void'
        WHERE event_id IS NULL AND result IS NULL
    """)

    # Step 2: Finalize locked accas where all bets now have results
    # For each locked acca, check if all bets have results
    # If yes, determine final status based on bet outcomes
    op.execute("""
        WITH acca_results AS (
            SELECT
                a.id as acca_id,
                COUNT(b.id) as total_bets,
                COUNT(b.result) as resolved_bets,
                SUM(CASE WHEN b.result = 'won' THEN 1 ELSE 0 END) as won_count,
                SUM(CASE WHEN b.result = 'lost' THEN 1 ELSE 0 END) as lost_count,
                SUM(CASE WHEN b.result = 'void' THEN 1 ELSE 0 END) as void_count
            FROM accas a
            INNER JOIN bets b ON b.acca_id = a.id
            WHERE a.status = 'locked'
            GROUP BY a.id
        ),
        acca_final_status AS (
            SELECT
                acca_id,
                CASE
                    -- If any bet lost, acca is lost
                    WHEN lost_count > 0 THEN 'lost'
                    -- If all bets are void, acca is settled
                    WHEN void_count = total_bets THEN 'settled'
                    -- If all non-void bets won, acca is won
                    WHEN won_count = total_bets - void_count AND won_count > 0 THEN 'won'
                    -- Otherwise settled
                    ELSE 'settled'
                END as final_status
            FROM acca_results
            WHERE total_bets = resolved_bets  -- All bets have results
        )
        UPDATE accas
        SET status = acca_final_status.final_status
        FROM acca_final_status
        WHERE accas.id = acca_final_status.acca_id
    """)


def downgrade() -> None:
    # Data migration — downgrade sets voided legacy bets back to NULL
    op.execute("""
        UPDATE bets SET result = NULL
        WHERE event_id IS NULL AND result = 'void'
    """)

    # Note: We don't revert acca status changes because we can't reliably
    # determine what the previous status was (could have been 'won', 'lost', or 'settled')

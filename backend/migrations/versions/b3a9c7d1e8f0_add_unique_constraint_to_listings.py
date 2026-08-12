"""add unique constraint to listings

Revision ID: b3a9c7d1e8f0
Revises: e9232d677328
Create Date: 2026-08-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3a9c7d1e8f0'
down_revision = 'e9232d677328' # Assumes this is the previous one. If not, the user can adjust it.
branch_labels = None
depends_on = None

def upgrade() -> None:
    # We must ensure there are no duplicates before creating the unique index
    # We rely on the dedupe script being run before this migration
    op.create_unique_constraint('uq_listing_user_marketplace', 'listings', ['user_id', 'marketplace_listing_id'])

def downgrade() -> None:
    op.drop_constraint('uq_listing_user_marketplace', 'listings', type_='unique')

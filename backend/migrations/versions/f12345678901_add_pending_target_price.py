"""add pending_target_price

Revision ID: f12345678901
Revises: e9232d677328
Create Date: 2026-08-12 17:39:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f12345678901'
down_revision = 'e9232d677328'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('automation_rules', sa.Column('pending_target_price', sa.Numeric(precision=10, scale=2), nullable=True))

def downgrade() -> None:
    op.drop_column('automation_rules', 'pending_target_price')

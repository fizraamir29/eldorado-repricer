"""Add status to listings

Revision ID: e9232d677328
Revises: e9232d677327
Create Date: 2026-08-12 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9232d677328'
down_revision: Union[str, None] = 'e9232d677327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('listings', sa.Column('status', sa.String(length=50), server_default='active', nullable=False))


def downgrade() -> None:
    op.drop_column('listings', 'status')

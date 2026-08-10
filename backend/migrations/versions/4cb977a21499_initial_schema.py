"""initial schema

Revision ID: 4cb977a21499
Revises:
Create Date: 2026-07-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "4cb977a21499"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("marketplace_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marketplace_listing_id", sa.String(128), nullable=False),
        sa.Column("game_name", sa.String(128), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("current_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_listings_user_id", "listings", ["user_id"])

    op.create_table(
        "automation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("undercut_step", sa.Numeric(10, 2), nullable=False, server_default="0.01"),
        sa.Column("check_interval_minutes", sa.Integer(), nullable=False, server_default="5"),
    )

    op.create_table(
        "price_history",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("lowest_competitor_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_price_history_listing_id", "price_history", ["listing_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=True),
        sa.Column("level", sa.String(20), nullable=False, server_default="info"),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("price_history")
    op.drop_table("automation_rules")
    op.drop_index("ix_listings_user_id", table_name="listings")
    op.drop_table("listings")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

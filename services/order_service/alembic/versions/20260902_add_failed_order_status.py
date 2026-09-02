"""Add failed order status.

Revision ID: 20260902_failed_order_status
Revises:
"""
from alembic import op

revision = "20260902_failed_order_status"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'FAILED'")


def downgrade() -> None:
    pass
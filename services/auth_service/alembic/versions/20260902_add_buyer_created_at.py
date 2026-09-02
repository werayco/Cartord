"""Add buyer registration timestamp.

Revision ID: 20260902_buyer_created_at
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20260902_buyer_created_at"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "buyer",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("buyer", "created_at")

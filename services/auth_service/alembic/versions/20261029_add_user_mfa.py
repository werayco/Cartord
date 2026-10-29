"""Add persistent MFA credentials.

Revision ID: 20261029_user_mfa
Revises: 20260902_buyer_created_at
"""

import sqlalchemy as sa
from alembic import op

revision = "20261029_user_mfa"
down_revision = "20260902_buyer_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mfa_credential",
        sa.Column("account_type", sa.String(length=16), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("encrypted_secret", sa.String(), nullable=False),
        sa.Column("last_used_counter", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("account_type", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("mfa_credential")

"""add seller_id to inventory

Revision ID: 15133768a65d
Revises: ba00c4993878
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15133768a65d'
down_revision: Union[str, None] = 'ba00c4993878'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventory', sa.Column('seller_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_inventory_seller_id'), 'inventory', ['seller_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_seller_id'), table_name='inventory')
    op.drop_column('inventory', 'seller_id')
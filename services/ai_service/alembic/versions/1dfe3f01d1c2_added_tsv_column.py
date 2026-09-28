"""added tsv column

Revision ID: 1dfe3f01d1c2
Revises: 29eb77c7fe13
Create Date: 2026-09-20 05:43:40.400925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1dfe3f01d1c2'
down_revision: Union[str, None] = '29eb77c7fe13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'documents',
        sa.Column(
            'content_tsv',
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=False,
        ),
    )
    op.create_index(
        'documents_content_tsv_idx',
        'documents',
        ['content_tsv'],
        unique=False,
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index(
        'documents_content_tsv_idx',
        table_name='documents',
        postgresql_using='gin',
    )
    op.drop_column('documents', 'content_tsv')
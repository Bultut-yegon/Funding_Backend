"""fix bookmarks missing columns

Revision ID: 08637e63f63a
Revises: 0045044e6f27
Create Date: 2026-07-29 23:49:42.757393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08637e63f63a'
down_revision: Union[str, Sequence[str], None] = '0045044e6f27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bookmarks', sa.Column('status', sa.String(), server_default='Saved', nullable=True))
    op.add_column('bookmarks', sa.Column('notes', sa.String(), nullable=True))
    op.add_column('bookmarks', sa.Column('applied_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('bookmarks', 'applied_date')
    op.drop_column('bookmarks', 'notes')
    op.drop_column('bookmarks', 'status')

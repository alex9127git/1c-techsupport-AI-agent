"""add source_file to knowledge_documents

Revision ID: 5f0f6b744abf
Revises: 9a307e0cf311
Create Date: 2026-09-14 06:06:54.673780
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5f0f6b744abf'
down_revision: Union[str, None] = '9a307e0cf311'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_documents', sa.Column('source_file', sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_documents', 'source_file')

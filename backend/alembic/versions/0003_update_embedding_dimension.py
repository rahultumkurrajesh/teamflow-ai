"""Update embedding dimension to 384 for all-MiniLM-L6-v2.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-31 00:00:00.000000

This migration updates the embedding column dimension from 1536 (OpenAI text-embedding-3-small)
to 384 (sentence-transformers all-MiniLM-L6-v2) as the new default.
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For PostgreSQL, we can alter the column type directly
    # Drop the old embedding column and add a new one with updated dimension
    op.drop_column('document_chunks', 'embedding')
    op.add_column(
        'document_chunks',
        sa.Column('embedding', Vector(dim=384), nullable=True)
    )


def downgrade() -> None:
    # Revert to 1536-dimensional vectors
    op.drop_column('document_chunks', 'embedding')
    op.add_column(
        'document_chunks',
        sa.Column('embedding', Vector(dim=1536), nullable=True)
    )

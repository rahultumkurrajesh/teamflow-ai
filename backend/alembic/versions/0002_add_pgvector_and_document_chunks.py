"""Add pgvector extension and document_chunks table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-30 00:00:00.000000

This migration:
1. Creates the pgvector extension (for vector similarity search)
2. Creates the document_chunks table with embedding vectors
3. Adds HNSW index on embedding for efficient similarity search
4. Adds index on document_id for fast lookups
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(dim=1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index(
        'idx_document_chunks_embedding',
        'document_chunks',
        ['embedding'],
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 200}
    )


def downgrade() -> None:
    # Drop table (cascade will handle indexes)
    op.drop_table('document_chunks')

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS vector')

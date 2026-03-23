"""Add chunk_metadata to document_chunks

Revision ID: 041_add_document_chunk_metadata
Revises: 040_add_workflow_connection_label_style
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '041_add_document_chunk_metadata'
down_revision = '040_add_workflow_connection_label_style'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    column_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'document_chunks'
          AND column_name = 'chunk_metadata'
        LIMIT 1
    """)).fetchone()

    if not column_exists:
        op.add_column(
            'document_chunks',
            sa.Column('chunk_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
        )


def downgrade() -> None:
    op.drop_column('document_chunks', 'chunk_metadata')

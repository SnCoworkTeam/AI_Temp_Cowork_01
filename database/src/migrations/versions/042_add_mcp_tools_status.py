"""Add status to mcp_tools

Revision ID: 042_add_mcp_tools_status
Revises: 041_add_document_chunk_metadata
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '042_add_mcp_tools_status'
down_revision = '041_add_document_chunk_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Create enum type if not exists
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE toolstatus AS ENUM ('active', 'inactive', 'deprecated');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    column_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'mcp_tools'
          AND column_name = 'status'
        LIMIT 1
    """)).fetchone()

    if not column_exists:
        op.add_column(
            'mcp_tools',
            sa.Column(
                'status',
                postgresql.ENUM('active', 'inactive', 'deprecated', name='toolstatus', create_type=False),
                nullable=False,
                server_default='active'
            )
        )

        # Backfill from legacy is_active if present
        is_active_exists = conn.execute(sa.text("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'mcp_tools'
              AND column_name = 'is_active'
            LIMIT 1
        """)).fetchone()

        if is_active_exists:
            conn.execute(sa.text("""
                UPDATE mcp_tools
                SET status = CASE
                    WHEN is_active = false THEN 'inactive'::toolstatus
                    ELSE 'active'::toolstatus
                END
                WHERE status IS NULL
            """))

        # Remove server default to match model behavior
        op.alter_column('mcp_tools', 'status', server_default=None)


def downgrade() -> None:
    op.drop_column('mcp_tools', 'status')
    op.execute("DROP TYPE IF EXISTS toolstatus")

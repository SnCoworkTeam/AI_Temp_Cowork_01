"""Make mcp_tools.avg_execution_time nullable

Revision ID: 044_make_mcp_tools_avg_execution_time_nullable
Revises: 043_fix_toolstatus_enum_case
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '044_make_mcp_tools_avg_execution_time_nullable'
down_revision = '043_fix_toolstatus_enum_case'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    column_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'mcp_tools'
          AND column_name = 'avg_execution_time'
        LIMIT 1
    """)).fetchone()
    if column_exists:
        op.alter_column('mcp_tools', 'avg_execution_time', nullable=True)


def downgrade() -> None:
    # Revert to NOT NULL (may fail if nulls exist)
    op.alter_column('mcp_tools', 'avg_execution_time', nullable=False)

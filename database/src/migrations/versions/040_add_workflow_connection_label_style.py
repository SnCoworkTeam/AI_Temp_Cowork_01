"""Add label/style to workflow_connections

Revision ID: 040_add_workflow_connection_label_style
Revises: 999999
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '040_add_workflow_connection_label_style'
down_revision = '999999'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    def column_exists(column_name: str) -> bool:
        return conn.execute(sa.text("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'workflow_connections'
              AND column_name = :column_name
            LIMIT 1
        """), {"column_name": column_name}).fetchone() is not None

    if not column_exists('label'):
        op.add_column('workflow_connections', sa.Column('label', sa.String(200), nullable=True))

    if not column_exists('style'):
        op.add_column('workflow_connections', sa.Column('style', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # 注意：按相反顺序删除列
    op.drop_column('workflow_connections', 'style')
    op.drop_column('workflow_connections', 'label')

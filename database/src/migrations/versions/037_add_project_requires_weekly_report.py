"""添加项目是否编写周报字段

Revision ID: 037_add_project_requires_weekly_report
Revises: 036_add_project_milestone_dates
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '037_add_project_requires_weekly_report'
down_revision = '036_add_project_milestone_dates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pm_projects')]

    # 添加是否编写周报字段
    if 'requires_weekly_report' not in columns:
        op.add_column('pm_projects', sa.Column('requires_weekly_report', sa.Boolean(), nullable=False, server_default='false', comment='是否编写周报'))


def downgrade() -> None:
    op.drop_column('pm_projects', 'requires_weekly_report')


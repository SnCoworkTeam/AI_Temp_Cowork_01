"""添加月报表缺失字段

Revision ID: 034_add_monthly_report_fields
Revises: 033_add_project_reporter_id
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '034_add_monthly_report_fields'
down_revision = '033_add_project_reporter_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pm_monthly_reports')]

    # 添加progress_percent字段
    if 'progress_percent' not in columns:
        op.add_column('pm_monthly_reports', sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0.0', comment='月度进度百分比'))

    # 添加key_milestones字段
    if 'key_milestones' not in columns:
        op.add_column('pm_monthly_reports', sa.Column('key_milestones', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]', comment='关键里程碑完成情况'))

    # 添加risk_summary字段
    if 'risk_summary' not in columns:
        op.add_column('pm_monthly_reports', sa.Column('risk_summary', sa.Text(), nullable=True, comment='风险汇总'))

    # 添加resource_summary字段
    if 'resource_summary' not in columns:
        op.add_column('pm_monthly_reports', sa.Column('resource_summary', sa.Text(), nullable=True, comment='资源使用情况'))


def downgrade() -> None:
    op.drop_column('pm_monthly_reports', 'resource_summary')
    op.drop_column('pm_monthly_reports', 'risk_summary')
    op.drop_column('pm_monthly_reports', 'key_milestones')
    op.drop_column('pm_monthly_reports', 'progress_percent')



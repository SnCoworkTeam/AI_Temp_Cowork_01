"""添加项目重要里程碑日期字段

Revision ID: 036_add_project_milestone_dates
Revises: 035_add_phase_milestone_category_id
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '036_add_project_milestone_dates'
down_revision = '035_add_phase_milestone_category_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pm_projects')]

    # 添加重要里程碑日期字段
    if 'milestone_implementation_start' not in columns:
        op.add_column('pm_projects', sa.Column('milestone_implementation_start', sa.Date(), nullable=True, comment='实施启动日期'))
    if 'milestone_solution_confirmation' not in columns:
        op.add_column('pm_projects', sa.Column('milestone_solution_confirmation', sa.Date(), nullable=True, comment='方案确认日期'))
    if 'milestone_delivery_online' not in columns:
        op.add_column('pm_projects', sa.Column('milestone_delivery_online', sa.Date(), nullable=True, comment='交付上线日期'))
    if 'milestone_project_acceptance' not in columns:
        op.add_column('pm_projects', sa.Column('milestone_project_acceptance', sa.Date(), nullable=True, comment='项目验收日期'))


def downgrade() -> None:
    op.drop_column('pm_projects', 'milestone_project_acceptance')
    op.drop_column('pm_projects', 'milestone_delivery_online')
    op.drop_column('pm_projects', 'milestone_solution_confirmation')
    op.drop_column('pm_projects', 'milestone_implementation_start')



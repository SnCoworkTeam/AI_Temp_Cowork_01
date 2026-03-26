"""添加项目阶段和里程碑的category_id字段

Revision ID: 035_add_phase_milestone_category_id
Revises: 034_add_monthly_report_fields
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '035_add_phase_milestone_category_id'
down_revision = '034_add_monthly_report_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 添加项目阶段的category_id字段
    phases_columns = [col['name'] for col in inspector.get_columns('pm_project_phases')]
    if 'category_id' not in phases_columns:
        op.add_column('pm_project_phases', sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True, comment='基础数据分类ID（项目阶段）'))

    phases_foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('pm_project_phases')]
    if 'fk_pm_project_phases_category_id' not in phases_foreign_keys:
        op.create_foreign_key('fk_pm_project_phases_category_id', 'pm_project_phases', 'pm_basic_data_categories', ['category_id'], ['id'])

    phases_indexes = [idx['name'] for idx in inspector.get_indexes('pm_project_phases')]
    if 'ix_pm_project_phases_category_id' not in phases_indexes:
        op.create_index(op.f('ix_pm_project_phases_category_id'), 'pm_project_phases', ['category_id'], unique=False)

    # 添加里程碑的category_id字段
    milestones_columns = [col['name'] for col in inspector.get_columns('pm_milestones')]
    if 'category_id' not in milestones_columns:
        op.add_column('pm_milestones', sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True, comment='基础数据分类ID（里程碑）'))

    milestones_foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('pm_milestones')]
    if 'fk_pm_milestones_category_id' not in milestones_foreign_keys:
        op.create_foreign_key('fk_pm_milestones_category_id', 'pm_milestones', 'pm_basic_data_categories', ['category_id'], ['id'])

    milestones_indexes = [idx['name'] for idx in inspector.get_indexes('pm_milestones')]
    if 'ix_pm_milestones_category_id' not in milestones_indexes:
        op.create_index(op.f('ix_pm_milestones_category_id'), 'pm_milestones', ['category_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_pm_milestones_category_id'), table_name='pm_milestones')
    op.drop_constraint('fk_pm_milestones_category_id', 'pm_milestones', type_='foreignkey')
    op.drop_column('pm_milestones', 'category_id')

    op.drop_index(op.f('ix_pm_project_phases_category_id'), table_name='pm_project_phases')
    op.drop_constraint('fk_pm_project_phases_category_id', 'pm_project_phases', type_='foreignkey')
    op.drop_column('pm_project_phases', 'category_id')


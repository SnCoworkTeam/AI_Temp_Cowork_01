"""add project management tables

Revision ID: 0021
Revises: 0020
Create Date: 2025-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '020'  # 修复：使用'020'而不是'0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建项目表
    op.create_table(
        'pm_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='项目ID'),
        sa.Column('project_code', sa.String(length=50), nullable=False, comment='项目编码'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='项目名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='项目描述'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planning', comment='项目状态'),
        sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium', comment='优先级'),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目经理ID'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('actual_start_date', sa.Date(), nullable=True, comment='实际开始日期'),
        sa.Column('actual_end_date', sa.Date(), nullable=True, comment='实际结束日期'),
        sa.Column('budget', sa.Float(), nullable=True, comment='预算'),
        sa.Column('actual_cost', sa.Float(), nullable=True, comment='实际成本'),
        sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0', comment='进度百分比'),
        sa.Column('health_score', sa.Float(), nullable=True, server_default='0', comment='健康度评分'),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联工作流ID'),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联知识库ID'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_code'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
    )
    op.create_index('ix_pm_projects_project_code', 'pm_projects', ['project_code'])
    op.create_index('ix_pm_projects_status', 'pm_projects', ['status'])
    op.create_index('ix_pm_projects_manager_id', 'pm_projects', ['manager_id'])

    # 创建项目阶段表
    op.create_table(
        'pm_project_phases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='阶段ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='阶段名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='阶段描述'),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0', comment='阶段顺序'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='结束日期'),
        sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0', comment='进度百分比'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pm_project_phases_project_id', 'pm_project_phases', ['project_id'])

    # 创建里程碑表
    op.create_table(
        'pm_milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='里程碑ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True, comment='阶段ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='里程碑名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='里程碑描述'),
        sa.Column('target_date', sa.Date(), nullable=True, comment='目标日期'),
        sa.Column('actual_date', sa.Date(), nullable=True, comment='实际完成日期'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned', comment='里程碑状态'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['pm_project_phases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pm_milestones_project_id', 'pm_milestones', ['project_id'])
    op.create_index('ix_pm_milestones_phase_id', 'pm_milestones', ['phase_id'])

    # 创建任务表
    op.create_table(
        'pm_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='任务ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True, comment='阶段ID'),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), nullable=True, comment='里程碑ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='任务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='todo', comment='任务状态'),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True, comment='负责人ID'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='开始日期'),
        sa.Column('due_date', sa.Date(), nullable=True, comment='截止日期'),
        sa.Column('completed_date', sa.Date(), nullable=True, comment='完成日期'),
        sa.Column('estimated_hours', sa.Float(), nullable=True, comment='预估工时'),
        sa.Column('actual_hours', sa.Float(), nullable=True, comment='实际工时'),
        sa.Column('progress_percent', sa.Float(), nullable=True, server_default='0', comment='进度百分比'),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='任务依赖关系'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['pm_project_phases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['milestone_id'], ['pm_milestones.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
    )
    op.create_index('ix_pm_tasks_project_id', 'pm_tasks', ['project_id'])
    op.create_index('ix_pm_tasks_phase_id', 'pm_tasks', ['phase_id'])
    op.create_index('ix_pm_tasks_milestone_id', 'pm_tasks', ['milestone_id'])
    op.create_index('ix_pm_tasks_assignee_id', 'pm_tasks', ['assignee_id'])
    op.create_index('ix_pm_tasks_status', 'pm_tasks', ['status'])

    # 创建周报表
    op.create_table(
        'pm_weekly_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='周报ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('week_number', sa.Integer(), nullable=True, comment='周数'),
        sa.Column('report_date', sa.Date(), nullable=False, comment='报告日期'),
        sa.Column('content_plan', sa.Text(), nullable=True, comment='计划内容'),
        sa.Column('content_achievement', sa.Text(), nullable=True, comment='成果内容'),
        sa.Column('key_tasks_completed', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='关键任务完成情况'),
        sa.Column('issues_risks', sa.Text(), nullable=True, comment='问题与风险'),
        sa.Column('next_week_plan', sa.Text(), nullable=True, comment='下周计划'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pm_weekly_reports_project_id', 'pm_weekly_reports', ['project_id'])
    op.create_index('ix_pm_weekly_reports_report_date', 'pm_weekly_reports', ['report_date'])

    # 创建风险表
    op.create_table(
        'pm_risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()'), comment='风险ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='风险名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='风险描述'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='medium', comment='风险等级'),
        sa.Column('probability', sa.Float(), nullable=True, comment='发生概率'),
        sa.Column('impact', sa.String(length=20), nullable=True, comment='影响程度'),
        sa.Column('mitigation_plan', sa.Text(), nullable=True, comment='应对措施'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='open', comment='风险状态'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pm_risks_project_id', 'pm_risks', ['project_id'])


def downgrade() -> None:
    # 删除表（注意顺序，先删除依赖表）
    op.drop_table('pm_risks')
    op.drop_table('pm_weekly_reports')
    op.drop_table('pm_tasks')
    op.drop_table('pm_milestones')
    op.drop_table('pm_project_phases')
    op.drop_table('pm_projects')

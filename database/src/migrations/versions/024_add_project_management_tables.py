"""
添加项目管理表

Revision ID: 024
Revises: 020
Create Date: 2025-12-06

功能: 创建项目管理相关表（pm_projects, pm_project_phases, pm_milestones, pm_tasks, pm_weekly_reports, pm_risks）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '024'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    """创建项目管理相关表"""
    conn = op.get_bind()
    table_exists = conn.execute(sa.text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'pm_projects'
        LIMIT 1
    """)).fetchone()

    if table_exists:
        print("⚠️  pm_projects 已存在，跳过 024 迁移")
        return

    print("=" * 50)
    print("创建项目管理表")
    print("=" * 50)
    
    # 创建 pm_projects 表
    print("创建 pm_projects 表...")
    op.create_table(
        'pm_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('project_code', sa.String(length=50), nullable=False, comment='项目编码'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='项目名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='项目描述'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planning', comment='项目状态'),
        sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium', comment='优先级'),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目经理ID'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('actual_start_date', sa.Date(), nullable=True, comment='实际开始日期'),
        sa.Column('actual_end_date', sa.Date(), nullable=True, comment='实际结束日期'),
        sa.Column('budget', sa.Float(), nullable=True, comment='预算'),
        sa.Column('actual_cost', sa.Float(), nullable=True, comment='实际成本'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='进度百分比'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='0.0', comment='健康度评分'),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联工作流ID'),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联知识库ID'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], name='fk_pm_projects_manager_id'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], name='fk_pm_projects_workflow_id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], name='fk_pm_projects_knowledge_base_id'),
        comment='项目表'
    )
    op.create_index('ix_pm_projects_project_code', 'pm_projects', ['project_code'], unique=True)
    op.create_index('ix_pm_projects_status', 'pm_projects', ['status'], unique=False)
    op.create_index('ix_pm_projects_manager_id', 'pm_projects', ['manager_id'], unique=False)
    print("✅ pm_projects 表已创建")
    
    # 创建 pm_project_phases 表
    print("创建 pm_project_phases 表...")
    op.create_table(
        'pm_project_phases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='阶段ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='阶段名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='阶段描述'),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0', comment='阶段顺序'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='结束日期'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='进度百分比'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_pm_project_phases_project_id', ondelete='CASCADE'),
        comment='项目阶段表'
    )
    op.create_index('ix_pm_project_phases_project_id', 'pm_project_phases', ['project_id'], unique=False)
    print("✅ pm_project_phases 表已创建")
    
    # 创建 pm_milestones 表
    print("创建 pm_milestones 表...")
    op.create_table(
        'pm_milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='里程碑ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True, comment='阶段ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='里程碑名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='里程碑描述'),
        sa.Column('target_date', sa.Date(), nullable=True, comment='目标日期'),
        sa.Column('actual_date', sa.Date(), nullable=True, comment='实际完成日期'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planned', comment='里程碑状态'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_pm_milestones_project_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['pm_project_phases.id'], name='fk_pm_milestones_phase_id', ondelete='CASCADE'),
        comment='里程碑表'
    )
    op.create_index('ix_pm_milestones_project_id', 'pm_milestones', ['project_id'], unique=False)
    op.create_index('ix_pm_milestones_phase_id', 'pm_milestones', ['phase_id'], unique=False)
    print("✅ pm_milestones 表已创建")
    
    # 创建 pm_tasks 表
    print("创建 pm_tasks 表...")
    op.create_table(
        'pm_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='任务ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True, comment='阶段ID'),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), nullable=True, comment='里程碑ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='任务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='todo', comment='任务状态'),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True, comment='负责人ID'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='开始日期'),
        sa.Column('due_date', sa.Date(), nullable=True, comment='截止日期'),
        sa.Column('completed_date', sa.Date(), nullable=True, comment='完成日期'),
        sa.Column('estimated_hours', sa.Float(), nullable=True, comment='预估工时'),
        sa.Column('actual_hours', sa.Float(), nullable=True, comment='实际工时'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='进度百分比'),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]', comment='任务依赖关系'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_pm_tasks_project_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['pm_project_phases.id'], name='fk_pm_tasks_phase_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['milestone_id'], ['pm_milestones.id'], name='fk_pm_tasks_milestone_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], name='fk_pm_tasks_assignee_id'),
        comment='任务表'
    )
    op.create_index('ix_pm_tasks_project_id', 'pm_tasks', ['project_id'], unique=False)
    op.create_index('ix_pm_tasks_status', 'pm_tasks', ['status'], unique=False)
    op.create_index('ix_pm_tasks_assignee_id', 'pm_tasks', ['assignee_id'], unique=False)
    print("✅ pm_tasks 表已创建")
    
    # 创建 pm_weekly_reports 表
    print("创建 pm_weekly_reports 表...")
    op.create_table(
        'pm_weekly_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='周报ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('week_number', sa.Integer(), nullable=True, comment='周数'),
        sa.Column('report_date', sa.Date(), nullable=False, comment='报告日期'),
        sa.Column('content_plan', sa.Text(), nullable=True, comment='计划内容'),
        sa.Column('content_achievement', sa.Text(), nullable=True, comment='成果内容'),
        sa.Column('key_tasks_completed', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]', comment='关键任务完成情况'),
        sa.Column('issues_risks', sa.Text(), nullable=True, comment='问题与风险'),
        sa.Column('next_week_plan', sa.Text(), nullable=True, comment='下周计划'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_pm_weekly_reports_project_id', ondelete='CASCADE'),
        comment='周报表'
    )
    op.create_index('ix_pm_weekly_reports_project_id', 'pm_weekly_reports', ['project_id'], unique=False)
    op.create_index('ix_pm_weekly_reports_report_date', 'pm_weekly_reports', ['report_date'], unique=False)
    print("✅ pm_weekly_reports 表已创建")
    
    # 创建 pm_risks 表
    print("创建 pm_risks 表...")
    op.create_table(
        'pm_risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='风险ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='风险名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='风险描述'),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='medium', comment='风险等级'),
        sa.Column('probability', sa.Float(), nullable=True, comment='发生概率'),
        sa.Column('impact', sa.String(length=20), nullable=True, comment='影响程度'),
        sa.Column('mitigation_plan', sa.Text(), nullable=True, comment='应对措施'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open', comment='风险状态'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_pm_risks_project_id', ondelete='CASCADE'),
        comment='风险表'
    )
    op.create_index('ix_pm_risks_project_id', 'pm_risks', ['project_id'], unique=False)
    print("✅ pm_risks 表已创建")
    
    print("=" * 50)
    print("项目管理表创建完成")
    print("=" * 50)


def downgrade():
    """删除项目管理相关表"""
    print("删除项目管理表...")
    
    op.drop_index('ix_pm_risks_project_id', table_name='pm_risks')
    op.drop_table('pm_risks')
    print("✅ pm_risks 表已删除")
    
    op.drop_index('ix_pm_weekly_reports_report_date', table_name='pm_weekly_reports')
    op.drop_index('ix_pm_weekly_reports_project_id', table_name='pm_weekly_reports')
    op.drop_table('pm_weekly_reports')
    print("✅ pm_weekly_reports 表已删除")
    
    op.drop_index('ix_pm_tasks_assignee_id', table_name='pm_tasks')
    op.drop_index('ix_pm_tasks_status', table_name='pm_tasks')
    op.drop_index('ix_pm_tasks_project_id', table_name='pm_tasks')
    op.drop_table('pm_tasks')
    print("✅ pm_tasks 表已删除")
    
    op.drop_index('ix_pm_milestones_phase_id', table_name='pm_milestones')
    op.drop_index('ix_pm_milestones_project_id', table_name='pm_milestones')
    op.drop_table('pm_milestones')
    print("✅ pm_milestones 表已删除")
    
    op.drop_index('ix_pm_project_phases_project_id', table_name='pm_project_phases')
    op.drop_table('pm_project_phases')
    print("✅ pm_project_phases 表已删除")
    
    op.drop_index('ix_pm_projects_manager_id', table_name='pm_projects')
    op.drop_index('ix_pm_projects_status', table_name='pm_projects')
    op.drop_index('ix_pm_projects_project_code', table_name='pm_projects')
    op.drop_table('pm_projects')
    print("✅ pm_projects 表已删除")
    
    print("项目管理表删除完成")

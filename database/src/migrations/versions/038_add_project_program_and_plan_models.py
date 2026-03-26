"""Add project program and plan models

Revision ID: 038_add_project_program_and_plan_models
Revises: 037_add_project_requires_weekly_report
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '038_add_project_program_and_plan_models'
down_revision = '037_add_project_requires_weekly_report'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. 创建项目群表
    if 'pm_programs' in existing_tables:
        print("表 pm_programs 已存在，跳过创建")
    else:
        op.create_table(
        'pm_programs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='项目群ID'),
        sa.Column('program_code', sa.String(50), nullable=False, unique=True, index=True, comment='项目群编码'),
        sa.Column('name', sa.String(200), nullable=False, comment='项目群名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='项目群描述'),
        sa.Column('status', sa.String(20), nullable=False, server_default='planning', comment='项目群状态'),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目群经理ID'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('actual_start_date', sa.Date(), nullable=True, comment='实际开始日期'),
        sa.Column('actual_end_date', sa.Date(), nullable=True, comment='实际结束日期'),
        sa.Column('budget', sa.Float(), nullable=True, comment='项目群预算'),
        sa.Column('actual_cost', sa.Float(), nullable=True, comment='实际成本'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='整体进度百分比'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='0.0', comment='健康度评分'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True, comment='项目群分类（从基础数据获取）'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], name='fk_program_manager'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], name='fk_program_category'),
        sa.Index('idx_program_code', 'program_code'),
        sa.Index('idx_program_status', 'status'),
        sa.Index('idx_program_manager', 'manager_id'),
        comment='项目群表'
        )

    # 2. 在项目表中添加项目群关联
    projects_columns = [col['name'] for col in inspector.get_columns('pm_projects')]
    if 'program_id' not in projects_columns:
        op.add_column('pm_projects', sa.Column('program_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属项目群ID'))

    projects_indexes = [idx['name'] for idx in inspector.get_indexes('pm_projects')]
    if 'idx_project_program' not in projects_indexes:
        op.create_index('idx_project_program', 'pm_projects', ['program_id'])

    projects_foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('pm_projects')]
    if 'fk_project_program' not in projects_foreign_keys:
        op.create_foreign_key('fk_project_program', 'pm_projects', 'pm_programs', ['program_id'], ['id'], ondelete='SET NULL')

    # 3. 创建项目群计划表
    if 'pm_program_plans' in existing_tables:
        print("表 pm_program_plans 已存在，跳过创建")
    else:
        op.create_table(
        'pm_program_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='计划ID'),
        sa.Column('program_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='项目群ID'),
        sa.Column('name', sa.String(200), nullable=False, comment='计划名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='计划描述'),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0', comment='计划版本'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['program_id'], ['pm_programs.id'], name='fk_program_plan_program', ondelete='CASCADE'),
        sa.Index('idx_program_plan_program', 'program_id'),
        comment='项目群计划表'
        )

    # 4. 创建项目群计划任务表
    if 'pm_program_plan_tasks' in existing_tables:
        print("表 pm_program_plan_tasks 已存在，跳过创建")
    else:
        op.create_table(
        'pm_program_plan_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='任务ID'),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='计划ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='关联的项目ID'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False, comment='任务类型（从基础数据获取）'),
        sa.Column('name', sa.String(200), nullable=False, comment='任务名称（从基础数据同步）'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('duration_days', sa.Integer(), nullable=True, comment='持续时间（天）'),
        sa.Column('dependencies', postgresql.JSONB(), nullable=True, server_default='[]', comment='依赖任务ID列表'),
        sa.Column('predecessors', postgresql.JSONB(), nullable=True, server_default='[]', comment='前置任务ID列表'),
        sa.Column('assigned_resources', postgresql.JSONB(), nullable=True, server_default='[]', comment='分配的资源ID列表'),
        sa.Column('estimated_effort', sa.Float(), nullable=True, comment='预估工作量（人天）'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='进度百分比'),
        sa.Column('status', sa.String(20), nullable=False, server_default='planned', comment='任务状态'),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false', comment='是否关键任务'),
        sa.Column('float_days', sa.Float(), nullable=True, comment='浮动时间（天）'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['plan_id'], ['pm_program_plans.id'], name='fk_program_plan_task_plan', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_program_plan_task_project', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], name='fk_program_plan_task_category'),
        sa.Index('idx_program_plan_task_plan', 'plan_id'),
        sa.Index('idx_program_plan_task_project', 'project_id'),
        sa.Index('idx_program_plan_task_category', 'category_id'),
        comment='项目群计划任务表'
        )

    # 5. 创建项目模板表（先于项目计划表，避免外键依赖错误）
    if 'pm_project_templates' in existing_tables:
        print("表 pm_project_templates 已存在，跳过创建")
    else:
        op.create_table(
        'pm_project_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='模板ID'),
        sa.Column('template_code', sa.String(50), nullable=False, unique=True, index=True, comment='模板编码'),
        sa.Column('name', sa.String(200), nullable=False, comment='模板名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True, comment='模板分类（从基础数据获取）'),
        sa.Column('template_structure', postgresql.JSONB(), nullable=True, server_default='{}', comment='模板结构'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='使用次数'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], name='fk_project_template_category', ondelete='SET NULL'),
        sa.Index('idx_project_template_code', 'template_code'),
        sa.Index('idx_project_template_active', 'is_active'),
        comment='项目模板表'
        )
        existing_tables.append('pm_project_templates')

    # 6. 创建项目计划表
    if 'pm_project_plans' in existing_tables:
        print("表 pm_project_plans 已存在，跳过创建")
    else:
        op.create_table(
        'pm_project_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='计划ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='项目ID'),
        sa.Column('name', sa.String(200), nullable=False, comment='计划名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='计划描述'),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0', comment='计划版本'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('is_baseline', sa.Boolean(), nullable=False, server_default='false', comment='是否基线计划'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('baseline_start_date', sa.Date(), nullable=True, comment='基线开始日期'),
        sa.Column('baseline_end_date', sa.Date(), nullable=True, comment='基线结束日期'),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True, comment='基于的模板ID'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], name='fk_project_plan_project', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['pm_project_templates.id'], name='fk_project_plan_template', ondelete='SET NULL'),
        sa.Index('idx_project_plan_project', 'project_id'),
        sa.Index('idx_project_plan_active', 'project_id', 'is_active'),
        comment='项目计划表'
        )

    # 6. 创建项目计划任务表
    if 'pm_project_plan_tasks' in existing_tables:
        print("表 pm_project_plan_tasks 已存在，跳过创建")
    else:
        op.create_table(
        'pm_project_plan_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='任务ID'),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='计划ID'),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='阶段ID'),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='里程碑ID'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False, comment='任务类型（从基础数据获取）'),
        sa.Column('name', sa.String(200), nullable=False, comment='任务名称（从基础数据同步）'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('start_date', sa.Date(), nullable=True, comment='计划开始日期'),
        sa.Column('end_date', sa.Date(), nullable=True, comment='计划结束日期'),
        sa.Column('duration_days', sa.Integer(), nullable=True, comment='持续时间（天）'),
        sa.Column('actual_start_date', sa.Date(), nullable=True, comment='实际开始日期'),
        sa.Column('actual_end_date', sa.Date(), nullable=True, comment='实际结束日期'),
        sa.Column('dependencies', postgresql.JSONB(), nullable=True, server_default='[]', comment='依赖关系列表'),
        sa.Column('predecessors', postgresql.JSONB(), nullable=True, server_default='[]', comment='前置任务ID列表'),
        sa.Column('successors', postgresql.JSONB(), nullable=True, server_default='[]', comment='后续任务ID列表'),
        sa.Column('assignee_id', postgresql.UUID(as_uuid=True), nullable=True, comment='负责人ID'),
        sa.Column('assigned_resources', postgresql.JSONB(), nullable=True, server_default='[]', comment='分配的资源ID列表'),
        sa.Column('estimated_hours', sa.Float(), nullable=True, comment='预估工时（小时）'),
        sa.Column('actual_hours', sa.Float(), nullable=True, comment='实际工时（小时）'),
        sa.Column('estimated_effort', sa.Float(), nullable=True, comment='预估工作量（人天）'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0', comment='进度百分比'),
        sa.Column('status', sa.String(20), nullable=False, server_default='planned', comment='任务状态'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium', comment='优先级'),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false', comment='是否关键任务'),
        sa.Column('early_start', sa.Date(), nullable=True, comment='最早开始时间'),
        sa.Column('early_finish', sa.Date(), nullable=True, comment='最早结束时间'),
        sa.Column('late_start', sa.Date(), nullable=True, comment='最晚开始时间'),
        sa.Column('late_finish', sa.Date(), nullable=True, comment='最晚结束时间'),
        sa.Column('total_float', sa.Float(), nullable=True, comment='总浮动时间（天）'),
        sa.Column('free_float', sa.Float(), nullable=True, comment='自由浮动时间（天）'),
        sa.Column('actual_task_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联的实际任务ID'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['plan_id'], ['pm_project_plans.id'], name='fk_project_plan_task_plan', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['phase_id'], ['pm_project_phases.id'], name='fk_project_plan_task_phase', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['milestone_id'], ['pm_milestones.id'], name='fk_project_plan_task_milestone', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], name='fk_project_plan_task_category'),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], name='fk_project_plan_task_assignee', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['actual_task_id'], ['pm_tasks.id'], name='fk_project_plan_task_actual', ondelete='SET NULL'),
        sa.Index('idx_project_plan_task_plan', 'plan_id'),
        sa.Index('idx_project_plan_task_phase', 'phase_id'),
        sa.Index('idx_project_plan_task_milestone', 'milestone_id'),
        sa.Index('idx_project_plan_task_category', 'category_id'),
        sa.Index('idx_project_plan_task_assignee', 'assignee_id'),
        sa.Index('idx_project_plan_task_critical', 'is_critical'),
        comment='项目计划任务表'
        )

    # 7. 创建项目模板表
    if 'pm_project_templates' in existing_tables:
        print("表 pm_project_templates 已存在，跳过创建")
    else:
        op.create_table(
        'pm_project_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='模板ID'),
        sa.Column('template_code', sa.String(50), nullable=False, unique=True, index=True, comment='模板编码'),
        sa.Column('name', sa.String(200), nullable=False, comment='模板名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模板描述'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True, comment='模板分类（从基础数据获取）'),
        sa.Column('template_structure', postgresql.JSONB(), nullable=True, server_default='{}', comment='模板结构'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否启用'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='使用次数'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.ForeignKeyConstraint(['category_id'], ['pm_basic_data_categories.id'], name='fk_project_template_category', ondelete='SET NULL'),
        sa.Index('idx_project_template_code', 'template_code'),
        sa.Index('idx_project_template_active', 'is_active'),
        comment='项目模板表'
        )


def downgrade() -> None:
    # 删除表（按相反顺序）
    op.drop_table('pm_project_templates')
    op.drop_table('pm_project_plan_tasks')
    op.drop_table('pm_project_plans')
    op.drop_table('pm_program_plan_tasks')
    op.drop_table('pm_program_plans')

    # 删除项目表中的项目群关联
    op.drop_constraint('fk_project_program', 'pm_projects', type_='foreignkey')
    op.drop_index('idx_project_program', 'pm_projects')
    op.drop_column('pm_projects', 'program_id')

    op.drop_table('pm_programs')

"""添加月报表

Revision ID: 029
Revises: 028
Create Date: 2025-12-24

创建独立的月报表（pm_monthly_reports），替代使用周报表存储月报数据的临时方案
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade():
    """创建月报表"""
    print("=" * 50)
    print("创建月报表 (pm_monthly_reports)")
    print("=" * 50)

    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_monthly_reports' in existing_tables:
        print("表 pm_monthly_reports 已存在，跳过创建")
        print("=" * 50)
        return

    # 创建月报表
    op.create_table(
        'pm_monthly_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='月报ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('report_year', sa.Integer(), nullable=False, comment='报告年份'),
        sa.Column('report_month', sa.Integer(), nullable=False, comment='报告月份（1-12）'),
        sa.Column('summary', sa.Text(), nullable=True, comment='月度总结'),
        sa.Column('achievements', sa.Text(), nullable=True, comment='月度成果'),
        sa.Column('challenges', sa.Text(), nullable=True, comment='挑战与问题'),
        sa.Column('next_month_plan', sa.Text(), nullable=True, comment='下月计划'),
        sa.Column('progress_percent', sa.Float(), nullable=True, default=0.0, comment='月度进度百分比'),
        sa.Column('key_milestones', postgresql.JSONB(), nullable=True, default=list, comment='关键里程碑完成情况'),
        sa.Column('risk_summary', sa.Text(), nullable=True, comment='风险汇总'),
        sa.Column('resource_summary', sa.Text(), nullable=True, comment='资源使用情况'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default=dict, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),

        # 外键
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),

        # 唯一约束：同一项目同一月份只能有一份月报
        sa.UniqueConstraint('project_id', 'report_year', 'report_month', name='uq_project_monthly_report'),

        comment='项目月报表'
    )

    # 创建索引
    op.create_index('idx_monthly_reports_project_id', 'pm_monthly_reports', ['project_id'])
    op.create_index('idx_monthly_reports_year_month', 'pm_monthly_reports', ['report_year', 'report_month'])
    op.create_index('idx_monthly_reports_created_at', 'pm_monthly_reports', ['created_at'])

    print("月报表创建完成！")
    print("=" * 50)

    # 迁移现有数据（从周报聚合生成月报）
    print("\n开始迁移现有月报数据...")
    print("=" * 50)

    # 从周报数据聚合生成月报
    conn = op.get_bind()

    # 查询所有项目的周报，按项目和月份分组
    result = conn.execute(sa.text("""
        SELECT
            project_id,
            EXTRACT(YEAR FROM report_date)::INTEGER as year,
            EXTRACT(MONTH FROM report_date)::INTEGER as month,
            COUNT(*) as week_count,
            STRING_AGG(DISTINCT content_achievement, E'\\n\\n' ORDER BY content_achievement) FILTER (WHERE content_achievement IS NOT NULL AND content_achievement != '') as achievements,
            STRING_AGG(DISTINCT issues_risks, E'\\n\\n' ORDER BY issues_risks) FILTER (WHERE issues_risks IS NOT NULL AND issues_risks != '') as challenges,
            STRING_AGG(DISTINCT next_week_plan, E'\\n\\n' ORDER BY next_week_plan) FILTER (WHERE next_week_plan IS NOT NULL AND next_week_plan != '') as next_plan,
            MIN(created_at) as first_created,
            MAX(updated_at) as last_updated
        FROM pm_weekly_reports
        GROUP BY project_id, EXTRACT(YEAR FROM report_date), EXTRACT(MONTH FROM report_date)
        HAVING COUNT(*) > 0
    """))

    migrated_count = 0
    for row in result:
        project_id = row[0]
        year = row[1]
        month = row[2]
        week_count = row[3]
        achievements = row[4] or f'{year}年{month}月完成相关工作'
        challenges = row[5] or '无重大挑战'
        next_plan = row[6] or '继续推进项目'
        first_created = row[7]
        last_updated = row[8]

        # 检查是否已存在月报
        check_result = conn.execute(sa.text("""
            SELECT id FROM pm_monthly_reports
            WHERE project_id = :project_id
            AND report_year = :year
            AND report_month = :month
        """), {
            'project_id': project_id,
            'year': year,
            'month': month
        })

        if check_result.fetchone() is None:
            # 插入月报
            conn.execute(sa.text("""
                INSERT INTO pm_monthly_reports (
                    id, project_id, report_year, report_month,
                    summary, achievements, challenges, next_month_plan,
                    progress_percent, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :project_id, :year, :month,
                    :summary, :achievements, :challenges, :next_plan,
                    0.0, :created_at, :updated_at
                )
            """), {
                'project_id': project_id,
                'year': year,
                'month': month,
                'summary': f'{year}年{month}月项目进展总结（基于{week_count}份周报聚合）',
                'achievements': achievements[:5000] if achievements else None,  # 限制长度
                'challenges': challenges[:5000] if challenges else None,
                'next_plan': next_plan[:5000] if next_plan else None,
                'created_at': first_created,
                'updated_at': last_updated
            })
            migrated_count += 1

    print(f"已迁移 {migrated_count} 份月报数据")
    print("=" * 50)


def downgrade():
    """删除月报表"""
    print("=" * 50)
    print("删除月报表 (pm_monthly_reports)")
    print("=" * 50)

    # 删除索引
    op.drop_index('idx_monthly_reports_created_at', table_name='pm_monthly_reports')
    op.drop_index('idx_monthly_reports_year_month', table_name='pm_monthly_reports')
    op.drop_index('idx_monthly_reports_project_id', table_name='pm_monthly_reports')

    # 删除表
    op.drop_table('pm_monthly_reports')

    print("月报表删除完成！")
    print("=" * 50)


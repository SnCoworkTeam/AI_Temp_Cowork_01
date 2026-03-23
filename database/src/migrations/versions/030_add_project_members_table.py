"""添加项目成员表

Revision ID: 030
Revises: 029
Create Date: 2025-12-24

创建项目成员表（pm_project_members），实现项目级别权限控制
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade():
    """创建项目成员表"""
    print("=" * 50)
    print("创建项目成员表 (pm_project_members)")
    print("=" * 50)

    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'pm_project_members' in existing_tables:
        print("表 pm_project_members 已存在，跳过创建")
        print("=" * 50)
        return

    # 创建项目成员角色枚举类型
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projectmemberrole AS ENUM ('manager', 'member', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 创建项目成员表
    op.create_table(
        'pm_project_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='成员ID'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, comment='项目ID'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='用户ID'),
        sa.Column('role', postgresql.ENUM('manager', 'member', 'viewer', name='projectmemberrole', create_type=False), nullable=False, server_default='member', comment='成员角色'),
        sa.Column('joined_at', sa.Date(), nullable=True, comment='加入日期'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default=dict, comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),

        # 外键
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        # 唯一约束：同一用户在同一项目中只能有一个角色
        sa.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),

        comment='项目成员表（项目级别权限）'
    )

    # 创建索引
    op.create_index('idx_project_members_project_id', 'pm_project_members', ['project_id'])
    op.create_index('idx_project_members_user_id', 'pm_project_members', ['user_id'])
    op.create_index('idx_project_members_role', 'pm_project_members', ['role'])

    # 为现有项目添加创建者和管理员为项目经理
    print("\n为现有项目添加创建者和管理员...")
    conn = op.get_bind()

    # 将项目的manager_id添加为项目经理
    result = conn.execute(sa.text("""
        INSERT INTO pm_project_members (project_id, user_id, role, joined_at, created_at, updated_at)
        SELECT
            id as project_id,
            manager_id as user_id,
            'manager'::projectmemberrole as role,
            created_at::date as joined_at,
            created_at,
            updated_at
        FROM pm_projects
        WHERE manager_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM pm_project_members
            WHERE pm_project_members.project_id = pm_projects.id
            AND pm_project_members.user_id = pm_projects.manager_id
        )
    """))

    print(f"已为 {result.rowcount} 个项目添加项目经理")
    print("项目成员表创建完成！")
    print("=" * 50)


def downgrade():
    """删除项目成员表"""
    print("=" * 50)
    print("删除项目成员表 (pm_project_members)")
    print("=" * 50)

    # 删除索引
    op.drop_index('idx_project_members_role', table_name='pm_project_members')
    op.drop_index('idx_project_members_user_id', table_name='pm_project_members')
    op.drop_index('idx_project_members_project_id', table_name='pm_project_members')

    # 删除表
    op.drop_table('pm_project_members')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS projectmemberrole;")

    print("项目成员表删除完成！")
    print("=" * 50)


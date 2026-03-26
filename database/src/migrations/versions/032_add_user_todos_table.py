"""Add user todos table

Revision ID: 032_add_user_todos
Revises: 031_add_basic_data_tables
Create Date: 2025-12-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '032_add_user_todos'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'user_todos' in existing_tables:
        print("表 user_todos 已存在，跳过创建")
        return

    # 创建枚举类型
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE todocategory AS ENUM ('work', 'personal', 'urgent', 'project', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE todopriority AS ENUM ('high', 'medium', 'low');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE todostatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 创建待办事项表
    op.create_table(
        'user_todos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', postgresql.ENUM('work', 'personal', 'urgent', 'project', 'other', name='todocategory', create_type=False), nullable=False, server_default='work'),
        sa.Column('priority', postgresql.ENUM('high', 'medium', 'low', name='todopriority', create_type=False), nullable=False, server_default='medium'),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'cancelled', name='todostatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['pm_projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['pm_tasks.id'], ondelete='SET NULL'),
    )

    # 创建索引（如果不存在）
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('user_todos')]
    index_definitions = [
        ('idx_user_todos_user_id', ['user_id']),
        ('idx_user_todos_status', ['status']),
        ('idx_user_todos_due_date', ['due_date']),
        ('idx_user_todos_category', ['category']),
        ('idx_user_todos_priority', ['priority']),
        ('idx_user_todos_project_id', ['project_id']),
        ('idx_user_todos_task_id', ['task_id']),
        ('idx_user_todos_user_status', ['user_id', 'status']),
        ('idx_user_todos_user_due_date', ['user_id', 'due_date']),
    ]
    for idx_name, idx_columns in index_definitions:
        if idx_name not in existing_indexes:
            op.create_index(idx_name, 'user_todos', idx_columns)

    # 添加表注释
    op.execute("COMMENT ON TABLE user_todos IS '用户待办事项表'")
    op.execute("COMMENT ON COLUMN user_todos.id IS '待办事项ID'")
    op.execute("COMMENT ON COLUMN user_todos.user_id IS '用户ID'")
    op.execute("COMMENT ON COLUMN user_todos.title IS '标题'")
    op.execute("COMMENT ON COLUMN user_todos.description IS '描述'")
    op.execute("COMMENT ON COLUMN user_todos.category IS '分类'")
    op.execute("COMMENT ON COLUMN user_todos.priority IS '优先级'")
    op.execute("COMMENT ON COLUMN user_todos.status IS '状态'")
    op.execute("COMMENT ON COLUMN user_todos.due_date IS '截止日期'")
    op.execute("COMMENT ON COLUMN user_todos.completed_at IS '完成时间'")
    op.execute("COMMENT ON COLUMN user_todos.project_id IS '关联项目ID'")
    op.execute("COMMENT ON COLUMN user_todos.task_id IS '关联任务ID'")
    op.execute("COMMENT ON COLUMN user_todos.metadata IS '扩展元数据'")
    op.execute("COMMENT ON COLUMN user_todos.created_at IS '创建时间'")
    op.execute("COMMENT ON COLUMN user_todos.updated_at IS '更新时间'")


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_user_todos_user_due_date', table_name='user_todos')
    op.drop_index('idx_user_todos_user_status', table_name='user_todos')
    op.drop_index('idx_user_todos_task_id', table_name='user_todos')
    op.drop_index('idx_user_todos_project_id', table_name='user_todos')
    op.drop_index('idx_user_todos_priority', table_name='user_todos')
    op.drop_index('idx_user_todos_category', table_name='user_todos')
    op.drop_index('idx_user_todos_due_date', table_name='user_todos')
    op.drop_index('idx_user_todos_status', table_name='user_todos')
    op.drop_index('idx_user_todos_user_id', table_name='user_todos')

    # 删除表
    op.drop_table('user_todos')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS todostatus")
    op.execute("DROP TYPE IF EXISTS todopriority")
    op.execute("DROP TYPE IF EXISTS todocategory")




"""Add reporter_id to projects table

Revision ID: 033_add_project_reporter_id
Revises: 032_add_user_todos
Create Date: 2025-12-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '033_add_project_reporter_id'
down_revision = '032_add_user_todos'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('pm_projects')]

    if 'reporter_id' not in columns:
        # 添加填报人ID字段
        op.add_column('pm_projects',
            sa.Column('reporter_id', postgresql.UUID(as_uuid=True), nullable=True, comment='填报人ID')
        )

    # 检查外键是否已存在
    foreign_keys = [fk['name'] for fk in inspector.get_foreign_keys('pm_projects')]
    if 'fk_pm_projects_reporter_id' not in foreign_keys:
        # 添加外键约束
        op.create_foreign_key(
            'fk_pm_projects_reporter_id',
            'pm_projects', 'users',
            ['reporter_id'], ['id'],
            ondelete='SET NULL'
        )

    # 检查索引是否已存在
    indexes = [idx['name'] for idx in inspector.get_indexes('pm_projects')]
    if 'ix_pm_projects_reporter_id' not in indexes:
        # 添加索引
        op.create_index('ix_pm_projects_reporter_id', 'pm_projects', ['reporter_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_pm_projects_reporter_id', table_name='pm_projects')

    # 删除外键约束
    op.drop_constraint('fk_pm_projects_reporter_id', 'pm_projects', type_='foreignkey')

    # 删除字段
    op.drop_column('pm_projects', 'reporter_id')



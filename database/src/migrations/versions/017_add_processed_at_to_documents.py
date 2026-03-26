"""添加processed_at列到documents表

Revision ID: 017
Revises: 016
Create Date: 2025-01-XX

添加processed_at列到documents表，用于记录文档处理完成时间
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    """添加processed_at列"""
    print("=" * 50)
    print("添加processed_at列到documents表")
    print("=" * 50)
    
    # 检查列是否已存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'processed_at' not in columns:
        # 添加processed_at列
        op.add_column(
            'documents',
            sa.Column('processed_at', sa.DateTime(), nullable=True, comment='处理完成时间')
        )
        print("✅ processed_at 列已添加到 documents 表")
    else:
        print("ℹ️  processed_at 列已存在，跳过")


def downgrade():
    """删除processed_at列"""
    # 检查列是否存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'processed_at' in columns:
        op.drop_column('documents', 'processed_at')
        print("✅ processed_at 列已从 documents 表删除")
    else:
        print("ℹ️  processed_at 列不存在，跳过")



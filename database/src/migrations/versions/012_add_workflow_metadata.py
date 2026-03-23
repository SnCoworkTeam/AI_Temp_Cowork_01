"""
添加 workflow_metadata 列到 workflow_definitions 表

Revision ID: 012
Revises: 011
Create Date: 2025-11-19

问题: workflow_definitions 表缺少 workflow_metadata 列
影响: 保存工作流时出现 UndefinedColumn 错误
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '012'
down_revision = '011_add_workflow_versions'  # 使用完整的revision ID
branch_labels = None
depends_on = None


def upgrade():
    """添加 workflow_metadata 列"""
    print("=" * 50)
    print("添加 workflow_metadata 列到 workflow_definitions 表")
    print("=" * 50)
    
    # 检查列是否已存在
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_definitions' 
        AND column_name = 'workflow_metadata'
    """))
    
    if result.fetchone():
        print("⚠️  workflow_metadata 列已存在，跳过")
        return
    
    # 添加 workflow_metadata 列
    op.add_column(
        'workflow_definitions',
        sa.Column(
            'workflow_metadata',
            postgresql.JSONB(),
            nullable=True,
            server_default='{}',
            comment='元数据'
        )
    )
    
    print("✅ workflow_metadata 列已添加")


def downgrade():
    """移除 workflow_metadata 列"""
    print("移除 workflow_metadata 列...")
    
    # 检查列是否存在
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_definitions' 
        AND column_name = 'workflow_metadata'
    """))
    
    if not result.fetchone():
        print("⚠️  workflow_metadata 列不存在，跳过")
        return
    
    op.drop_column('workflow_definitions', 'workflow_metadata')
    print("✅ workflow_metadata 列已移除")


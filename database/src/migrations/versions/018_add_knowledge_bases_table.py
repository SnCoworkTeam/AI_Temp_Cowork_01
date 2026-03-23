"""添加knowledge_bases表和documents.knowledge_base_id字段

Revision ID: 018
Revises: 017
Create Date: 2025-01-XX

添加knowledge_bases表作为知识库的独立实体
在documents表中添加knowledge_base_id外键，建立文档与知识库的关联
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    """创建knowledge_bases表并添加knowledge_base_id字段到documents表"""
    print("=" * 50)
    print("添加knowledge_bases表和documents.knowledge_base_id字段")
    print("=" * 50)
    
    # 使用op.get_bind()获取连接，但需要确保op已正确初始化
    # 如果op.get_bind()不可用，使用op.connection
    try:
        connection = op.get_bind()
    except:
        connection = op.connection
    inspector = sa.inspect(connection)
    
    # 1. 创建knowledge_bases表
    if 'knowledge_bases' not in inspector.get_table_names():
        op.create_table(
            'knowledge_bases',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='知识库ID'),
            sa.Column('name', sa.String(200), nullable=False, comment='知识库名称'),
            sa.Column('description', sa.Text(), nullable=True, comment='知识库描述'),
            sa.Column('status', sa.String(50), nullable=False, server_default='active', comment='知识库状态'),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, comment='创建者ID'),
            sa.Column('embedding_model', sa.String(100), nullable=False, server_default='default', comment='嵌入模型'),
            sa.Column('chunk_strategy', sa.String(50), nullable=False, server_default='fixed', comment='分块策略'),
            sa.Column('chunk_size', sa.Integer(), nullable=False, server_default='1000', comment='分块大小'),
            sa.Column('chunk_overlap', sa.Integer(), nullable=False, server_default='200', comment='分块重叠'),
            sa.Column('settings', postgresql.JSONB(), nullable=True, comment='知识库设置'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_kb_created_by'),
        )
        
        # 创建索引
        op.create_index('idx_kb_name', 'knowledge_bases', ['name'])
        op.create_index('idx_kb_status', 'knowledge_bases', ['status'])
        op.create_index('idx_kb_created_by', 'knowledge_bases', ['created_by'])
        
        print("✅ knowledge_bases 表已创建")
    else:
        print("ℹ️  knowledge_bases 表已存在，跳过")
    
    # 2. 在documents表中添加knowledge_base_id字段
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'knowledge_base_id' not in columns:
        op.add_column(
            'documents',
            sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属知识库ID')
        )
        
        # 创建外键约束
        op.create_foreign_key(
            'fk_documents_knowledge_base_id',
            'documents',
            'knowledge_bases',
            ['knowledge_base_id'],
            ['id'],
            ondelete='SET NULL'
        )
        
        # 创建索引
        op.create_index('idx_documents_kb_id', 'documents', ['knowledge_base_id'])
        
        print("✅ knowledge_base_id 列已添加到 documents 表")
    else:
        print("ℹ️  knowledge_base_id 列已存在，跳过")


def downgrade():
    """删除knowledge_base_id字段和knowledge_bases表"""
    try:
        connection = op.get_bind()
    except:
        connection = op.connection
    inspector = sa.inspect(connection)
    
    # 1. 删除documents表中的knowledge_base_id字段
    columns = [col['name'] for col in inspector.get_columns('documents')]
    
    if 'knowledge_base_id' in columns:
        # 删除索引
        try:
            op.drop_index('idx_documents_kb_id', table_name='documents')
        except:
            pass
        
        # 删除外键约束
        try:
            op.drop_constraint('fk_documents_knowledge_base_id', 'documents', type_='foreignkey')
        except:
            pass
        
        # 删除列
        op.drop_column('documents', 'knowledge_base_id')
        print("✅ knowledge_base_id 列已从 documents 表删除")
    else:
        print("ℹ️  knowledge_base_id 列不存在，跳过")
    
    # 2. 删除knowledge_bases表
    if 'knowledge_bases' in inspector.get_table_names():
        op.drop_table('knowledge_bases')
        print("✅ knowledge_bases 表已删除")
    else:
        print("ℹ️  knowledge_bases 表不存在，跳过")


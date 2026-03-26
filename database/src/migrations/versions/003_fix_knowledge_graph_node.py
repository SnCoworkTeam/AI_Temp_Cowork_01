"""
数据库迁移脚本: 修复 KnowledgeGraphNode 字段映射

Revision ID: 003
Revises: 002
Create Date: 2025-11-13

问题: 模型定义(label, node_type, properties, document_id) vs
      迁移定义(concept, category, description) 完全不同
影响: 无法保存节点属性，无法关联源文档，知识图谱功能不可用
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """修复 KnowledgeGraphNode 表结构"""

    # 1. 重命名现有字段以匹配模型
    op.alter_column('knowledge_graph_nodes', 'concept',
                    new_column_name='label',
                    existing_type=sa.String(255))

    op.alter_column('knowledge_graph_nodes', 'category',
                    new_column_name='node_type',
                    existing_type=sa.String(100))

    # 2. 删除不匹配的字段
    op.drop_column('knowledge_graph_nodes', 'description')

    # 3. 添加缺失的字段
    op.add_column('knowledge_graph_nodes',
                  sa.Column('properties', JSONB, nullable=True,
                           comment='节点属性，JSON格式'))

    op.add_column('knowledge_graph_nodes',
                  sa.Column('document_id', UUID(as_uuid=True), nullable=True,
                           comment='关联的源文档ID'))

    # 4. 添加外键约束
    op.create_foreign_key(
        'fk_knowledge_graph_nodes_document',
        'knowledge_graph_nodes', 'documents',
        ['document_id'], ['id'],
        ondelete='SET NULL'
    )

    # 5. 添加索引
    op.create_index('idx_kg_nodes_type',
                    'knowledge_graph_nodes',
                    ['node_type'],
                    unique=False)

    op.create_index('idx_kg_nodes_document',
                    'knowledge_graph_nodes',
                    ['document_id'],
                    unique=False)

    print("✅ KnowledgeGraphNode 表结构修复完成")
    print("   - 重命名字段: concept→label, category→node_type")
    print("   - 添加了 properties, document_id 字段")
    print("   - 创建了外键约束和索引")


def downgrade():
    """回滚修复"""

    # 删除索引
    op.drop_index('idx_kg_nodes_document', table_name='knowledge_graph_nodes')
    op.drop_index('idx_kg_nodes_type', table_name='knowledge_graph_nodes')

    # 删除外键
    op.drop_constraint('fk_knowledge_graph_nodes_document',
                      'knowledge_graph_nodes', type_='foreignkey')

    # 删除新字段
    op.drop_column('knowledge_graph_nodes', 'document_id')
    op.drop_column('knowledge_graph_nodes', 'properties')

    # 恢复旧字段
    op.add_column('knowledge_graph_nodes',
                  sa.Column('description', sa.Text, nullable=True))

    # 重命名回原字段名
    op.alter_column('knowledge_graph_nodes', 'node_type',
                    new_column_name='category',
                    existing_type=sa.String(100))

    op.alter_column('knowledge_graph_nodes', 'label',
                    new_column_name='concept',
                    existing_type=sa.String(255))

    print("⚠️  已回滚 KnowledgeGraphNode 表结构修复")

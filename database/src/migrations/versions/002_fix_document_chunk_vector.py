"""
数据库迁移脚本: 修复 DocumentChunk 向量字段

Revision ID: 002
Revises: 001
Create Date: 2025-11-13

问题: DocumentChunk 模型定义 embedding(JSONB) 但迁移中是 vector_id(String)
影响: 无法存储嵌入向量，知识库语义搜索功能完全不可用
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = '002'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """修复 DocumentChunk 表结构"""

    # 1. 删除不匹配的字段
    op.drop_column('document_chunks', 'vector_id')
    op.drop_column('document_chunks', 'metadata')

    # 2. 添加正确的字段
    op.add_column('document_chunks',
                  sa.Column('embedding', JSONB, nullable=True,
                           comment='嵌入向量，存储为JSON数组'))

    op.add_column('document_chunks',
                  sa.Column('embedding_model', sa.String(100), nullable=True,
                           comment='使用的嵌入模型名称'))

    op.add_column('document_chunks',
                  sa.Column('start_char', sa.Integer, nullable=True,
                           comment='块在文档中的起始字符位置'))

    op.add_column('document_chunks',
                  sa.Column('end_char', sa.Integer, nullable=True,
                           comment='块在文档中的结束字符位置'))

    op.add_column('document_chunks',
                  sa.Column('page_number', sa.Integer, nullable=True,
                           comment='块所在的页码'))

    # 3. 添加索引以提高查询性能
    op.create_index('idx_document_chunks_document',
                    'document_chunks',
                    ['document_id', 'chunk_index'],
                    unique=False)

    print("✅ DocumentChunk 表结构修复完成")
    print("   - 删除了 vector_id 和 metadata 字段")
    print("   - 添加了 embedding, embedding_model, start_char, end_char, page_number")
    print("   - 创建了复合索引 idx_document_chunks_document")


def downgrade():
    """回滚修复"""

    # 删除索引
    op.drop_index('idx_document_chunks_document', table_name='document_chunks')

    # 删除新字段
    op.drop_column('document_chunks', 'page_number')
    op.drop_column('document_chunks', 'end_char')
    op.drop_column('document_chunks', 'start_char')
    op.drop_column('document_chunks', 'embedding_model')
    op.drop_column('document_chunks', 'embedding')

    # 恢复旧字段
    op.add_column('document_chunks',
                  sa.Column('vector_id', sa.String(255), nullable=True))
    op.add_column('document_chunks',
                  sa.Column('metadata', JSONB, nullable=True))

    print("⚠️  已回滚 DocumentChunk 表结构修复")

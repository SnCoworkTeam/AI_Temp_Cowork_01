"""
添加实体映射表

Revision ID: 020
Revises: 019
Create Date: 2025-11-28

功能: 创建实体映射表，用于映射knowledge-base和metadata-service的实体
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    """创建实体映射表"""
    print("=" * 50)
    print("创建实体映射表")
    print("=" * 50)
    
    # 创建 entity_mappings 表
    print("创建 entity_mappings 表...")
    op.create_table(
        'entity_mappings',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('source_uri', sa.String(length=500), nullable=False, comment='源实体URI'),
        sa.Column('source_type', sa.String(length=50), nullable=False, comment='源实体类型'),
        sa.Column('source_id', sa.String(length=255), nullable=False, comment='源实体ID'),
        sa.Column('target_uri', sa.String(length=500), nullable=False, comment='目标实体URI'),
        sa.Column('target_type', sa.String(length=50), nullable=False, comment='目标实体类型'),
        sa.Column('target_id', sa.String(length=255), nullable=False, comment='目标实体ID'),
        sa.Column('mapping_type', sa.String(length=50), nullable=False, server_default='auto', comment='映射类型：auto, manual, similarity'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0', comment='映射置信度（0-1）'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='状态：pending, confirmed, rejected'),
        sa.Column('mapped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='映射时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='实体映射表'
    )
    
    # 创建索引
    op.create_index('idx_source_uri', 'entity_mappings', ['source_uri'], unique=False)
    op.create_index('idx_target_uri', 'entity_mappings', ['target_uri'], unique=False)
    op.create_index('idx_source_target', 'entity_mappings', ['source_uri', 'target_uri'], unique=False)
    op.create_index('idx_status', 'entity_mappings', ['status'], unique=False)
    op.create_index('ix_entity_mappings_id', 'entity_mappings', ['id'], unique=False)
    
    print("✅ entity_mappings 表已创建")
    print("=" * 50)
    print("实体映射表创建完成")
    print("=" * 50)


def downgrade():
    """删除实体映射表"""
    print("删除实体映射表...")
    
    op.drop_index('ix_entity_mappings_id', table_name='entity_mappings')
    op.drop_index('idx_status', table_name='entity_mappings')
    op.drop_index('idx_source_target', table_name='entity_mappings')
    op.drop_index('idx_target_uri', table_name='entity_mappings')
    op.drop_index('idx_source_uri', table_name='entity_mappings')
    op.drop_table('entity_mappings')
    
    print("✅ 实体映射表已删除")









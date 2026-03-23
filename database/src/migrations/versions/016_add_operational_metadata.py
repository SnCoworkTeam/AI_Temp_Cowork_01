"""添加操作元数据表

Revision ID: 016
Revises: 015
Create Date: 2025-11-24

创建操作元数据表，用于存储使用统计和变更历史
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """创建操作元数据表"""
    print("=" * 50)
    print("创建操作元数据表：operational_metadata")
    print("=" * 50)
    
    # 创建操作元数据表
    op.create_table(
        'operational_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('usage_stats', postgresql.JSONB(), nullable=True),
        sa.Column('change_history', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_operational_metadata_asset_type', 'asset_type'),
        sa.Index('ix_operational_metadata_asset_id', 'asset_id'),
        sa.Index('ix_operational_metadata_asset_type_asset_id', 'asset_type', 'asset_id'),
        comment='操作元数据表，存储使用统计和变更历史'
    )
    print("✅ operational_metadata 表已创建")


def downgrade():
    """删除操作元数据表"""
    op.drop_table('operational_metadata')
    print("✅ operational_metadata 表已删除")



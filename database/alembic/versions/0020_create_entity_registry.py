"""create entity registry table

Revision ID: 0020
Revises: 0019
Create Date: 2025-11-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade():
    # 创建entity_registry表
    op.create_table(
        'entity_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_uri', sa.String(length=500), nullable=False, comment='统一实体URI'),
        sa.Column('domain', sa.String(length=50), nullable=False, comment='实体域（metadata, knowledge, sap, workflow）'),
        sa.Column('entity_type', sa.String(length=50), nullable=False, comment='实体类型（data_asset, node, business_entity等）'),
        sa.Column('internal_id', sa.String(length=255), nullable=False, comment='服务内部ID'),
        sa.Column('service_name', sa.String(length=50), nullable=False, comment='所属服务名称'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='active', comment='状态：active, deleted, merged'),
    sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='额外元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_entity_uri', 'entity_registry', ['entity_uri'], unique=True)
    op.create_index('idx_domain_type', 'entity_registry', ['domain', 'entity_type'])
    op.create_index('idx_service_internal', 'entity_registry', ['service_name', 'internal_id'])
    op.create_index('idx_status', 'entity_registry', ['status'])


def downgrade():
    op.drop_index('idx_status', table_name='entity_registry')
    op.drop_index('idx_service_internal', table_name='entity_registry')
    op.drop_index('idx_domain_type', table_name='entity_registry')
    op.drop_index('idx_entity_uri', table_name='entity_registry')
    op.drop_table('entity_registry')


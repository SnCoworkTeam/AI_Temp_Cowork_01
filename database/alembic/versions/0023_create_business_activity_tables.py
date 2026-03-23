"""创建业务活动相关表

Revision ID: 0023
Revises: 0022
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0023_create_business_activity_tables'
down_revision = '0022_create_value_metrics_table'
branch_labels = None
depends_on = None


def upgrade():
    # 创建业务活动表
    op.create_table(
        'business_activities',
        sa.Column('id', sa.String(255), primary_key=True, comment='活动ID，格式：activity:domain:name'),
        sa.Column('name', sa.String(200), nullable=False, comment='活动名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='活动描述'),
        sa.Column('activity_type', sa.String(50), nullable=False, comment='活动类型：action, query, approval, notification'),
        sa.Column('business_domain', sa.String(50), nullable=False, comment='业务领域：procurement, finance, warehouse等'),
        sa.Column('success_criteria', sa.Text(), nullable=True, comment='成功标准'),
        sa.Column('prerequisites', postgresql.JSONB(), nullable=True, comment='前置条件列表'),
        sa.Column('estimated_time', sa.String(50), nullable=True, comment='预计时间'),
        sa.Column('risk_level', sa.String(20), nullable=True, comment='风险等级：low, medium, high'),
        sa.Column('owner_dept', sa.String(100), nullable=True, comment='责任部门'),
        sa.Column('source_type', sa.String(50), nullable=True, comment='来源类型：document, log, conversation, code'),
        sa.Column('source_id', sa.String(255), nullable=True, comment='来源ID'),
        sa.Column('vector_entity_uri', sa.String(500), nullable=False, comment='指向vector_coordinator的URI'),
        sa.Column('embedding_snapshot', postgresql.JSONB(), nullable=True, comment='快照向量（用于快速检索，可选）'),
        sa.Column('embedding_version', sa.String(20), nullable=False, server_default='1.0', comment='向量版本'),
        sa.Column('last_vectorized_at', sa.DateTime(), nullable=True, comment='最后向量化时间'),
        sa.Column('description_updated_at', sa.DateTime(), nullable=True, comment='描述更新时间（用于触发向量更新）'),
        sa.Column('multi_modal_vectors', postgresql.JSONB(), nullable=True, comment='多模态向量URI列表'),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, comment='额外元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # 创建业务活动表索引
    op.create_index('idx_activity_name', 'business_activities', ['name'])
    op.create_index('idx_activity_type', 'business_activities', ['activity_type'])
    op.create_index('idx_activity_domain', 'business_activities', ['business_domain'])
    op.create_index('idx_activity_vector_uri', 'business_activities', ['vector_entity_uri'])
    op.create_index('idx_activity_domain_type', 'business_activities', ['business_domain', 'activity_type'])
    
    # 创建能力单元表
    op.create_table(
        'capability_units',
        sa.Column('id', sa.String(255), primary_key=True, comment='能力单元ID，格式：component:system:name 或 agent:name'),
        sa.Column('name', sa.String(200), nullable=False, comment='能力单元名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='能力单元描述'),
        sa.Column('capability_type', sa.String(50), nullable=False, comment='能力类型：Component, Agent, Tool, API'),
        sa.Column('version', sa.String(50), nullable=True, comment='版本号'),
        sa.Column('endpoint', sa.String(500), nullable=True, comment='端点URL'),
        sa.Column('input_schema', postgresql.JSONB(), nullable=True, comment='输入参数Schema'),
        sa.Column('output_schema', postgresql.JSONB(), nullable=True, comment='输出结果Schema'),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='0.0', comment='历史成功率（0.0-1.0）'),
        sa.Column('avg_response_time', sa.Float(), nullable=True, comment='平均响应时间（秒）'),
        sa.Column('max_concurrent', sa.Integer(), nullable=False, server_default='1', comment='最大并发数'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='使用次数'),
        sa.Column('tags', postgresql.JSONB(), nullable=True, comment='标签列表'),
        sa.Column('category', sa.String(100), nullable=True, comment='分类'),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, comment='额外元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # 创建能力单元表索引
    op.create_index('idx_capability_name', 'capability_units', ['name'])
    op.create_index('idx_capability_type', 'capability_units', ['capability_type'])
    op.create_index('idx_capability_category', 'capability_units', ['category'])
    op.create_index('idx_capability_reliability', 'capability_units', ['reliability_score'])
    
    # 创建活动-能力映射表
    op.create_table(
        'activity_capability_mappings',
        sa.Column('id', sa.String(255), primary_key=True, comment='映射ID，格式：mapping:activity_id:capability_id'),
        sa.Column('activity_id', sa.String(255), nullable=False, comment='业务活动ID'),
        sa.Column('capability_id', sa.String(255), nullable=False, comment='能力单元ID'),
        sa.Column('mapping_type', sa.String(50), nullable=False, server_default='primary', comment='映射类型：primary, alternative, fallback'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0', comment='优先级（数字越大优先级越高）'),
        sa.Column('conditions', postgresql.JSONB(), nullable=True, comment='使用条件'),
        sa.Column('success_rate', sa.Float(), nullable=False, server_default='0.0', comment='使用该能力执行活动的成功率（0.0-1.0）'),
        sa.Column('avg_execution_time', sa.Float(), nullable=True, comment='平均执行时间（秒）'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='使用次数'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0', comment='映射置信度（0.0-1.0）'),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True, comment='额外元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # 创建活动-能力映射表索引
    op.create_index('idx_mapping_activity', 'activity_capability_mappings', ['activity_id'])
    op.create_index('idx_mapping_capability', 'activity_capability_mappings', ['capability_id'])
    op.create_index('idx_mapping_type', 'activity_capability_mappings', ['mapping_type'])
    op.create_index('idx_mapping_activity_capability', 'activity_capability_mappings', ['activity_id', 'capability_id'], unique=True)
    op.create_index('idx_mapping_success_rate', 'activity_capability_mappings', ['success_rate'])


def downgrade():
    # 删除索引
    op.drop_index('idx_mapping_success_rate', table_name='activity_capability_mappings')
    op.drop_index('idx_mapping_activity_capability', table_name='activity_capability_mappings')
    op.drop_index('idx_mapping_type', table_name='activity_capability_mappings')
    op.drop_index('idx_mapping_capability', table_name='activity_capability_mappings')
    op.drop_index('idx_mapping_activity', table_name='activity_capability_mappings')
    
    op.drop_index('idx_capability_reliability', table_name='capability_units')
    op.drop_index('idx_capability_category', table_name='capability_units')
    op.drop_index('idx_capability_type', table_name='capability_units')
    op.drop_index('idx_capability_name', table_name='capability_units')
    
    op.drop_index('idx_activity_domain_type', table_name='business_activities')
    op.drop_index('idx_activity_vector_uri', table_name='business_activities')
    op.drop_index('idx_activity_domain', table_name='business_activities')
    op.drop_index('idx_activity_type', table_name='business_activities')
    op.drop_index('idx_activity_name', table_name='business_activities')
    
    # 删除表
    op.drop_table('activity_capability_mappings')
    op.drop_table('capability_units')
    op.drop_table('business_activities')


"""添加元数据表（ai_models, data_assets, business_entities）

Revision ID: 015
Revises: 012
Create Date: 2025-11-23

创建metadata-service需要的表：
- ai_models: AI模型元数据
- data_assets: 数据资产元数据
- business_entities: 业务实体元数据
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '015'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    """创建元数据表"""
    print("=" * 50)
    print("创建元数据表：ai_models, data_assets, business_entities")
    print("=" * 50)
    
    # 创建枚举类型
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE modeltype AS ENUM ('llm', 'embedding', 'classification', 'regression', 'clustering', 'custom');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE modelstatus AS ENUM ('training', 'active', 'deprecated', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dataassettype AS ENUM ('dataset', 'table', 'view', 'file', 'stream', 'api');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dataassetstatus AS ENUM ('active', 'deprecated', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE entitytype AS ENUM ('domain', 'concept', 'term', 'glossary', 'policy', 'rule');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 创建 ai_models 表
    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_type', postgresql.ENUM('llm', 'embedding', 'classification', 'regression', 'clustering', 'custom', name='modeltype', create_type=False), nullable=False, index=True),
        sa.Column('status', postgresql.ENUM('training', 'active', 'deprecated', 'archived', name='modelstatus', create_type=False), nullable=False, default='active', index=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('framework', sa.String(100), nullable=True),
        sa.Column('model_path', sa.String(500), nullable=True),
        sa.Column('model_size', sa.Integer(), nullable=True),
        sa.Column('training_dataset', sa.String(255), nullable=True),
        sa.Column('training_config', postgresql.JSONB(), nullable=True),
        sa.Column('hyperparameters', postgresql.JSONB(), nullable=True),
        sa.Column('training_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('deployment_endpoint', sa.String(500), nullable=True),
        sa.Column('deployment_config', postgresql.JSONB(), nullable=True),
        sa.Column('inference_latency', sa.Float(), nullable=True),
        sa.Column('business_owner', sa.String(100), nullable=True),
        sa.Column('technical_owner', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('use_cases', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    print("✅ ai_models 表已创建")
    
    # 创建 data_assets 表
    op.create_table(
        'data_assets',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('asset_type', postgresql.ENUM('dataset', 'table', 'view', 'file', 'stream', 'api', name='dataassettype', create_type=False), nullable=False, index=True),
        sa.Column('status', postgresql.ENUM('active', 'deprecated', 'archived', name='dataassetstatus', create_type=False), nullable=False, default='active', index=True),
        sa.Column('source_system', sa.String(100), nullable=True),
        sa.Column('source_path', sa.String(500), nullable=True),
        sa.Column('source_connection', sa.String(255), nullable=True),
        sa.Column('schema_info', postgresql.JSONB(), nullable=True),
        sa.Column('sample_data', postgresql.JSONB(), nullable=True),
        sa.Column('data_quality_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('business_owner', sa.String(100), nullable=True),
        sa.Column('technical_owner', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('classification', sa.String(50), nullable=True),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('update_frequency', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    print("✅ data_assets 表已创建")
    
    # 创建 business_entities 表
    op.create_table(
        'business_entities',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_type', postgresql.ENUM('domain', 'concept', 'term', 'glossary', 'policy', 'rule', name='entitytype', create_type=False), nullable=False, index=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('business_entities.id'), nullable=True),
        sa.Column('business_definition', sa.Text(), nullable=True),
        sa.Column('business_rules', postgresql.JSONB(), nullable=True),
        sa.Column('data_dictionary', postgresql.JSONB(), nullable=True),
        sa.Column('related_entities', postgresql.JSONB(), nullable=True),
        sa.Column('related_data_assets', postgresql.JSONB(), nullable=True),
        sa.Column('related_models', postgresql.JSONB(), nullable=True),
        sa.Column('data_steward', sa.String(100), nullable=True),
        sa.Column('business_owner', sa.String(100), nullable=True),
        sa.Column('classification', sa.String(50), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    print("✅ business_entities 表已创建")
    
    # 创建索引
    op.create_index('idx_ai_models_name', 'ai_models', ['name'])
    op.create_index('idx_ai_models_type_status', 'ai_models', ['model_type', 'status'])
    op.create_index('idx_data_assets_name', 'data_assets', ['name'])
    op.create_index('idx_data_assets_type_status', 'data_assets', ['asset_type', 'status'])
    op.create_index('idx_business_entities_name', 'business_entities', ['name'])
    op.create_index('idx_business_entities_type', 'business_entities', ['entity_type'])
    op.create_index('idx_business_entities_parent', 'business_entities', ['parent_id'])
    
    print("✅ 所有索引已创建")


def downgrade():
    """删除元数据表"""
    print("删除元数据表...")
    
    # 删除索引
    op.drop_index('idx_business_entities_parent', 'business_entities')
    op.drop_index('idx_business_entities_type', 'business_entities')
    op.drop_index('idx_business_entities_name', 'business_entities')
    op.drop_index('idx_data_assets_type_status', 'data_assets')
    op.drop_index('idx_data_assets_name', 'data_assets')
    op.drop_index('idx_ai_models_type_status', 'ai_models')
    op.drop_index('idx_ai_models_name', 'ai_models')
    
    # 删除表
    op.drop_table('business_entities')
    op.drop_table('data_assets')
    op.drop_table('ai_models')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS entitytype')
    op.execute('DROP TYPE IF EXISTS dataassetstatus')
    op.execute('DROP TYPE IF EXISTS dataassettype')
    op.execute('DROP TYPE IF EXISTS modelstatus')
    op.execute('DROP TYPE IF EXISTS modeltype')
    
    print("✅ 元数据表已删除")



"""添加分类维度字段

Revision ID: 028
Revises: 027
Create Date: 2025-12-19

为元数据表添加分类维度字段：
- classification_dimensions: JSON字段，存储多维度分类信息
- standardized_tags: JSON字段，存储标准化标签

支持三层分类体系：
1. 主分类（primary classification）- 保留在classification字段
2. 维度分类（dimension classification）- 存储在classification_dimensions
3. 标准化标签（standardized tags）- 存储在standardized_tags
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '028'
# 支持多个可能的父版本，优先使用027，如果不存在则使用合并点
# 如果服务器上存在156ed976eba1合并点，则使用它；否则使用8323deb6c345或027
down_revision = '027'  # 优先使用027，如果不存在会在服务器上自动处理
branch_labels = None
depends_on = None


def upgrade():
    """添加分类维度字段"""
    print("=" * 50)
    print("添加分类维度字段到元数据表")
    print("=" * 50)
    
    # 为 data_assets 表添加分类维度字段
    print("为 data_assets 表添加分类维度字段...")
    op.add_column('data_assets', 
        sa.Column('classification_dimensions', postgresql.JSONB, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    )
    op.add_column('data_assets',
        sa.Column('standardized_tags', postgresql.JSONB, nullable=True, comment='标准化标签列表')
    )
    
    # 为 ai_models 表添加分类维度字段
    print("为 ai_models 表添加分类维度字段...")
    op.add_column('ai_models',
        sa.Column('classification_dimensions', postgresql.JSONB, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    )
    op.add_column('ai_models',
        sa.Column('standardized_tags', postgresql.JSONB, nullable=True, comment='标准化标签列表')
    )
    
    # 检查 workflow_metadata 表是否存在，如果不存在则创建
    print("检查 workflow_metadata 表...")
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'workflow_metadata'
    """))
    
    if not result.fetchone():
        print("workflow_metadata 表不存在，正在创建...")
        # 创建 workflowstatus 枚举类型
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'deprecated', 'archived');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # 创建 workflow_metadata 表
        op.create_table(
            'workflow_metadata',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('workflow_id', sa.String(100), nullable=False, unique=True, index=True),
            sa.Column('name', sa.String(255), nullable=False, index=True),
            sa.Column('display_name', sa.String(255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', postgresql.ENUM('draft', 'active', 'deprecated', 'archived', name='workflowstatus', create_type=False), nullable=False, default='active', index=True),
            sa.Column('version', sa.String(50), nullable=True),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('workflow_type', sa.String(50), nullable=True),
            sa.Column('definition', postgresql.JSONB(), nullable=True),
            sa.Column('input_schema', postgresql.JSONB(), nullable=True),
            sa.Column('output_schema', postgresql.JSONB(), nullable=True),
            sa.Column('execution_count', sa.Integer(), default=0),
            sa.Column('last_execution_time', sa.DateTime(), nullable=True),
            sa.Column('average_execution_time', sa.Integer(), nullable=True),
            sa.Column('success_rate', sa.String(10), nullable=True),
            sa.Column('dependencies', postgresql.JSONB(), nullable=True),
            sa.Column('data_sources', postgresql.JSONB(), nullable=True),
            sa.Column('data_sinks', postgresql.JSONB(), nullable=True),
            sa.Column('business_owner', sa.String(100), nullable=True),
            sa.Column('technical_owner', sa.String(100), nullable=True),
            sa.Column('tags', postgresql.JSONB(), nullable=True),
            sa.Column('use_cases', postgresql.JSONB(), nullable=True),
            sa.Column('classification_dimensions', postgresql.JSONB(), nullable=True, comment='分类维度（业务、技术、生命周期、治理）'),
            sa.Column('standardized_tags', postgresql.JSONB(), nullable=True, comment='标准化标签列表'),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        )
        print("✅ workflow_metadata 表已创建（包含分类维度字段）")
    else:
        print("workflow_metadata 表已存在，添加分类维度字段...")
        # 如果表已存在，检查并添加分类维度字段
        try:
            # 检查列是否已存在
            col_result = conn.execute(sa.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'workflow_metadata' 
                AND column_name = 'classification_dimensions'
            """))
            if not col_result.fetchone():
                op.add_column('workflow_metadata',
                    sa.Column('classification_dimensions', postgresql.JSONB, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
                )
        except Exception as e:
            print(f"⚠️  添加 classification_dimensions 列时出错: {e}")
        
        try:
            col_result = conn.execute(sa.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'workflow_metadata' 
                AND column_name = 'standardized_tags'
            """))
            if not col_result.fetchone():
                op.add_column('workflow_metadata',
                    sa.Column('standardized_tags', postgresql.JSONB, nullable=True, comment='标准化标签列表')
                )
        except Exception as e:
            print(f"⚠️  添加 standardized_tags 列时出错: {e}")
    
    # 为 business_entities 表添加分类维度字段
    print("为 business_entities 表添加分类维度字段...")
    op.add_column('business_entities',
        sa.Column('classification_dimensions', postgresql.JSONB, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    )
    op.add_column('business_entities',
        sa.Column('standardized_tags', postgresql.JSONB, nullable=True, comment='标准化标签列表')
    )
    
    # 创建索引以优化查询性能
    print("创建分类维度索引...")
    
    # data_assets 表的索引
    # 注意：PostgreSQL JSONB索引需要使用表达式索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_data_assets_business_domain 
        ON data_assets USING btree ((classification_dimensions->'business'->>'domain'));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_data_assets_technical_source 
        ON data_assets USING btree ((classification_dimensions->'technical'->>'source'));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_data_assets_standardized_tags 
        ON data_assets USING gin (standardized_tags);
    """)
    
    # ai_models 表的索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_models_lifecycle_status 
        ON ai_models USING btree ((classification_dimensions->'lifecycle'->>'status'));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_models_standardized_tags 
        ON ai_models USING gin (standardized_tags);
    """)
    
    # workflow_metadata 表的索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_workflow_business_domain 
        ON workflow_metadata USING btree ((classification_dimensions->'business'->>'domain'));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_workflow_standardized_tags 
        ON workflow_metadata USING gin (standardized_tags);
    """)
    
    # business_entities 表的索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_entities_business_domain 
        ON business_entities USING btree ((classification_dimensions->'business'->>'domain'));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_entities_standardized_tags 
        ON business_entities USING gin (standardized_tags);
    """)
    
    print("分类维度字段添加完成！")
    print("=" * 50)


def downgrade():
    """回滚分类维度字段"""
    print("=" * 50)
    print("回滚分类维度字段")
    print("=" * 50)
    
    # 删除索引
    op.execute("DROP INDEX IF EXISTS idx_business_entities_standardized_tags;")
    op.execute("DROP INDEX IF EXISTS idx_business_entities_business_domain;")
    op.execute("DROP INDEX IF EXISTS idx_workflow_standardized_tags;")
    op.execute("DROP INDEX IF EXISTS idx_workflow_business_domain;")
    op.execute("DROP INDEX IF EXISTS idx_ai_models_standardized_tags;")
    op.execute("DROP INDEX IF EXISTS idx_ai_models_lifecycle_status;")
    op.execute("DROP INDEX IF EXISTS idx_data_assets_standardized_tags;")
    op.execute("DROP INDEX IF EXISTS idx_data_assets_technical_source;")
    op.execute("DROP INDEX IF EXISTS idx_data_assets_business_domain;")
    
    # 删除字段
    op.drop_column('business_entities', 'standardized_tags')
    op.drop_column('business_entities', 'classification_dimensions')
    op.drop_column('workflow_metadata', 'standardized_tags')
    op.drop_column('workflow_metadata', 'classification_dimensions')
    op.drop_column('ai_models', 'standardized_tags')
    op.drop_column('ai_models', 'classification_dimensions')
    op.drop_column('data_assets', 'standardized_tags')
    op.drop_column('data_assets', 'classification_dimensions')
    
    print("分类维度字段回滚完成！")
    print("=" * 50)




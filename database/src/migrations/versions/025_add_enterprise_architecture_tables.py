"""
添加企业架构表

Revision ID: 025
Revises: 024
Create Date: 2025-12-07

功能: 创建企业架构相关表（业务架构、应用架构、数据架构、技术架构、架构关系）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade():
    """创建企业架构相关表"""
    print("=" * 50)
    print("创建企业架构表")
    print("=" * 50)
    
    # ========== 业务架构表 ==========
    
    # 创建 business_processes 表
    print("创建 business_processes 表...")
    op.create_table(
        'business_processes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='流程ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='流程名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='流程描述'),
        sa.Column('owner', sa.String(length=255), nullable=True, comment='负责人'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active', comment='状态'),
        sa.Column('classification', sa.String(length=100), nullable=True, comment='分类'),
        sa.Column('level', sa.Integer(), nullable=True, server_default='1', comment='层级'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='父流程ID'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['business_processes.id'], name='fk_business_processes_parent_id', ondelete='SET NULL'),
        comment='业务流程表'
    )
    op.create_index('ix_business_processes_name', 'business_processes', ['name'], unique=False)
    op.create_index('ix_business_processes_status', 'business_processes', ['status'], unique=False)
    op.create_index('ix_business_processes_parent_id', 'business_processes', ['parent_id'], unique=False)
    print("✅ business_processes 表已创建")
    
    # 创建 business_capabilities 表
    print("创建 business_capabilities 表...")
    op.create_table(
        'business_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='能力ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='能力名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='能力描述'),
        sa.Column('level', sa.Integer(), nullable=True, server_default='1', comment='层级'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='父能力ID'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['business_capabilities.id'], name='fk_business_capabilities_parent_id', ondelete='SET NULL'),
        comment='业务能力表'
    )
    op.create_index('ix_business_capabilities_name', 'business_capabilities', ['name'], unique=False)
    op.create_index('ix_business_capabilities_parent_id', 'business_capabilities', ['parent_id'], unique=False)
    print("✅ business_capabilities 表已创建")
    
    # 创建 business_services 表
    print("创建 business_services 表...")
    op.create_table(
        'business_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='服务ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='服务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='服务描述'),
        sa.Column('service_type', sa.String(length=100), nullable=True, comment='服务类型'),
        sa.Column('endpoint', sa.String(length=500), nullable=True, comment='服务端点'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active', comment='状态'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='业务服务表'
    )
    op.create_index('ix_business_services_name', 'business_services', ['name'], unique=False)
    op.create_index('ix_business_services_status', 'business_services', ['status'], unique=False)
    print("✅ business_services 表已创建")
    
    # ========== 应用架构表 ==========
    
    # 创建 application_systems 表
    print("创建 application_systems 表...")
    op.create_table(
        'application_systems',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='系统ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='系统名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='系统描述'),
        sa.Column('system_type', sa.String(length=100), nullable=True, comment='系统类型'),
        sa.Column('vendor', sa.String(length=255), nullable=True, comment='供应商'),
        sa.Column('version', sa.String(length=50), nullable=True, comment='版本'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active', comment='状态'),
        sa.Column('owner', sa.String(length=255), nullable=True, comment='负责人'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='应用系统表'
    )
    op.create_index('ix_application_systems_name', 'application_systems', ['name'], unique=False)
    op.create_index('ix_application_systems_status', 'application_systems', ['status'], unique=False)
    print("✅ application_systems 表已创建")
    
    # 创建 application_services 表
    print("创建 application_services 表...")
    op.create_table(
        'application_services',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='服务ID'),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=True, comment='应用系统ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='服务名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='服务描述'),
        sa.Column('service_type', sa.String(length=100), nullable=True, comment='服务类型'),
        sa.Column('protocol', sa.String(length=50), nullable=True, comment='协议'),
        sa.Column('endpoint', sa.String(length=500), nullable=True, comment='服务端点'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['application_id'], ['application_systems.id'], name='fk_application_services_application_id', ondelete='CASCADE'),
        comment='应用服务表'
    )
    op.create_index('ix_application_services_application_id', 'application_services', ['application_id'], unique=False)
    op.create_index('ix_application_services_name', 'application_services', ['name'], unique=False)
    print("✅ application_services 表已创建")
    
    # 创建 api_interfaces 表
    print("创建 api_interfaces 表...")
    op.create_table(
        'api_interfaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='接口ID'),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=True, comment='应用服务ID'),
        sa.Column('path', sa.String(length=500), nullable=False, comment='接口路径'),
        sa.Column('method', sa.String(length=10), nullable=False, comment='HTTP方法'),
        sa.Column('description', sa.Text(), nullable=True, comment='接口描述'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['service_id'], ['application_services.id'], name='fk_api_interfaces_service_id', ondelete='CASCADE'),
        comment='API接口表'
    )
    op.create_index('ix_api_interfaces_service_id', 'api_interfaces', ['service_id'], unique=False)
    op.create_index('ix_api_interfaces_path_method', 'api_interfaces', ['path', 'method'], unique=False)
    print("✅ api_interfaces 表已创建")
    
    # ========== 数据架构表 ==========
    
    # 创建 data_entities 表
    print("创建 data_entities 表...")
    op.create_table(
        'data_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='实体ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='实体名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='实体描述'),
        sa.Column('schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='数据模式'),
        sa.Column('entity_type', sa.String(length=100), nullable=True, comment='实体类型'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='数据实体表'
    )
    op.create_index('ix_data_entities_name', 'data_entities', ['name'], unique=False)
    print("✅ data_entities 表已创建")
    
    # 创建 data_models 表
    print("创建 data_models 表...")
    op.create_table(
        'data_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='模型ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='模型名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='模型描述'),
        sa.Column('version', sa.String(length=50), nullable=True, comment='版本'),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='模型定义'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='数据模型表'
    )
    op.create_index('ix_data_models_name', 'data_models', ['name'], unique=False)
    print("✅ data_models 表已创建")
    
    # 创建 data_flows 表
    print("创建 data_flows 表...")
    op.create_table(
        'data_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='数据流ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='数据流名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='数据流描述'),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='源实体ID'),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), nullable=True, comment='目标实体ID'),
        sa.Column('transformation', sa.Text(), nullable=True, comment='转换规则'),
        sa.Column('neo4j_relationship_id', sa.String(length=255), nullable=True, comment='Neo4j关系ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_entity_id'], ['data_entities.id'], name='fk_data_flows_source_entity_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['data_entities.id'], name='fk_data_flows_target_entity_id', ondelete='SET NULL'),
        comment='数据流表'
    )
    op.create_index('ix_data_flows_source_entity_id', 'data_flows', ['source_entity_id'], unique=False)
    op.create_index('ix_data_flows_target_entity_id', 'data_flows', ['target_entity_id'], unique=False)
    print("✅ data_flows 表已创建")
    
    # ========== 技术架构表 ==========
    
    # 创建 technology_components 表
    print("创建 technology_components 表...")
    op.create_table(
        'technology_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='组件ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='组件名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='组件描述'),
        sa.Column('component_type', sa.String(length=100), nullable=True, comment='组件类型'),
        sa.Column('version', sa.String(length=50), nullable=True, comment='版本'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='技术组件表'
    )
    op.create_index('ix_technology_components_name', 'technology_components', ['name'], unique=False)
    print("✅ technology_components 表已创建")
    
    # 创建 technology_stacks 表
    print("创建 technology_stacks 表...")
    op.create_table(
        'technology_stacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='技术栈ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='技术栈名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='技术栈描述'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='类别'),
        sa.Column('components', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='组件列表'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='技术栈表'
    )
    op.create_index('ix_technology_stacks_name', 'technology_stacks', ['name'], unique=False)
    print("✅ technology_stacks 表已创建")
    
    # 创建 infrastructure_components 表
    print("创建 infrastructure_components 表...")
    op.create_table(
        'infrastructure_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='基础设施组件ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='组件名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='组件描述'),
        sa.Column('component_type', sa.String(length=100), nullable=True, comment='组件类型'),
        sa.Column('specifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='规格说明'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='基础设施组件表'
    )
    op.create_index('ix_infrastructure_components_name', 'infrastructure_components', ['name'], unique=False)
    print("✅ infrastructure_components 表已创建")
    
    # ========== 架构关系表 ==========
    
    # 创建 architecture_relationships 表
    print("创建 architecture_relationships 表...")
    op.create_table(
        'architecture_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='关系ID'),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False, comment='源实体ID'),
        sa.Column('source_type', sa.String(length=100), nullable=False, comment='源实体类型'),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False, comment='目标实体ID'),
        sa.Column('target_type', sa.String(length=100), nullable=False, comment='目标实体类型'),
        sa.Column('relationship_type', sa.String(length=100), nullable=False, comment='关系类型'),
        sa.Column('description', sa.Text(), nullable=True, comment='关系描述'),
        sa.Column('neo4j_relationship_id', sa.String(length=255), nullable=True, comment='Neo4j关系ID'),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='关系属性'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='架构关系表'
    )
    op.create_index('ix_architecture_relationships_source', 'architecture_relationships', ['source_type', 'source_id'], unique=False)
    op.create_index('ix_architecture_relationships_target', 'architecture_relationships', ['target_type', 'target_id'], unique=False)
    op.create_index('ix_architecture_relationships_type', 'architecture_relationships', ['relationship_type'], unique=False)
    print("✅ architecture_relationships 表已创建")
    
    # ========== 元数据分类表 ==========
    
    # 创建 metadata_classifications 表
    print("创建 metadata_classifications 表...")
    op.create_table(
        'metadata_classifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='分类ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='分类名称（英文）'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称（中文）'),
        sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='父分类ID'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1', comment='层级'),
        sa.Column('order_index', sa.Integer(), nullable=True, server_default='0', comment='排序索引'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['metadata_classifications.id'], name='fk_metadata_classifications_parent_id', ondelete='SET NULL'),
        comment='元数据分类表'
    )
    op.create_index('ix_metadata_classifications_name', 'metadata_classifications', ['name'], unique=True)
    op.create_index('ix_metadata_classifications_parent_id', 'metadata_classifications', ['parent_id'], unique=False)
    print("✅ metadata_classifications 表已创建")
    
    print("=" * 50)
    print("企业架构表创建完成")
    print("=" * 50)


def downgrade():
    """删除企业架构相关表"""
    print("删除企业架构表...")
    
    op.drop_index('ix_metadata_classifications_parent_id', table_name='metadata_classifications')
    op.drop_index('ix_metadata_classifications_name', table_name='metadata_classifications')
    op.drop_table('metadata_classifications')
    print("✅ metadata_classifications 表已删除")
    
    op.drop_index('ix_architecture_relationships_type', table_name='architecture_relationships')
    op.drop_index('ix_architecture_relationships_target', table_name='architecture_relationships')
    op.drop_index('ix_architecture_relationships_source', table_name='architecture_relationships')
    op.drop_table('architecture_relationships')
    print("✅ architecture_relationships 表已删除")
    
    op.drop_index('ix_infrastructure_components_name', table_name='infrastructure_components')
    op.drop_table('infrastructure_components')
    print("✅ infrastructure_components 表已删除")
    
    op.drop_index('ix_technology_stacks_name', table_name='technology_stacks')
    op.drop_table('technology_stacks')
    print("✅ technology_stacks 表已删除")
    
    op.drop_index('ix_technology_components_name', table_name='technology_components')
    op.drop_table('technology_components')
    print("✅ technology_components 表已删除")
    
    op.drop_index('ix_data_flows_target_entity_id', table_name='data_flows')
    op.drop_index('ix_data_flows_source_entity_id', table_name='data_flows')
    op.drop_table('data_flows')
    print("✅ data_flows 表已删除")
    
    op.drop_index('ix_data_models_name', table_name='data_models')
    op.drop_table('data_models')
    print("✅ data_models 表已删除")
    
    op.drop_index('ix_data_entities_name', table_name='data_entities')
    op.drop_table('data_entities')
    print("✅ data_entities 表已删除")
    
    op.drop_index('ix_api_interfaces_path_method', table_name='api_interfaces')
    op.drop_index('ix_api_interfaces_service_id', table_name='api_interfaces')
    op.drop_table('api_interfaces')
    print("✅ api_interfaces 表已删除")
    
    op.drop_index('ix_application_services_name', table_name='application_services')
    op.drop_index('ix_application_services_application_id', table_name='application_services')
    op.drop_table('application_services')
    print("✅ application_services 表已删除")
    
    op.drop_index('ix_application_systems_status', table_name='application_systems')
    op.drop_index('ix_application_systems_name', table_name='application_systems')
    op.drop_table('application_systems')
    print("✅ application_systems 表已删除")
    
    op.drop_index('ix_business_services_status', table_name='business_services')
    op.drop_index('ix_business_services_name', table_name='business_services')
    op.drop_table('business_services')
    print("✅ business_services 表已删除")
    
    op.drop_index('ix_business_capabilities_parent_id', table_name='business_capabilities')
    op.drop_index('ix_business_capabilities_name', table_name='business_capabilities')
    op.drop_table('business_capabilities')
    print("✅ business_capabilities 表已删除")
    
    op.drop_index('ix_business_processes_parent_id', table_name='business_processes')
    op.drop_index('ix_business_processes_status', table_name='business_processes')
    op.drop_index('ix_business_processes_name', table_name='business_processes')
    op.drop_table('business_processes')
    print("✅ business_processes 表已删除")
    
    print("企业架构表删除完成")


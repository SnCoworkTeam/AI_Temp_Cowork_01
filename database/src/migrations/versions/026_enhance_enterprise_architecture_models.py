"""
增强企业架构模型

Revision ID: 026
Revises: 025
Create Date: 2025-12-07

功能: 增强现有模型并添加新模型（组织架构、技术实例、技术类型等）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade():
    """增强企业架构模型"""
    print("=" * 50)
    print("增强企业架构模型")
    print("=" * 50)
    
    # ========== 1. 创建organization_units表 ==========
    print("创建 organization_units 表...")
    op.create_table(
        'organization_units',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='组织ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='组织名称'),
        sa.Column('code', sa.String(length=100), nullable=True, comment='组织编码'),
        sa.Column('description', sa.Text(), nullable=True, comment='组织描述'),
        sa.Column('organization_type', sa.String(length=100), nullable=True, comment='组织类型'),
        sa.Column('level', sa.Integer(), nullable=True, server_default='1', comment='组织层级'),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True, comment='上级组织ID'),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), nullable=True, comment='负责人ID'),
        sa.Column('location', sa.String(length=255), nullable=True, comment='地理位置'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active', comment='状态'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['organization_units.id'], name='fk_organization_units_parent_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], name='fk_organization_units_manager_id', ondelete='SET NULL'),
        comment='组织单元表'
    )
    op.create_index('ix_organization_units_name', 'organization_units', ['name'], unique=False)
    op.create_index('ix_organization_units_code', 'organization_units', ['code'], unique=True)
    op.create_index('ix_organization_units_status', 'organization_units', ['status'], unique=False)
    op.create_index('ix_organization_units_type', 'organization_units', ['organization_type'], unique=False)
    op.create_index('ix_organization_units_parent_id', 'organization_units', ['parent_id'], unique=False)
    print("✅ organization_units 表已创建")
    
    # ========== 2. 创建business_roles表 ==========
    print("创建 business_roles 表...")
    op.create_table(
        'business_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='角色ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='角色名称'),
        sa.Column('code', sa.String(length=100), nullable=True, comment='角色编码'),
        sa.Column('description', sa.Text(), nullable=True, comment='角色描述'),
        sa.Column('role_type', sa.String(length=100), nullable=True, comment='角色类型'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属组织ID'),
        sa.Column('responsibilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='职责列表'),
        sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='所需技能'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organization_units.id'], name='fk_business_roles_organization_id', ondelete='SET NULL'),
        comment='业务角色表'
    )
    op.create_index('ix_business_roles_name', 'business_roles', ['name'], unique=False)
    op.create_index('ix_business_roles_code', 'business_roles', ['code'], unique=True)
    op.create_index('ix_business_roles_organization_id', 'business_roles', ['organization_id'], unique=False)
    print("✅ business_roles 表已创建")
    
    # ========== 3. 创建technology_types表 ==========
    print("创建 technology_types 表...")
    op.create_table(
        'technology_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='类型ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='技术名称'),
        sa.Column('category', sa.String(length=100), nullable=False, comment='技术类别'),
        sa.Column('description', sa.Text(), nullable=True, comment='技术描述'),
        sa.Column('standard_version', sa.String(length=50), nullable=True, comment='企业标准版本'),
        sa.Column('recommended_version', sa.String(length=50), nullable=True, comment='推荐版本'),
        sa.Column('lifecycle_status', sa.String(length=50), nullable=True, server_default='strategic', comment='生命周期状态'),
        sa.Column('owner_team', sa.String(length=255), nullable=True, comment='技术负责人团队'),
        sa.Column('governance_status', sa.String(length=50), nullable=True, comment='治理状态'),
        sa.Column('usage_guidelines', sa.Text(), nullable=True, comment='使用指南'),
        sa.Column('instance_count', sa.Integer(), nullable=True, server_default='0', comment='实例数量'),
        sa.Column('version_diversity', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='版本多样性统计'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_technology_types_name'),
        comment='技术类型表'
    )
    op.create_index('ix_technology_types_category', 'technology_types', ['category'], unique=False)
    op.create_index('ix_technology_types_lifecycle', 'technology_types', ['lifecycle_status'], unique=False)
    print("✅ technology_types 表已创建")
    
    # ========== 4. 创建technology_instances表 ==========
    print("创建 technology_instances 表...")
    op.create_table(
        'technology_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='实例ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='实例名称'),
        sa.Column('instance_id', sa.String(length=255), nullable=True, comment='实例标识'),
        sa.Column('application_system_id', postgresql.UUID(as_uuid=True), nullable=True, comment='归属应用系统ID'),
        sa.Column('owner_department', sa.String(length=255), nullable=True, comment='负责部门'),
        sa.Column('owner_team', sa.String(length=255), nullable=True, comment='负责团队'),
        sa.Column('technology_type', sa.String(length=100), nullable=False, comment='技术类型'),
        sa.Column('technology_name', sa.String(length=255), nullable=False, comment='技术名称'),
        sa.Column('technology_type_id', postgresql.UUID(as_uuid=True), nullable=True, comment='关联技术类型ID'),
        sa.Column('vendor', sa.String(length=255), nullable=True, comment='供应商'),
        sa.Column('version', sa.String(length=50), nullable=True, comment='版本'),
        sa.Column('deployment_type', sa.String(length=50), nullable=True, server_default='independent', comment='部署类型'),
        sa.Column('host', sa.String(length=255), nullable=True, comment='主机地址'),
        sa.Column('port', sa.Integer(), nullable=True, comment='端口'),
        sa.Column('location', sa.String(length=255), nullable=True, comment='部署位置'),
        sa.Column('capacity', sa.String(length=100), nullable=True, comment='容量'),
        sa.Column('resource_allocation', sa.String(length=50), nullable=True, server_default='dedicated', comment='资源分配'),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='active', comment='状态'),
        sa.Column('lifecycle_status', sa.String(length=50), nullable=True, comment='生命周期状态'),
        sa.Column('neo4j_node_id', sa.String(length=255), nullable=True, comment='Neo4j节点ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['application_system_id'], ['application_systems.id'], name='fk_technology_instances_application_system_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['technology_type_id'], ['technology_types.id'], name='fk_technology_instances_technology_type_id', ondelete='SET NULL'),
        comment='技术实例表'
    )
    op.create_index('ix_technology_instances_name', 'technology_instances', ['name'], unique=False)
    op.create_index('ix_technology_instances_instance_id', 'technology_instances', ['instance_id'], unique=True)
    op.create_index('ix_technology_instances_app', 'technology_instances', ['application_system_id'], unique=False)
    op.create_index('ix_technology_instances_tech', 'technology_instances', ['technology_name', 'technology_type'], unique=False)
    op.create_index('ix_technology_instances_type', 'technology_instances', ['technology_type_id'], unique=False)
    op.create_index('ix_technology_instances_deployment', 'technology_instances', ['deployment_type'], unique=False)
    print("✅ technology_instances 表已创建")
    
    # ========== 5. 创建organization_business_relationships表 ==========
    print("创建 organization_business_relationships 表...")
    op.create_table(
        'organization_business_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='关系ID'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, comment='组织ID'),
        sa.Column('entity_type', sa.String(length=100), nullable=False, comment='实体类型'),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False, comment='实体ID'),
        sa.Column('relationship_type', sa.String(length=100), nullable=False, comment='关系类型'),
        sa.Column('responsibility_level', sa.String(length=50), nullable=True, comment='责任级别'),
        sa.Column('neo4j_relationship_id', sa.String(length=255), nullable=True, comment='Neo4j关系ID'),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}', comment='扩展元数据'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organization_units.id'], name='fk_org_business_rel_org_id', ondelete='CASCADE'),
        comment='组织与业务关系表'
    )
    op.create_index('ix_org_business_rel_org', 'organization_business_relationships', ['organization_id'], unique=False)
    op.create_index('ix_org_business_rel_entity', 'organization_business_relationships', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_org_business_rel_type', 'organization_business_relationships', ['relationship_type'], unique=False)
    print("✅ organization_business_relationships 表已创建")
    
    # ========== 6. 增强business_processes表 ==========
    print("增强 business_processes 表...")
    op.add_column('business_processes', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True, comment='负责组织ID'))
    op.create_index('ix_business_processes_organization_id', 'business_processes', ['organization_id'], unique=False)
    op.create_foreign_key('fk_business_processes_organization_id', 'business_processes', 'organization_units', ['organization_id'], ['id'], ondelete='SET NULL')
    print("✅ business_processes 表已增强")
    
    # ========== 7. 增强business_capabilities表 ==========
    print("增强 business_capabilities 表...")
    op.add_column('business_capabilities', sa.Column('owner_organization_id', postgresql.UUID(as_uuid=True), nullable=True, comment='拥有组织ID'))
    op.create_index('ix_business_capabilities_owner_org_id', 'business_capabilities', ['owner_organization_id'], unique=False)
    op.create_foreign_key('fk_business_capabilities_owner_org_id', 'business_capabilities', 'organization_units', ['owner_organization_id'], ['id'], ondelete='SET NULL')
    print("✅ business_capabilities 表已增强")
    
    # ========== 8. 增强application_systems表 ==========
    print("增强 application_systems 表...")
    op.add_column('application_systems', sa.Column('system_category', sa.String(length=50), nullable=True, comment='系统分类: Core, Peripheral, Custom'))
    op.add_column('application_systems', sa.Column('business_owner_org_id', postgresql.UUID(as_uuid=True), nullable=True, comment='业务拥有组织ID'))
    op.create_index('ix_application_systems_category', 'application_systems', ['system_category'], unique=False)
    op.create_index('ix_application_systems_business_owner_org_id', 'application_systems', ['business_owner_org_id'], unique=False)
    op.create_foreign_key('fk_application_systems_business_owner_org_id', 'application_systems', 'organization_units', ['business_owner_org_id'], ['id'], ondelete='SET NULL')
    print("✅ application_systems 表已增强")
    
    # ========== 9. 增强data_entities表 ==========
    print("增强 data_entities 表...")
    op.add_column('data_entities', sa.Column('code', sa.String(length=100), nullable=True, comment='实体编码'))
    op.add_column('data_entities', sa.Column('schema_name', sa.String(length=255), nullable=True, comment='Schema名称'))
    op.add_column('data_entities', sa.Column('table_name', sa.String(length=255), nullable=True, comment='表名'))
    op.add_column('data_entities', sa.Column('application_system_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属应用系统ID'))
    op.add_column('data_entities', sa.Column('technology_system_id', postgresql.UUID(as_uuid=True), nullable=True, comment='存储的技术系统ID'))
    op.add_column('data_entities', sa.Column('data_model_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属数据模型ID'))
    op.create_index('ix_data_entities_code', 'data_entities', ['code'], unique=True)
    op.create_index('ix_data_entities_table_name', 'data_entities', ['table_name'], unique=False)
    op.create_index('ix_data_entities_application_system_id', 'data_entities', ['application_system_id'], unique=False)
    op.create_index('ix_data_entities_technology_system_id', 'data_entities', ['technology_system_id'], unique=False)
    op.create_foreign_key('fk_data_entities_application_system_id', 'data_entities', 'application_systems', ['application_system_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_data_entities_technology_system_id', 'data_entities', 'technology_instances', ['technology_system_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_data_entities_data_model_id', 'data_entities', 'data_models', ['data_model_id'], ['id'], ondelete='SET NULL')
    print("✅ data_entities 表已增强")
    
    # ========== 10. 增强api_interfaces表 ==========
    print("增强 api_interfaces 表...")
    op.add_column('api_interfaces', sa.Column('code', sa.String(length=100), nullable=True, comment='接口编码'))
    op.add_column('api_interfaces', sa.Column('interface_type', sa.String(length=100), nullable=True, comment='接口类型'))
    op.add_column('api_interfaces', sa.Column('endpoint', sa.String(length=500), nullable=True, comment='接口端点'))
    op.add_column('api_interfaces', sa.Column('application_system_id', postgresql.UUID(as_uuid=True), nullable=True, comment='所属应用系统ID'))
    op.add_column('api_interfaces', sa.Column('name', sa.String(length=255), nullable=True, comment='接口名称'))
    op.create_index('ix_api_interfaces_code', 'api_interfaces', ['code'], unique=True)
    op.create_index('ix_api_interfaces_interface_type', 'api_interfaces', ['interface_type'], unique=False)
    op.create_index('ix_api_interfaces_application_system_id', 'api_interfaces', ['application_system_id'], unique=False)
    op.create_foreign_key('fk_api_interfaces_application_system_id', 'api_interfaces', 'application_systems', ['application_system_id'], ['id'], ondelete='SET NULL')
    print("✅ api_interfaces 表已增强")
    
    print("=" * 50)
    print("✅ 所有表创建和增强完成")
    print("=" * 50)


def downgrade():
    """回滚增强"""
    print("=" * 50)
    print("回滚企业架构模型增强")
    print("=" * 50)
    
    # 删除增强的字段
    op.drop_constraint('fk_api_interfaces_application_system_id', 'api_interfaces', type_='foreignkey')
    op.drop_index('ix_api_interfaces_application_system_id', 'api_interfaces')
    op.drop_index('ix_api_interfaces_interface_type', 'api_interfaces')
    op.drop_index('ix_api_interfaces_code', 'api_interfaces')
    op.drop_column('api_interfaces', 'name')
    op.drop_column('api_interfaces', 'application_system_id')
    op.drop_column('api_interfaces', 'endpoint')
    op.drop_column('api_interfaces', 'interface_type')
    op.drop_column('api_interfaces', 'code')
    
    op.drop_constraint('fk_data_entities_data_model_id', 'data_entities', type_='foreignkey')
    op.drop_constraint('fk_data_entities_technology_system_id', 'data_entities', type_='foreignkey')
    op.drop_constraint('fk_data_entities_application_system_id', 'data_entities', type_='foreignkey')
    op.drop_index('ix_data_entities_technology_system_id', 'data_entities')
    op.drop_index('ix_data_entities_application_system_id', 'data_entities')
    op.drop_index('ix_data_entities_table_name', 'data_entities')
    op.drop_index('ix_data_entities_code', 'data_entities')
    op.drop_column('data_entities', 'data_model_id')
    op.drop_column('data_entities', 'technology_system_id')
    op.drop_column('data_entities', 'application_system_id')
    op.drop_column('data_entities', 'table_name')
    op.drop_column('data_entities', 'schema_name')
    op.drop_column('data_entities', 'code')
    
    op.drop_constraint('fk_application_systems_business_owner_org_id', 'application_systems', type_='foreignkey')
    op.drop_index('ix_application_systems_business_owner_org_id', 'application_systems')
    op.drop_index('ix_application_systems_category', 'application_systems')
    op.drop_column('application_systems', 'business_owner_org_id')
    op.drop_column('application_systems', 'system_category')
    
    op.drop_constraint('fk_business_capabilities_owner_org_id', 'business_capabilities', type_='foreignkey')
    op.drop_index('ix_business_capabilities_owner_org_id', 'business_capabilities')
    op.drop_column('business_capabilities', 'owner_organization_id')
    
    op.drop_constraint('fk_business_processes_organization_id', 'business_processes', type_='foreignkey')
    op.drop_index('ix_business_processes_organization_id', 'business_processes')
    op.drop_column('business_processes', 'organization_id')
    
    # 删除新增的表
    op.drop_table('organization_business_relationships')
    op.drop_table('technology_instances')
    op.drop_table('technology_types')
    op.drop_table('business_roles')
    op.drop_table('organization_units')
    
    print("✅ 回滚完成")


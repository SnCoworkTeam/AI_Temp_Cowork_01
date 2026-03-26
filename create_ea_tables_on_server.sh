#!/bin/bash
# 在服务器上创建企业架构表的脚本

cd /opt/enterprise-ai-platform

# 使用docker exec在postgres容器中执行SQL
docker compose exec -T postgres psql -U ai_user -d ai_platform <<EOF

-- 创建业务架构表
CREATE TABLE IF NOT EXISTS business_processes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    classification VARCHAR(100),
    level INTEGER DEFAULT 1,
    parent_id UUID REFERENCES business_processes(id) ON DELETE SET NULL,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_business_processes_name ON business_processes(name);
CREATE INDEX IF NOT EXISTS ix_business_processes_status ON business_processes(status);
CREATE INDEX IF NOT EXISTS ix_business_processes_parent_id ON business_processes(parent_id);

CREATE TABLE IF NOT EXISTS business_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    level INTEGER DEFAULT 1,
    parent_id UUID REFERENCES business_capabilities(id) ON DELETE SET NULL,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_business_capabilities_name ON business_capabilities(name);
CREATE INDEX IF NOT EXISTS ix_business_capabilities_parent_id ON business_capabilities(parent_id);

CREATE TABLE IF NOT EXISTS business_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    service_type VARCHAR(100),
    endpoint VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_business_services_name ON business_services(name);
CREATE INDEX IF NOT EXISTS ix_business_services_status ON business_services(status);

-- 创建应用架构表
CREATE TABLE IF NOT EXISTS application_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_type VARCHAR(100),
    vendor VARCHAR(255),
    version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    owner VARCHAR(255),
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_application_systems_name ON application_systems(name);
CREATE INDEX IF NOT EXISTS ix_application_systems_status ON application_systems(status);

CREATE TABLE IF NOT EXISTS application_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES application_systems(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    service_type VARCHAR(100),
    protocol VARCHAR(50),
    endpoint VARCHAR(500),
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_application_services_application_id ON application_services(application_id);
CREATE INDEX IF NOT EXISTS ix_application_services_name ON application_services(name);

CREATE TABLE IF NOT EXISTS api_interfaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES application_services(id) ON DELETE CASCADE,
    path VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    description TEXT,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_api_interfaces_service_id ON api_interfaces(service_id);
CREATE INDEX IF NOT EXISTS ix_api_interfaces_path_method ON api_interfaces(path, method);

-- 创建数据架构表
CREATE TABLE IF NOT EXISTS data_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schema JSONB,
    entity_type VARCHAR(100),
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_data_entities_name ON data_entities(name);

CREATE TABLE IF NOT EXISTS data_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    definition JSONB,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_data_models_name ON data_models(name);

CREATE TABLE IF NOT EXISTS data_flows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_entity_id UUID REFERENCES data_entities(id) ON DELETE SET NULL,
    target_entity_id UUID REFERENCES data_entities(id) ON DELETE SET NULL,
    transformation TEXT,
    neo4j_relationship_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_data_flows_source_entity_id ON data_flows(source_entity_id);
CREATE INDEX IF NOT EXISTS ix_data_flows_target_entity_id ON data_flows(target_entity_id);

-- 创建技术架构表
CREATE TABLE IF NOT EXISTS technology_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    component_type VARCHAR(100),
    version VARCHAR(50),
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_technology_components_name ON technology_components(name);

CREATE TABLE IF NOT EXISTS technology_stacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    components JSONB,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_technology_stacks_name ON technology_stacks(name);

CREATE TABLE IF NOT EXISTS infrastructure_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    component_type VARCHAR(100),
    specifications JSONB,
    neo4j_node_id VARCHAR(255),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_infrastructure_components_name ON infrastructure_components(name);

-- 创建架构关系表
CREATE TABLE IF NOT EXISTS architecture_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    description TEXT,
    neo4j_relationship_id VARCHAR(255),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_architecture_relationships_source ON architecture_relationships(source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_architecture_relationships_target ON architecture_relationships(target_type, target_id);
CREATE INDEX IF NOT EXISTS ix_architecture_relationships_type ON architecture_relationships(relationship_type);

EOF

echo "企业架构表创建完成！"


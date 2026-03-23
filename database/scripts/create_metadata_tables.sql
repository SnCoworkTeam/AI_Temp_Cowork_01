-- 创建元数据表：ai_models, data_assets, business_entities

-- 创建枚举类型
DO $$ BEGIN
    CREATE TYPE modeltype AS ENUM ('llm', 'embedding', 'classification', 'regression', 'clustering', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE modelstatus AS ENUM ('training', 'active', 'deprecated', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE dataassettype AS ENUM ('dataset', 'table', 'view', 'file', 'stream', 'api');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE dataassetstatus AS ENUM ('active', 'deprecated', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE entitytype AS ENUM ('domain', 'concept', 'term', 'glossary', 'policy', 'rule');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建 ai_models 表
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    model_type modeltype NOT NULL,
    status modelstatus NOT NULL DEFAULT 'active',
    model_version VARCHAR(50),
    framework VARCHAR(100),
    model_path VARCHAR(500),
    model_size INTEGER,
    training_dataset VARCHAR(255),
    training_config JSONB,
    hyperparameters JSONB,
    training_metrics JSONB,
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    performance_metrics JSONB,
    deployment_endpoint VARCHAR(500),
    deployment_config JSONB,
    inference_latency FLOAT,
    business_owner VARCHAR(100),
    technical_owner VARCHAR(100),
    tags JSONB,
    use_cases JSONB,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 创建 data_assets 表
CREATE TABLE IF NOT EXISTS data_assets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    asset_type dataassettype NOT NULL,
    status dataassetstatus NOT NULL DEFAULT 'active',
    source_system VARCHAR(100),
    source_path VARCHAR(500),
    source_connection VARCHAR(255),
    schema_info JSONB,
    sample_data JSONB,
    data_quality_metrics JSONB,
    business_owner VARCHAR(100),
    technical_owner VARCHAR(100),
    tags JSONB,
    classification VARCHAR(50),
    record_count INTEGER,
    size_bytes INTEGER,
    last_updated TIMESTAMP,
    update_frequency VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 创建 business_entities 表
CREATE TABLE IF NOT EXISTS business_entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    entity_type entitytype NOT NULL,
    parent_id INTEGER REFERENCES business_entities(id),
    business_definition TEXT,
    business_rules JSONB,
    data_dictionary JSONB,
    related_entities JSONB,
    related_data_assets JSONB,
    related_models JSONB,
    data_steward VARCHAR(100),
    business_owner VARCHAR(100),
    classification VARCHAR(50),
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ai_models_name ON ai_models(name);
CREATE INDEX IF NOT EXISTS idx_ai_models_type_status ON ai_models(model_type, status);
CREATE INDEX IF NOT EXISTS idx_data_assets_name ON data_assets(name);
CREATE INDEX IF NOT EXISTS idx_data_assets_type_status ON data_assets(asset_type, status);
CREATE INDEX IF NOT EXISTS idx_business_entities_name ON business_entities(name);
CREATE INDEX IF NOT EXISTS idx_business_entities_type ON business_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_business_entities_parent ON business_entities(parent_id);



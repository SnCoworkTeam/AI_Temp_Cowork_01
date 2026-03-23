-- 创建workflow_metadata表和添加classification_dimensions列的SQL脚本
-- 用于在43服务器上手动执行

-- 1. 创建workflowstatus枚举类型（如果不存在）
DO $$ BEGIN
    CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'deprecated', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. 创建workflow_metadata表（如果不存在）
CREATE TABLE IF NOT EXISTS workflow_metadata (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    status workflowstatus NOT NULL DEFAULT 'active',
    version VARCHAR(50),
    category VARCHAR(100),
    workflow_type VARCHAR(50),
    definition JSONB,
    input_schema JSONB,
    output_schema JSONB,
    execution_count INTEGER DEFAULT 0,
    last_execution_time TIMESTAMP,
    average_execution_time INTEGER,
    success_rate VARCHAR(10),
    dependencies JSONB,
    data_sources JSONB,
    data_sinks JSONB,
    business_owner VARCHAR(100),
    technical_owner VARCHAR(100),
    tags JSONB,
    use_cases JSONB,
    classification_dimensions JSONB,
    standardized_tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_workflow_metadata_workflow_id ON workflow_metadata(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_metadata_name ON workflow_metadata(name);
CREATE INDEX IF NOT EXISTS idx_workflow_metadata_status ON workflow_metadata(status);

-- 4. 为data_assets表添加classification_dimensions列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'data_assets' AND column_name = 'classification_dimensions'
    ) THEN
        ALTER TABLE data_assets ADD COLUMN classification_dimensions JSONB;
    END IF;
END $$;

-- 5. 为data_assets表添加standardized_tags列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'data_assets' AND column_name = 'standardized_tags'
    ) THEN
        ALTER TABLE data_assets ADD COLUMN standardized_tags JSONB;
    END IF;
END $$;

-- 6. 为ai_models表添加classification_dimensions列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ai_models' AND column_name = 'classification_dimensions'
    ) THEN
        ALTER TABLE ai_models ADD COLUMN classification_dimensions JSONB;
    END IF;
END $$;

-- 7. 为ai_models表添加standardized_tags列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ai_models' AND column_name = 'standardized_tags'
    ) THEN
        ALTER TABLE ai_models ADD COLUMN standardized_tags JSONB;
    END IF;
END $$;

-- 8. 为business_entities表添加classification_dimensions列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'business_entities' AND column_name = 'classification_dimensions'
    ) THEN
        ALTER TABLE business_entities ADD COLUMN classification_dimensions JSONB;
    END IF;
END $$;

-- 9. 为business_entities表添加standardized_tags列（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'business_entities' AND column_name = 'standardized_tags'
    ) THEN
        ALTER TABLE business_entities ADD COLUMN standardized_tags JSONB;
    END IF;
END $$;

-- 10. 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_data_assets_business_domain 
    ON data_assets USING gin ((classification_dimensions->'business'->>'domain'));

CREATE INDEX IF NOT EXISTS idx_data_assets_technical_source 
    ON data_assets USING gin ((classification_dimensions->'technical'->>'source'));

CREATE INDEX IF NOT EXISTS idx_data_assets_standardized_tags 
    ON data_assets USING gin (standardized_tags);

CREATE INDEX IF NOT EXISTS idx_workflow_business_domain 
    ON workflow_metadata USING gin ((classification_dimensions->'business'->>'domain'));

CREATE INDEX IF NOT EXISTS idx_workflow_standardized_tags 
    ON workflow_metadata USING gin (standardized_tags);

-- 验证
SELECT 'workflow_metadata表已创建' AS status;
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='workflow_metadata';
SELECT column_name FROM information_schema.columns WHERE table_name='data_assets' AND column_name='classification_dimensions';





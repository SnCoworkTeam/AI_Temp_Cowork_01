-- 删除之前创建失败的表
DROP TABLE IF EXISTS agent_execution_records CASCADE;
DROP TABLE IF EXISTS agent_contexts CASCADE;
DROP TABLE IF EXISTS agent_nodes CASCADE;
DROP TABLE IF EXISTS agent_registry CASCADE;

-- 创建Agent相关的枚举类型
DO $$ BEGIN
    CREATE TYPE agenttype AS ENUM ('conversational', 'tool_calling', 'reasoning', 'planning', 'code_generation', 'data_analysis', 'document_processing');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE agentstatus AS ENUM ('active', 'inactive', 'training', 'deprecated', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE agentexecutionstate AS ENUM ('pending', 'running', 'thinking', 'calling_tools', 'waiting_for_input', 'completed', 'failed', 'timeout', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE conversationrole AS ENUM ('system', 'user', 'assistant', 'function', 'tool');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建 agent_registry 表
CREATE TABLE agent_registry (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    agent_type agenttype NOT NULL,
    status agentstatus NOT NULL DEFAULT 'inactive',
    version VARCHAR NOT NULL DEFAULT '1.0.0',

    personality_name VARCHAR NOT NULL,
    personality_description TEXT NOT NULL,
    personality_traits JSONB NOT NULL DEFAULT '[]',
    communication_style VARCHAR NOT NULL DEFAULT 'professional',
    expertise_areas JSONB NOT NULL DEFAULT '[]',
    limitations JSONB NOT NULL DEFAULT '[]',

    capabilities JSONB NOT NULL DEFAULT '[]',

    model VARCHAR NOT NULL,
    temperature FLOAT NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 2048,
    top_p FLOAT NOT NULL DEFAULT 1.0,
    frequency_penalty FLOAT NOT NULL DEFAULT 0.0,
    presence_penalty FLOAT NOT NULL DEFAULT 0.0,
    timeout INTEGER NOT NULL DEFAULT 300,
    max_tool_calls INTEGER NOT NULL DEFAULT 10,
    enable_memory BOOLEAN NOT NULL DEFAULT TRUE,
    memory_size INTEGER NOT NULL DEFAULT 20,

    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL DEFAULT '{input}',

    available_tools JSONB NOT NULL DEFAULT '[]',
    required_permissions JSONB NOT NULL DEFAULT '[]',

    tags JSONB NOT NULL DEFAULT '[]',
    category VARCHAR NOT NULL DEFAULT 'general',
    author VARCHAR NOT NULL,
    created_by VARCHAR NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,

    usage_count INTEGER NOT NULL DEFAULT 0,
    success_rate FLOAT NOT NULL DEFAULT 0.0,
    average_execution_time FLOAT NOT NULL DEFAULT 0.0
);

-- 创建 agent_nodes 表 (注意: workflow_id 改为 UUID 类型)
CREATE TABLE agent_nodes (
    id VARCHAR PRIMARY KEY,
    workflow_id UUID NOT NULL REFERENCES workflow_definitions(id),
    agent_id VARCHAR NOT NULL REFERENCES agent_registry(id),
    node_name VARCHAR NOT NULL,
    description TEXT,

    position JSONB,
    size JSONB,
    style JSONB,

    input_mapping JSONB NOT NULL DEFAULT '{}',
    output_mapping JSONB NOT NULL DEFAULT '{}',

    retry_count INTEGER NOT NULL DEFAULT 3,
    retry_delay INTEGER NOT NULL DEFAULT 5,
    enable_streaming BOOLEAN NOT NULL DEFAULT FALSE,

    context_window_size INTEGER NOT NULL DEFAULT 10,
    preserve_conversation BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建 agent_contexts 表
CREATE TABLE agent_contexts (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL REFERENCES agent_registry(id),
    node_id VARCHAR NOT NULL REFERENCES agent_nodes(id),

    current_state agentexecutionstate NOT NULL DEFAULT 'pending',
    variables JSONB NOT NULL DEFAULT '{}',
    shared_memory JSONB NOT NULL DEFAULT '{}',

    execution_count INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_execution_time FLOAT NOT NULL DEFAULT 0.0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,

    UNIQUE(conversation_id, agent_id, node_id)
);

-- 创建 agent_execution_records 表 (注意: workflow_id 改为 UUID 类型)
CREATE TABLE agent_execution_records (
    id VARCHAR PRIMARY KEY,
    agent_id VARCHAR NOT NULL REFERENCES agent_registry(id),
    node_id VARCHAR NOT NULL REFERENCES agent_nodes(id),
    workflow_id UUID NOT NULL REFERENCES workflow_definitions(id),
    execution_id VARCHAR NOT NULL,

    input_data JSONB NOT NULL,
    output_data JSONB,

    state agentexecutionstate NOT NULL,
    error_message TEXT,
    error_code VARCHAR,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    execution_time FLOAT,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    tool_calls_count INTEGER NOT NULL DEFAULT 0,

    success BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score FLOAT,
    user_feedback TEXT,

    meta_info JSONB NOT NULL DEFAULT '{}'
);

-- 创建索引
CREATE INDEX idx_agent_registry_name ON agent_registry(name);
CREATE INDEX idx_agent_registry_type ON agent_registry(agent_type);
CREATE INDEX idx_agent_registry_status ON agent_registry(status);
CREATE INDEX idx_agent_nodes_workflow_id ON agent_nodes(workflow_id);
CREATE INDEX idx_agent_nodes_agent_id ON agent_nodes(agent_id);
CREATE INDEX idx_agent_contexts_conversation_id ON agent_contexts(conversation_id);
CREATE INDEX idx_agent_contexts_agent_id ON agent_contexts(agent_id);
CREATE INDEX idx_agent_execution_records_agent_id ON agent_execution_records(agent_id);
CREATE INDEX idx_agent_execution_records_workflow_id ON agent_execution_records(workflow_id);

-- 更新alembic版本
UPDATE alembic_version SET version_num = '009_add_agent_tables';

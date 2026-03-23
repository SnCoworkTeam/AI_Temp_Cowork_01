-- ============================================
-- 数据库初始化脚本 - 基础表结构
-- ============================================
-- 此脚本在数据库首次创建时自动执行
-- 注意：实际表结构由Alembic迁移管理，此脚本主要用于：
-- 1. 创建PostgreSQL扩展
-- 2. 设置数据库参数
-- 3. 创建必要的函数和类型

-- 启用必要的PostgreSQL扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 用于模糊搜索
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- 用于性能监控

-- 设置时区
SET timezone = 'UTC';

-- 创建枚举类型（如果不存在）
-- 注意：这些类型通常由Alembic迁移创建，这里仅作为备份

-- 用户状态枚举
DO $$ BEGIN
    CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 工作流状态枚举
DO $$ BEGIN
    CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'inactive', 'archived');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 执行状态枚举
DO $$ BEGIN
    CREATE TYPE executionstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 节点类型枚举
DO $$ BEGIN
    CREATE TYPE nodetype AS ENUM (
        'start', 'end', 'llm', 'tool', 'condition', 'transform', 
        'http', 'delay', 'log', 'knowledge_search', 
        'document_processing', 'knowledge_enhancement'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 文档类型枚举
DO $$ BEGIN
    CREATE TYPE documenttype AS ENUM ('pdf', 'word', 'excel', 'text', 'markdown', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 文档状态枚举
DO $$ BEGIN
    CREATE TYPE documentstatus AS ENUM ('uploading', 'processing', 'processed', 'failed', 'deleted');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 配置类别枚举
DO $$ BEGIN
    CREATE TYPE configcategory AS ENUM ('system', 'feature', 'integration', 'security', 'performance');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 审计操作类型枚举
DO $$ BEGIN
    CREATE TYPE auditaction AS ENUM (
        'create', 'read', 'update', 'delete', 'execute', 
        'login', 'logout', 'permission_denied'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建审计日志触发器函数（可选）
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    -- 这里可以添加自动审计日志逻辑
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 设置数据库默认权限（用户需与 docker-compose 中 DB_USER/POSTGRES_USER 一致，默认 ai_user）
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ai_user;

-- 输出初始化完成信息
DO $$
BEGIN
    RAISE NOTICE '数据库初始化脚本执行完成';
    RAISE NOTICE '已创建必要的扩展和枚举类型';
    RAISE NOTICE '请运行Alembic迁移以创建表结构';
END $$;










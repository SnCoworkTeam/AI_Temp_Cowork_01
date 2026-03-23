-- Fix workflow schema inconsistencies
-- 修复workflow_definitions表的schema不一致问题
-- Date: 2025-11-14

\echo '=================================================='
\echo '开始修复workflow_definitions Schema'
\echo '=================================================='

-- 1. 修改version字段从integer改为VARCHAR(50)
\echo '修改workflow_definitions.version字段类型...'

ALTER TABLE workflow_definitions
ALTER COLUMN version TYPE VARCHAR(50)
USING version::text;

ALTER TABLE workflow_definitions
ALTER COLUMN version SET DEFAULT '1.0.0';

\echo '✅ version字段已从integer修改为VARCHAR(50)'

-- 2. 验证并修复status枚举类型
\echo '验证workflow_definitions.status枚举...'

-- 临时将status改为VARCHAR以便修改枚举
ALTER TABLE workflow_definitions ALTER COLUMN status TYPE VARCHAR(50);

-- 删除旧枚举
DROP TYPE IF EXISTS workflowstatus CASCADE;

-- 重新创建枚举
CREATE TYPE workflowstatus AS ENUM ('draft', 'active', 'inactive', 'archived');

-- 将status列改回枚举类型
ALTER TABLE workflow_definitions
ALTER COLUMN status TYPE workflowstatus
USING status::workflowstatus;

-- 设置默认值
ALTER TABLE workflow_definitions
ALTER COLUMN status SET DEFAULT 'draft'::workflowstatus;

\echo '✅ status枚举已修复'

-- 3. 确保config和workflow_metadata是JSONB类型且有默认值
\echo '验证JSONB字段...'

ALTER TABLE workflow_definitions
ALTER COLUMN config SET DEFAULT '{}'::jsonb;

ALTER TABLE workflow_definitions
ALTER COLUMN workflow_metadata SET DEFAULT '{}'::jsonb;

\echo '✅ JSONB字段已验证'

-- 4. 创建必要的索引
\echo '创建必要的索引...'

CREATE INDEX IF NOT EXISTS ix_workflow_definitions_version
ON workflow_definitions(version);

CREATE INDEX IF NOT EXISTS ix_workflow_definitions_status
ON workflow_definitions(status);

CREATE INDEX IF NOT EXISTS ix_workflow_definitions_created_at
ON workflow_definitions(created_at DESC);

\echo '✅ 索引已创建'

-- 5. 验证修改
\echo '=================================================='
\echo '验证修改结果...'
\echo '=================================================='

\d workflow_definitions

\echo '=================================================='
\echo '✅ Schema修复完成！'
\echo '=================================================='

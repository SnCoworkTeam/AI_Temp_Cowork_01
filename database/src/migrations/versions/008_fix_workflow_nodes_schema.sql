-- Fix workflow_nodes schema inconsistencies
-- 修复workflow_nodes表的schema不一致问题
-- Date: 2025-11-14

\echo '=================================================='
\echo '开始修复workflow_nodes Schema'
\echo '=================================================='

-- 1. 添加缺失的description字段
\echo '添加description字段...'
ALTER TABLE workflow_nodes
ADD COLUMN IF NOT EXISTS description TEXT;

\echo '✅ description字段已添加'

-- 2. 添加position字段（JSONB格式）并迁移旧数据
\echo '添加position (JSONB)字段...'
ALTER TABLE workflow_nodes
ADD COLUMN IF NOT EXISTS position JSONB;

-- 迁移旧的position_x和position_y数据到position JSON
UPDATE workflow_nodes
SET position = jsonb_build_object('x', position_x, 'y', position_y)
WHERE position_x IS NOT NULL OR position_y IS NOT NULL;

\echo '✅ position字段已添加并迁移数据'

-- 3. 添加style字段
\echo '添加style字段...'
ALTER TABLE workflow_nodes
ADD COLUMN IF NOT EXISTS style JSONB;

\echo '✅ style字段已添加'

-- 4. 可选：删除旧的position_x和position_y字段（如果不再需要）
-- 暂时保留这些字段以保持向后兼容性
-- ALTER TABLE workflow_nodes DROP COLUMN IF EXISTS position_x;
-- ALTER TABLE workflow_nodes DROP COLUMN IF EXISTS position_y;

\echo '=================================================='
\echo '验证修改结果...'
\echo '=================================================='

\d workflow_nodes

\echo '=================================================='
\echo '✅ workflow_nodes Schema修复完成！'
\echo '=================================================='

-- 修复 workflow_executions 表，添加缺失的列
-- 执行: docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < fix_workflow_executions.sql

-- 1. 添加 progress 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'progress'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN progress FLOAT NOT NULL DEFAULT 0.0;
        COMMENT ON COLUMN workflow_executions.progress IS '执行进度（0-1）';
        RAISE NOTICE '✅ progress 列已添加';
    ELSE
        RAISE NOTICE '⚠️  progress 列已存在，跳过';
    END IF;
END $$;

-- 2. 添加 current_node_id 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'current_node_id'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN current_node_id VARCHAR(100);
        COMMENT ON COLUMN workflow_executions.current_node_id IS '当前节点ID';
        RAISE NOTICE '✅ current_node_id 列已添加';
    ELSE
        RAISE NOTICE '⚠️  current_node_id 列已存在，跳过';
    END IF;
END $$;

-- 3. 添加 node_results 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'node_results'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN node_results JSONB;
        COMMENT ON COLUMN workflow_executions.node_results IS '节点执行结果';
        RAISE NOTICE '✅ node_results 列已添加';
    ELSE
        RAISE NOTICE '⚠️  node_results 列已存在，跳过';
    END IF;
END $$;

-- 4. 添加 start_time 列（如果 started_at 存在，同步数据）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'start_time'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN start_time TIMESTAMP;
        COMMENT ON COLUMN workflow_executions.start_time IS '开始时间';
        
        -- 如果 started_at 存在，同步数据
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' AND column_name = 'started_at'
        ) THEN
            UPDATE workflow_executions 
            SET start_time = started_at 
            WHERE started_at IS NOT NULL AND start_time IS NULL;
            RAISE NOTICE '✅ start_time 列已添加并同步数据';
        ELSE
            RAISE NOTICE '✅ start_time 列已添加';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  start_time 列已存在，跳过';
    END IF;
END $$;

-- 5. 添加 end_time 列（如果 finished_at 存在，同步数据）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'end_time'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN end_time TIMESTAMP;
        COMMENT ON COLUMN workflow_executions.end_time IS '结束时间';
        
        -- 如果 finished_at 存在，同步数据
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' AND column_name = 'finished_at'
        ) THEN
            UPDATE workflow_executions 
            SET end_time = finished_at 
            WHERE finished_at IS NOT NULL AND end_time IS NULL;
            RAISE NOTICE '✅ end_time 列已添加并同步数据';
        ELSE
            RAISE NOTICE '✅ end_time 列已添加';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  end_time 列已存在，跳过';
    END IF;
END $$;

-- 6. 添加 execution_time 列（如果 duration_seconds 存在，同步数据）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'execution_time'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN execution_time FLOAT;
        COMMENT ON COLUMN workflow_executions.execution_time IS '执行耗时（秒）';
        
        -- 如果 duration_seconds 存在，同步数据
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'workflow_executions' AND column_name = 'duration_seconds'
        ) THEN
            UPDATE workflow_executions 
            SET execution_time = duration_seconds 
            WHERE duration_seconds IS NOT NULL AND execution_time IS NULL;
            RAISE NOTICE '✅ execution_time 列已添加并同步数据';
        ELSE
            RAISE NOTICE '✅ execution_time 列已添加';
        END IF;
    ELSE
        RAISE NOTICE '⚠️  execution_time 列已存在，跳过';
    END IF;
END $$;

-- 7. 添加 execution_metadata 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' AND column_name = 'execution_metadata'
    ) THEN
        ALTER TABLE workflow_executions 
        ADD COLUMN execution_metadata JSONB DEFAULT '{}';
        COMMENT ON COLUMN workflow_executions.execution_metadata IS '执行元数据';
        RAISE NOTICE '✅ execution_metadata 列已添加';
    ELSE
        RAISE NOTICE '⚠️  execution_metadata 列已存在，跳过';
    END IF;
END $$;

SELECT '✅ workflow_executions 表修复完成' AS result;


-- ============================================
-- 数据库索引创建脚本
-- ============================================
-- 此脚本创建额外的性能优化索引
-- 注意：主要索引已在Alembic迁移中创建，这里补充一些复合索引和功能索引

DO $$
BEGIN
    -- 检查表是否存在
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users'
    ) THEN
        RAISE NOTICE '表尚未创建，跳过索引创建';
        RETURN;
    END IF;

    -- ============================================
    -- 用户相关索引
    -- ============================================
    
    -- 用户状态索引（用于筛选活跃用户）
    CREATE INDEX IF NOT EXISTS idx_users_status 
        ON users(status) 
        WHERE status = 'active';
    
    -- 用户最后登录时间索引（用于排序）
    CREATE INDEX IF NOT EXISTS idx_users_last_login 
        ON users(last_login_at DESC NULLS LAST);

    -- ============================================
    -- 工作流相关索引
    -- ============================================
    
    -- 工作流状态和创建者复合索引
    CREATE INDEX IF NOT EXISTS idx_workflow_definitions_status_creator 
        ON workflow_definitions(status, created_by);
    
    -- 工作流执行状态和时间索引
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_status_time 
        ON workflow_executions(status, created_at DESC);
    
    -- 工作流执行用户和时间索引
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_time 
        ON workflow_executions(executed_by, created_at DESC);
    
    -- 工作流节点工作流ID和节点ID索引
    CREATE INDEX IF NOT EXISTS idx_workflow_nodes_workflow_node 
        ON workflow_nodes(workflow_id, node_id);

    -- ============================================
    -- 知识库相关索引
    -- ============================================
    
    -- 文档状态和类型索引
    CREATE INDEX IF NOT EXISTS idx_documents_status_type 
        ON documents(status, file_type);
    
    -- 文档分类和状态索引
    CREATE INDEX IF NOT EXISTS idx_documents_category_status 
        ON documents(category, status) 
        WHERE category IS NOT NULL;
    
    -- 文档上传者和时间索引
    CREATE INDEX IF NOT EXISTS idx_documents_uploader_time 
        ON documents(uploaded_by, created_at DESC);
    
    -- 文档标题全文搜索索引（使用GIN索引）
    CREATE INDEX IF NOT EXISTS idx_documents_title_gin 
        ON documents USING gin(to_tsvector('english', COALESCE(title, '')));
    
    -- 文档块文档ID和索引复合索引
    CREATE INDEX IF NOT EXISTS idx_document_chunks_document_index 
        ON document_chunks(document_id, chunk_index);
    
    -- 知识图谱节点概念搜索索引
    CREATE INDEX IF NOT EXISTS idx_knowledge_graph_nodes_concept_trgm 
        ON knowledge_graph_nodes USING gin(concept gin_trgm_ops);
    
    -- 知识图谱边关系和权重索引
    CREATE INDEX IF NOT EXISTS idx_knowledge_graph_edges_relationship_weight 
        ON knowledge_graph_edges(relationship_type, weight DESC NULLS LAST);

    -- ============================================
    -- MCP工具相关索引
    -- ============================================
    
    -- MCP工具状态和类型索引
    CREATE INDEX IF NOT EXISTS idx_mcp_tools_active_type 
        ON mcp_tools(is_active, tool_type) 
        WHERE is_active = true;
    
    -- MCP工具执行状态和时间索引
    CREATE INDEX IF NOT EXISTS idx_mcp_tool_executions_status_time 
        ON mcp_tool_executions(success, created_at DESC);
    
    -- MCP工具执行用户和时间索引
    CREATE INDEX IF NOT EXISTS idx_mcp_tool_executions_user_time 
        ON mcp_tool_executions(executed_by, created_at DESC);

    -- ============================================
    -- 系统相关索引
    -- ============================================
    
    -- 系统配置分类索引
    CREATE INDEX IF NOT EXISTS idx_system_configs_category 
        ON system_configs(category);
    
    -- 审计日志用户和操作复合索引（已在迁移中创建，但这里确保存在）
    CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action 
        ON audit_logs(user_id, action);
    
    -- 审计日志资源类型和ID复合索引（已在迁移中创建）
    CREATE INDEX IF NOT EXISTS idx_audit_logs_resource 
        ON audit_logs(resource_type, resource_id);
    
    -- 审计日志时间索引（已在迁移中创建）
    CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
        ON audit_logs(timestamp DESC);
    
    -- 审计日志操作和时间复合索引
    CREATE INDEX IF NOT EXISTS idx_audit_logs_action_time 
        ON audit_logs(action, timestamp DESC);

    -- ============================================
    -- 用户会话相关索引
    -- ============================================
    
    -- 用户会话用户ID和过期时间索引
    CREATE INDEX IF NOT EXISTS idx_user_sessions_user_expires 
        ON user_sessions(user_id, expires_at);
    
    -- 用户会话活跃状态索引
    CREATE INDEX IF NOT EXISTS idx_user_sessions_active 
        ON user_sessions(is_active, expires_at) 
        WHERE is_active = true;

    -- ============================================
    -- 时间戳索引优化
    -- ============================================
    -- 为常用查询字段添加时间戳索引
    
    -- 用户创建时间索引
    CREATE INDEX IF NOT EXISTS idx_users_created_at 
        ON users(created_at DESC);
    
    -- 工作流定义更新时间索引
    CREATE INDEX IF NOT EXISTS idx_workflow_definitions_updated_at 
        ON workflow_definitions(updated_at DESC);
    
    -- 文档更新时间索引
    CREATE INDEX IF NOT EXISTS idx_documents_updated_at 
        ON documents(updated_at DESC);

    RAISE NOTICE '索引创建完成';
    RAISE NOTICE '已创建 % 个性能优化索引', (
        SELECT COUNT(*) 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname LIKE 'idx_%'
    );
END $$;

-- 更新表统计信息以便查询优化器使用
ANALYZE;










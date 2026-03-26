-- ============================================
-- 数据库种子数据脚本
-- ============================================
-- 此脚本插入初始数据：
-- 1. 默认角色和权限
-- 2. 管理员用户（如果不存在）
-- 3. 系统配置
-- 注意：此脚本在数据库初始化后执行

-- 等待表创建完成（由Alembic迁移管理）
-- 这里使用DO块来检查表是否存在

DO $$
BEGIN
    -- 检查表是否存在，如果不存在则等待
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users'
    ) THEN
        RAISE NOTICE '表尚未创建，跳过种子数据插入';
        RETURN;
    END IF;

    -- ============================================
    -- 插入默认权限
    -- ============================================
    INSERT INTO permissions (id, code, name, description, resource, action, created_at, updated_at)
    VALUES
        -- 用户管理权限
        (gen_random_uuid(), 'user:read', '查看用户', '查看用户列表和详情', 'user', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'user:create', '创建用户', '创建新用户', 'user', 'create', NOW(), NOW()),
        (gen_random_uuid(), 'user:update', '更新用户', '更新用户信息', 'user', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'user:delete', '删除用户', '删除用户', 'user', 'delete', NOW(), NOW()),
        
        -- 角色管理权限
        (gen_random_uuid(), 'role:read', '查看角色', '查看角色列表和详情', 'role', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'role:create', '创建角色', '创建新角色', 'role', 'create', NOW(), NOW()),
        (gen_random_uuid(), 'role:update', '更新角色', '更新角色信息', 'role', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'role:delete', '删除角色', '删除角色', 'role', 'delete', NOW(), NOW()),
        
        -- 工作流管理权限
        (gen_random_uuid(), 'workflow:read', '查看工作流', '查看工作流列表和详情', 'workflow', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'workflow:create', '创建工作流', '创建新工作流', 'workflow', 'create', NOW(), NOW()),
        (gen_random_uuid(), 'workflow:update', '更新工作流', '更新工作流信息', 'workflow', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'workflow:delete', '删除工作流', '删除工作流', 'workflow', 'delete', NOW(), NOW()),
        (gen_random_uuid(), 'workflow:execute', '执行工作流', '执行工作流', 'workflow', 'execute', NOW(), NOW()),
        
        -- 知识库管理权限
        (gen_random_uuid(), 'knowledge:read', '查看知识库', '查看知识库文档', 'knowledge', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'knowledge:create', '创建知识库', '上传文档到知识库', 'knowledge', 'create', NOW(), NOW()),
        (gen_random_uuid(), 'knowledge:update', '更新知识库', '更新知识库文档', 'knowledge', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'knowledge:delete', '删除知识库', '删除知识库文档', 'knowledge', 'delete', NOW(), NOW()),
        
        -- MCP工具管理权限
        (gen_random_uuid(), 'tool:read', '查看工具', '查看MCP工具列表', 'tool', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'tool:create', '创建工具', '注册新MCP工具', 'tool', 'create', NOW(), NOW()),
        (gen_random_uuid(), 'tool:update', '更新工具', '更新MCP工具信息', 'tool', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'tool:delete', '删除工具', '删除MCP工具', 'tool', 'delete', NOW(), NOW()),
        (gen_random_uuid(), 'tool:execute', '执行工具', '执行MCP工具', 'tool', 'execute', NOW(), NOW()),
        
        -- 系统管理权限
        (gen_random_uuid(), 'system:read', '查看系统', '查看系统配置和日志', 'system', 'read', NOW(), NOW()),
        (gen_random_uuid(), 'system:update', '更新系统', '更新系统配置', 'system', 'update', NOW(), NOW()),
        (gen_random_uuid(), 'system:monitor', '系统监控', '查看系统监控信息', 'system', 'monitor', NOW(), NOW())
    ON CONFLICT (code) DO NOTHING;

    -- ============================================
    -- 插入默认角色
    -- ============================================
    -- 超级管理员角色
    INSERT INTO roles (id, code, name, description, is_system, created_at, updated_at)
    VALUES
        (gen_random_uuid(), 'admin', '超级管理员', '拥有所有权限的系统管理员', true, NOW(), NOW()),
        (gen_random_uuid(), 'user', '普通用户', '普通用户角色', true, NOW(), NOW()),
        (gen_random_uuid(), 'developer', '开发者', '开发者角色，可以管理工作流和工具', false, NOW(), NOW()),
        (gen_random_uuid(), 'viewer', '查看者', '只读权限的查看者角色', false, NOW(), NOW())
    ON CONFLICT (code) DO NOTHING;

    -- ============================================
    -- 为角色分配权限
    -- ============================================
    -- 超级管理员拥有所有权限
    INSERT INTO role_permissions (role_id, permission_id, created_at)
    SELECT 
        r.id,
        p.id,
        NOW()
    FROM roles r
    CROSS JOIN permissions p
    WHERE r.code = 'admin'
    ON CONFLICT DO NOTHING;

    -- 普通用户权限（基本查看和执行权限）
    INSERT INTO role_permissions (role_id, permission_id, created_at)
    SELECT 
        r.id,
        p.id,
        NOW()
    FROM roles r
    CROSS JOIN permissions p
    WHERE r.code = 'user'
        AND p.code IN (
            'user:read', 'workflow:read', 'workflow:execute',
            'knowledge:read', 'tool:read', 'tool:execute'
        )
    ON CONFLICT DO NOTHING;

    -- 开发者权限
    INSERT INTO role_permissions (role_id, permission_id, created_at)
    SELECT 
        r.id,
        p.id,
        NOW()
    FROM roles r
    CROSS JOIN permissions p
    WHERE r.code = 'developer'
        AND p.code IN (
            'user:read', 'workflow:read', 'workflow:create', 'workflow:update', 'workflow:execute',
            'knowledge:read', 'knowledge:create', 'knowledge:update',
            'tool:read', 'tool:create', 'tool:update', 'tool:execute'
        )
    ON CONFLICT DO NOTHING;

    -- 查看者权限（只读）
    INSERT INTO role_permissions (role_id, permission_id, created_at)
    SELECT 
        r.id,
        p.id,
        NOW()
    FROM roles r
    CROSS JOIN permissions p
    WHERE r.code = 'viewer'
        AND p.code LIKE '%:read'
    ON CONFLICT DO NOTHING;

    -- ============================================
    -- 创建默认管理员用户（如果不存在）
    -- ============================================
    -- 注意：密码需要在实际使用时通过密码哈希函数生成
    -- 这里使用占位符，实际部署时应该通过应用层创建
    INSERT INTO users (id, username, email, password_hash, full_name, status, created_at, updated_at)
    VALUES
        (
            gen_random_uuid(),
            'admin',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYq5L5v5F5e',  -- 默认密码: admin123，请在生产环境中修改
            '系统管理员',
            'active',
            NOW(),
            NOW()
        )
    ON CONFLICT (username) DO NOTHING;

    -- 为管理员用户分配admin角色
    INSERT INTO user_roles (user_id, role_id, created_at)
    SELECT 
        u.id,
        r.id,
        NOW()
    FROM users u
    CROSS JOIN roles r
    WHERE u.username = 'admin' AND r.code = 'admin'
    ON CONFLICT DO NOTHING;

    -- ============================================
    -- 插入系统配置
    -- ============================================
    INSERT INTO system_configs (id, key, value, value_type, category, description, is_encrypted, is_public, created_at, updated_at)
    VALUES
        -- 系统配置
        (gen_random_uuid(), 'system.name', 'Enterprise AI Platform', 'string', 'system', '系统名称', false, true, NOW(), NOW()),
        (gen_random_uuid(), 'system.version', '1.0.0', 'string', 'system', '系统版本', false, true, NOW(), NOW()),
        (gen_random_uuid(), 'system.maintenance_mode', 'false', 'bool', 'system', '维护模式', false, false, NOW(), NOW()),
        
        -- 功能配置
        (gen_random_uuid(), 'feature.sso.enabled', 'true', 'bool', 'feature', 'SSO单点登录启用', false, false, NOW(), NOW()),
        (gen_random_uuid(), 'feature.knowledge_base.enabled', 'true', 'bool', 'feature', '知识库功能启用', false, false, NOW(), NOW()),
        (gen_random_uuid(), 'feature.workflow.enabled', 'true', 'bool', 'feature', '工作流功能启用', false, false, NOW(), NOW()),
        
        -- 性能配置
        (gen_random_uuid(), 'performance.max_workflow_executions', '100', 'int', 'performance', '最大工作流并发执行数', false, false, NOW(), NOW()),
        (gen_random_uuid(), 'performance.max_file_size_mb', '100', 'int', 'performance', '最大文件大小（MB）', false, false, NOW(), NOW()),
        
        -- 安全配置
        (gen_random_uuid(), 'security.session_timeout_minutes', '30', 'int', 'security', '会话超时时间（分钟）', false, false, NOW(), NOW()),
        (gen_random_uuid(), 'security.password_min_length', '8', 'int', 'security', '密码最小长度', false, false, NOW(), NOW()),
        (gen_random_uuid(), 'security.enable_audit_log', 'true', 'bool', 'security', '启用审计日志', false, false, NOW(), NOW())
    ON CONFLICT (key) DO NOTHING;

    RAISE NOTICE '种子数据插入完成';
END $$;










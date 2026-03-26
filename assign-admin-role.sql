-- 为 admin 用户分配 admin 角色
-- 使用方法: docker exec -i enterprise-ai-postgres psql -U <DB_USER> -d enterprise_ai_platform < assign-admin-role.sql

-- 检查 admin 用户是否存在
DO $$
DECLARE
    admin_user_id UUID;
    admin_role_id UUID;
BEGIN
    -- 获取 admin 用户 ID
    SELECT id INTO admin_user_id
    FROM users
    WHERE username = 'admin'
    LIMIT 1;
    
    -- 获取 admin 角色 ID
    SELECT id INTO admin_role_id
    FROM roles
    WHERE code = 'admin'
    LIMIT 1;
    
    -- 如果用户和角色都存在，分配角色
    IF admin_user_id IS NOT NULL AND admin_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id, created_at)
        VALUES (admin_user_id, admin_role_id, NOW())
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Admin role assigned to admin user successfully';
    ELSE
        IF admin_user_id IS NULL THEN
            RAISE NOTICE 'Admin user not found';
        END IF;
        IF admin_role_id IS NULL THEN
            RAISE NOTICE 'Admin role not found';
        END IF;
    END IF;
END $$;

-- 验证分配结果
SELECT 
    u.username,
    u.email,
    r.code as role_code,
    r.name as role_name
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.username = 'admin';


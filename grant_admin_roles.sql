-- 添加roles列（如果不存在）
ALTER TABLE users ADD COLUMN IF NOT EXISTS roles JSONB DEFAULT '[]'::jsonb;

-- 给admin、guanruibei、zhaojun配置管理员权限
UPDATE users 
SET roles = '["admin"]'::jsonb 
WHERE username IN ('admin', 'guanruibei', 'zhaojun');

-- 查询结果
SELECT username, roles 
FROM users 
WHERE username IN ('admin', 'guanruibei', 'zhaojun');


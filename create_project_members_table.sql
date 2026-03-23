-- 创建项目成员表
-- 先检查并创建枚举类型
DO $$ BEGIN
    CREATE TYPE projectmemberrole AS ENUM ('manager', 'member', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建项目成员表
CREATE TABLE IF NOT EXISTS pm_project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role projectmemberrole NOT NULL DEFAULT 'member',
    joined_at DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_member UNIQUE(project_id, user_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON pm_project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON pm_project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_role ON pm_project_members(role);

-- 为现有项目添加创建者和管理员为项目经理
INSERT INTO pm_project_members (project_id, user_id, role, joined_at, created_at, updated_at)
SELECT 
    id as project_id,
    manager_id as user_id,
    'manager'::projectmemberrole as role,
    created_at::date as joined_at,
    created_at,
    updated_at
FROM pm_projects
WHERE manager_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM pm_project_members 
    WHERE pm_project_members.project_id = pm_projects.id 
    AND pm_project_members.user_id = pm_projects.manager_id
);


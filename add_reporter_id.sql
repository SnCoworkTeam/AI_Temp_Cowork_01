-- 添加reporter_id字段到pm_projects表
ALTER TABLE pm_projects 
ADD COLUMN IF NOT EXISTS reporter_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_pm_projects_reporter_id ON pm_projects(reporter_id);

-- 添加注释
COMMENT ON COLUMN pm_projects.reporter_id IS '填报人ID';



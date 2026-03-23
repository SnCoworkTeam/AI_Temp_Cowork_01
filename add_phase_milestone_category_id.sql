-- 添加项目阶段的category_id字段
ALTER TABLE pm_project_phases 
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES pm_basic_data_categories(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS ix_pm_project_phases_category_id ON pm_project_phases(category_id);
COMMENT ON COLUMN pm_project_phases.category_id IS '基础数据分类ID（项目阶段）';

-- 添加里程碑的category_id字段
ALTER TABLE pm_milestones 
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES pm_basic_data_categories(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS ix_pm_milestones_category_id ON pm_milestones(category_id);
COMMENT ON COLUMN pm_milestones.category_id IS '基础数据分类ID（里程碑）';


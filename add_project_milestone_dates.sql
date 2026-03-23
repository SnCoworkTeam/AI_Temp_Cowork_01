-- 添加项目重要里程碑日期字段
ALTER TABLE pm_projects ADD COLUMN IF NOT EXISTS milestone_implementation_start DATE;
COMMENT ON COLUMN pm_projects.milestone_implementation_start IS '实施启动日期';

ALTER TABLE pm_projects ADD COLUMN IF NOT EXISTS milestone_solution_confirmation DATE;
COMMENT ON COLUMN pm_projects.milestone_solution_confirmation IS '方案确认日期';

ALTER TABLE pm_projects ADD COLUMN IF NOT EXISTS milestone_delivery_online DATE;
COMMENT ON COLUMN pm_projects.milestone_delivery_online IS '交付上线日期';

ALTER TABLE pm_projects ADD COLUMN IF NOT EXISTS milestone_project_acceptance DATE;
COMMENT ON COLUMN pm_projects.milestone_project_acceptance IS '项目验收日期';



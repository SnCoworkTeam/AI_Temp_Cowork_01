-- 添加月报表缺失字段
ALTER TABLE pm_monthly_reports 
ADD COLUMN IF NOT EXISTS progress_percent FLOAT DEFAULT 0.0;

ALTER TABLE pm_monthly_reports 
ADD COLUMN IF NOT EXISTS key_milestones JSONB DEFAULT '[]'::jsonb;

ALTER TABLE pm_monthly_reports 
ADD COLUMN IF NOT EXISTS risk_summary TEXT;

ALTER TABLE pm_monthly_reports 
ADD COLUMN IF NOT EXISTS resource_summary TEXT;

-- 添加注释
COMMENT ON COLUMN pm_monthly_reports.progress_percent IS '月度进度百分比';
COMMENT ON COLUMN pm_monthly_reports.key_milestones IS '关键里程碑完成情况';
COMMENT ON COLUMN pm_monthly_reports.risk_summary IS '风险汇总';
COMMENT ON COLUMN pm_monthly_reports.resource_summary IS '资源使用情况';



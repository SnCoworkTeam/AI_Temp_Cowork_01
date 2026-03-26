-- 生成项目管理测试数据
-- 为项目创建阶段、里程碑、周报、风险等数据

-- 1. 生成项目阶段
INSERT INTO pm_project_phases (id, project_id, name, description, sequence, start_date, end_date, progress_percent, metadata)
SELECT 
    gen_random_uuid(),
    p.id,
    phase_names.name,
    p.name || '的' || phase_names.name,
    phase_names.seq,
    CURRENT_DATE - (30 - phase_names.seq * 10)::integer,
    CURRENT_DATE - (30 - phase_names.seq * 10)::integer + 15,
    LEAST(100, (phase_names.seq + 1) * 30),
    '{}'::jsonb
FROM pm_projects p
CROSS JOIN (
    SELECT '需求分析' as name, 0 as seq
    UNION ALL SELECT '设计阶段', 1
    UNION ALL SELECT '开发阶段', 2
) phase_names
WHERE NOT EXISTS (
    SELECT 1 FROM pm_project_phases pp 
    WHERE pp.project_id = p.id AND pp.sequence = phase_names.seq
)
LIMIT 60;

-- 2. 生成里程碑
INSERT INTO pm_milestones (id, project_id, phase_id, name, description, target_date, status, metadata)
SELECT 
    gen_random_uuid(),
    p.id,
    (SELECT id FROM pm_project_phases WHERE project_id = p.id ORDER BY sequence LIMIT 1),
    milestone_names.name,
    p.name || '的' || milestone_names.name || '里程碑',
    CURRENT_DATE + (milestone_names.seq * 20),
    CASE WHEN milestone_names.seq = 0 THEN 'in_progress' ELSE 'planned' END,
    '{}'::jsonb
FROM pm_projects p
CROSS JOIN (
    SELECT '需求确认' as name, 0 as seq
    UNION ALL SELECT '设计评审', 1
    UNION ALL SELECT '开发完成', 2
) milestone_names
WHERE NOT EXISTS (
    SELECT 1 FROM pm_milestones m 
    WHERE m.project_id = p.id AND m.name = p.name || '的' || milestone_names.name || '里程碑'
)
LIMIT 60;

-- 3. 生成周报（最近4周）
INSERT INTO pm_weekly_reports (id, project_id, week_number, report_date, content_plan, content_achievement, issues_risks, next_week_plan, metadata)
SELECT 
    gen_random_uuid(),
    p.id,
    EXTRACT(WEEK FROM (CURRENT_DATE - (week_offset * INTERVAL '1 week')))::integer,
    CURRENT_DATE - (week_offset * INTERVAL '1 week'),
    '第' || (week_offset + 1) || '周计划：继续推进项目进度',
    '第' || (week_offset + 1) || '周成果：完成部分功能开发',
    CASE WHEN week_offset < 2 THEN '无重大风险' ELSE '需要关注进度' END,
    '第' || (week_offset + 2) || '周计划：继续推进',
    '{}'::jsonb
FROM pm_projects p
CROSS JOIN generate_series(0, 3) week_offset
WHERE NOT EXISTS (
    SELECT 1 FROM pm_weekly_reports wr 
    WHERE wr.project_id = p.id 
    AND wr.report_date = CURRENT_DATE - (week_offset * INTERVAL '1 week')
)
LIMIT 80;

-- 4. 生成风险（约1/3的项目）
INSERT INTO pm_risks (id, project_id, name, description, risk_level, status, mitigation_plan, metadata)
SELECT 
    gen_random_uuid(),
    p.id,
    p.name || '潜在风险',
    '项目进度可能存在延迟风险',
    CASE (p.id::text ~ '[0-9]')::integer % 3
        WHEN 0 THEN 'low'
        WHEN 1 THEN 'medium'
        ELSE 'high'
    END,
    'open',
    '加强进度跟踪，及时调整资源',
    '{}'::jsonb
FROM pm_projects p
WHERE (p.id::text ~ '[0-9]')::integer % 3 = 0
AND NOT EXISTS (
    SELECT 1 FROM pm_risks r WHERE r.project_id = p.id
)
LIMIT 20;

-- 显示统计
SELECT 
    '项目阶段' as type, COUNT(*) as count FROM pm_project_phases
UNION ALL
SELECT '里程碑', COUNT(*) FROM pm_milestones
UNION ALL
SELECT '周报', COUNT(*) FROM pm_weekly_reports
UNION ALL
SELECT '风险', COUNT(*) FROM pm_risks;












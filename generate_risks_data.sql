-- 生成风险数据
INSERT INTO pm_risks (id, project_id, name, description, risk_level, status, mitigation_plan, metadata)
SELECT 
    gen_random_uuid(),
    p.id,
    p.name || '潜在风险',
    '项目进度可能存在延迟风险，需要加强跟踪',
    CASE (ROW_NUMBER() OVER (ORDER BY p.id) % 3)
        WHEN 0 THEN 'low'
        WHEN 1 THEN 'medium'
        ELSE 'high'
    END,
    'open',
    '加强进度跟踪，及时调整资源分配',
    '{}'::jsonb
FROM pm_projects p
WHERE NOT EXISTS (
    SELECT 1 FROM pm_risks r WHERE r.project_id = p.id
)
LIMIT 20;

-- 显示统计
SELECT '风险' as type, COUNT(*) as count FROM pm_risks;












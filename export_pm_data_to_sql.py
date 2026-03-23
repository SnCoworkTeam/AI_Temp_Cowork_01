"""
导出项目管理数据为SQL格式
"""
import psycopg2
import json
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ai_platform',
    'user': 'ai_user',
    'password': 'ai_password'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

sql_statements = []

# 导出项目
cur.execute("SELECT id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata FROM pm_projects")
projects = cur.fetchall()

sql_statements.append("-- 导入项目管理数据")
sql_statements.append("-- 项目数据")
sql_statements.append("")

for row in projects:
    project_id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata = row
    
    # 转义字符串
    name_escaped = name.replace("'", "''")
    description_escaped = (description or '').replace("'", "''")
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False).replace("'", "''")
    
    start_date_str = f"'{start_date}'" if start_date else "NULL"
    end_date_str = f"'{end_date}'" if end_date else "NULL"
    budget_str = str(budget) if budget else "NULL"
    
    sql = f"""
INSERT INTO pm_projects (id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata)
VALUES ('{project_id}', '{project_code}', '{name_escaped}', '{description_escaped}', '{status}', '{priority}', {start_date_str}, {end_date_str}, {progress_percent}, {budget_str}, '{metadata_json}'::jsonb)
ON CONFLICT (project_code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();
"""
    sql_statements.append(sql)

# 导出任务
cur.execute("SELECT id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata FROM pm_tasks")
tasks = cur.fetchall()

sql_statements.append("-- 任务数据")
sql_statements.append("")

for row in tasks:
    task_id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata = row
    
    # 转义字符串
    name_escaped = name.replace("'", "''")
    description_escaped = (description or '').replace("'", "''")
    dependencies_json = json.dumps(dependencies or [], ensure_ascii=False).replace("'", "''")
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False).replace("'", "''")
    
    phase_id_str = f"'{phase_id}'" if phase_id else "NULL"
    milestone_id_str = f"'{milestone_id}'" if milestone_id else "NULL"
    assignee_id_str = f"'{assignee_id}'" if assignee_id else "NULL"
    start_date_str = f"'{start_date}'" if start_date else "NULL"
    due_date_str = f"'{due_date}'" if due_date else "NULL"
    completed_date_str = f"'{completed_date}'" if completed_date else "NULL"
    estimated_hours_str = str(estimated_hours) if estimated_hours else "NULL"
    actual_hours_str = str(actual_hours) if actual_hours else "NULL"
    
    sql = f"""
INSERT INTO pm_tasks (id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata)
VALUES ('{task_id}', '{project_id}', {phase_id_str}, {milestone_id_str}, '{name_escaped}', '{description_escaped}', '{status}', {assignee_id_str}, {start_date_str}, {due_date_str}, {completed_date_str}, {estimated_hours_str}, {actual_hours_str}, {progress_percent}, '{dependencies_json}'::jsonb, '{metadata_json}'::jsonb)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    progress_percent = EXCLUDED.progress_percent,
    updated_at = now();
"""
    sql_statements.append(sql)

# 输出SQL到文件
sql_content = '\n'.join(sql_statements)

# 直接写入文件，避免编码问题
with open('pm_data_import.sql', 'w', encoding='utf-8') as f:
    f.write(sql_content)

print(f"SQL文件已生成: pm_data_import.sql")
print(f"包含 {len(projects)} 个项目和 {len(tasks)} 个任务")

cur.close()
conn.close()


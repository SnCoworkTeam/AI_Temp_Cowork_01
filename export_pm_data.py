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

# 导出项目
cur.execute("SELECT id, project_code, name, description, status, priority, start_date, end_date, progress_percent, budget, metadata FROM pm_projects")
projects = []
for row in cur.fetchall():
    projects.append({
        'id': str(row[0]),
        'project_code': row[1],
        'name': row[2],
        'description': row[3],
        'status': row[4],
        'priority': row[5],
        'start_date': str(row[6]) if row[6] else None,
        'end_date': str(row[7]) if row[7] else None,
        'progress_percent': float(row[8]) if row[8] else 0.0,
        'budget': float(row[9]) if row[9] else None,
        'metadata': row[10] if row[10] else {}
    })

# 导出任务
cur.execute("SELECT id, project_id, phase_id, milestone_id, name, description, status, assignee_id, start_date, due_date, completed_date, estimated_hours, actual_hours, progress_percent, dependencies, metadata FROM pm_tasks")
tasks = []
for row in cur.fetchall():
    tasks.append({
        'id': str(row[0]),
        'project_id': str(row[1]),
        'phase_id': str(row[2]) if row[2] else None,
        'milestone_id': str(row[3]) if row[3] else None,
        'name': row[4],
        'description': row[5],
        'status': row[6],
        'assignee_id': str(row[7]) if row[7] else None,
        'start_date': str(row[8]) if row[8] else None,
        'due_date': str(row[9]) if row[9] else None,
        'completed_date': str(row[10]) if row[10] else None,
        'estimated_hours': float(row[11]) if row[11] else None,
        'actual_hours': float(row[12]) if row[12] else None,
        'progress_percent': float(row[13]) if row[13] else 0.0,
        'dependencies': row[14] if row[14] else [],
        'metadata': row[15] if row[15] else {}
    })

data = {
    'projects': projects,
    'tasks': tasks
}

print(json.dumps(data, ensure_ascii=False, indent=2))

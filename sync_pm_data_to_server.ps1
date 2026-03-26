# 同步项目管理数据到服务器
# 从本地数据库导出数据，然后导入到服务器数据库

$SSH_KEY = "enterprise_ai_platform.pem"
$SERVER = "ubuntu@43.143.139.197"
$SERVER_PATH = "/opt/enterprise-ai-platform"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  同步项目管理数据到服务器" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 1. 导出本地数据
Write-Host ""
Write-Host "1. 导出本地项目管理数据..." -ForegroundColor Yellow

$exportScript = @"
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
"@

$exportScript | Out-File -FilePath "export_pm_data.py" -Encoding UTF8
$exportData = python export_pm_data.py 2>&1 | Out-String

# 保存到文件
$exportData | Out-File -FilePath "pm_data_export.json" -Encoding UTF8
Write-Host "✅ 数据已导出到 pm_data_export.json" -ForegroundColor Green

# 2. 上传数据文件到服务器
Write-Host ""
Write-Host "2. 上传数据文件到服务器..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "pm_data_export.json" "${SERVER}:${SERVER_PATH}/pm_data_export.json"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 数据文件已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
    exit 1
}

# 3. 生成SQL文件
Write-Host ""
Write-Host "3. 生成SQL导入文件..." -ForegroundColor Yellow
python export_pm_data_to_sql.py 2>&1
if (Test-Path "pm_data_import.sql") {
    $lineCount = (Get-Content pm_data_import.sql -Encoding UTF8 | Measure-Object -Line).Lines
    Write-Host "✅ SQL文件已生成 ($lineCount 行)" -ForegroundColor Green
} else {
    Write-Host "❌ SQL文件生成失败" -ForegroundColor Red
    exit 1
}

# 4. 上传SQL文件到服务器
Write-Host ""
Write-Host "4. 上传SQL文件到服务器..." -ForegroundColor Yellow
scp -i $SSH_KEY -o StrictHostKeyChecking=no "pm_data_import.sql" "${SERVER}:${SERVER_PATH}/pm_data_import.sql"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SQL文件已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
    exit 1
}

# 5. 确保服务器上有项目管理表
Write-Host ""
Write-Host "5. 确保服务器上有项目管理表..." -ForegroundColor Yellow
$createTablesScript = @"
import psycopg2
import json
import sys
import os

# 读取服务器数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'ai_platform'),
    'user': os.getenv('DB_USER', 'ai_user'),
    'password': os.getenv('DB_PASSWORD', 'ai_password')
}

# 读取数据
with open('/opt/enterprise-ai-platform/pm_data_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

try:
    # 导入项目
    print(f"导入 {len(data['projects'])} 个项目...")
    for project in data['projects']:
        cur.execute("""
            INSERT INTO pm_projects 
            (id, project_code, name, description, status, priority, start_date, end_date, 
             progress_percent, budget, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_code) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                progress_percent = EXCLUDED.progress_percent,
                updated_at = now()
        """, (
            project['id'],
            project['project_code'],
            project['name'],
            project['description'],
            project['status'],
            project['priority'],
            project['start_date'],
            project['end_date'],
            project['progress_percent'],
            project['budget'],
            json.dumps(project['metadata'], ensure_ascii=False)
        ))
    
    # 导入任务
    print(f"导入 {len(data['tasks'])} 个任务...")
    for task in data['tasks']:
        cur.execute("""
            INSERT INTO pm_tasks 
            (id, project_id, phase_id, milestone_id, name, description, status, assignee_id,
             start_date, due_date, completed_date, estimated_hours, actual_hours, 
             progress_percent, dependencies, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                progress_percent = EXCLUDED.progress_percent,
                updated_at = now()
        """, (
            task['id'],
            task['project_id'],
            task['phase_id'],
            task['milestone_id'],
            task['name'],
            task['description'],
            task['status'],
            task['assignee_id'],
            task['start_date'],
            task['due_date'],
            task['completed_date'],
            task['estimated_hours'],
            task['actual_hours'],
            task['progress_percent'],
            json.dumps(task['dependencies'], ensure_ascii=False),
            json.dumps(task['metadata'], ensure_ascii=False)
        ))
    
    conn.commit()
    print("✅ 数据导入成功")
    print(f"   - 项目: {len(data['projects'])} 个")
    print(f"   - 任务: {len(data['tasks'])} 个")
    
except Exception as e:
    conn.rollback()
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    cur.close()
    conn.close()
"@

$importScript | Out-File -FilePath "import_pm_data_to_server.py" -Encoding UTF8
scp -i $SSH_KEY -o StrictHostKeyChecking=no "import_pm_data_to_server.py" "${SERVER}:${SERVER_PATH}/import_pm_data_to_server.py"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 导入脚本已上传" -ForegroundColor Green
} else {
    Write-Host "❌ 上传失败" -ForegroundColor Red
    exit 1
}

# 4. 确保服务器上有项目管理表
Write-Host ""
Write-Host "4. 确保服务器上有项目管理表..." -ForegroundColor Yellow
$createTablesCmd = "cd $SERVER_PATH && docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform -f - < database/src/migrations/versions/024_add_project_management_tables.sql 2>&1 || echo 'Tables may already exist'"
# 或者直接运行Python脚本创建表
$createTablesScript = @"
import psycopg2
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'ai_platform'),
    'user': os.getenv('DB_USER', 'ai_user'),
    'password': os.getenv('DB_PASSWORD', 'ai_password')
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# 创建表（如果不存在）
try:
    # pm_project_phases
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_project_phases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            sequence INTEGER NOT NULL DEFAULT 0,
            start_date DATE,
            end_date DATE,
            progress_percent FLOAT NOT NULL DEFAULT 0.0,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_project_phases_project_id ON pm_project_phases(project_id);")
    
    # pm_milestones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_milestones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
            phase_id UUID REFERENCES pm_project_phases(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            target_date DATE,
            actual_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'planned',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_milestones_project_id ON pm_milestones(project_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_milestones_phase_id ON pm_milestones(phase_id);")
    
    # pm_tasks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pm_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
            phase_id UUID REFERENCES pm_project_phases(id) ON DELETE CASCADE,
            milestone_id UUID REFERENCES pm_milestones(id) ON DELETE SET NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'todo',
            assignee_id UUID REFERENCES users(id),
            start_date DATE,
            due_date DATE,
            completed_date DATE,
            estimated_hours FLOAT,
            actual_hours FLOAT,
            progress_percent FLOAT NOT NULL DEFAULT 0.0,
            dependencies JSONB DEFAULT '[]',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_tasks_project_id ON pm_tasks(project_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_tasks_status ON pm_tasks(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_pm_tasks_assignee_id ON pm_tasks(assignee_id);")
    
    conn.commit()
    print("✅ 项目管理表已创建或已存在")
except Exception as e:
    conn.rollback()
    print(f"⚠️  创建表时出错（可能已存在）: {e}")
finally:
    cur.close()
    conn.close()
"@

$createTablesScript | Out-File -FilePath "create_pm_tables_server.py" -Encoding UTF8
scp -i $SSH_KEY -o StrictHostKeyChecking=no "create_pm_tables_server.py" "${SERVER}:${SERVER_PATH}/create_pm_tables_server.py"

# 在服务器上创建表（使用SQL）
$createTablesSQL = @"
CREATE TABLE IF NOT EXISTS pm_project_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sequence INTEGER NOT NULL DEFAULT 0,
    start_date DATE,
    end_date DATE,
    progress_percent FLOAT NOT NULL DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_pm_project_phases_project_id ON pm_project_phases(project_id);

CREATE TABLE IF NOT EXISTS pm_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES pm_project_phases(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    target_date DATE,
    actual_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_pm_milestones_project_id ON pm_milestones(project_id);
CREATE INDEX IF NOT EXISTS ix_pm_milestones_phase_id ON pm_milestones(phase_id);

CREATE TABLE IF NOT EXISTS pm_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES pm_projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES pm_project_phases(id) ON DELETE CASCADE,
    milestone_id UUID REFERENCES pm_milestones(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    assignee_id UUID REFERENCES users(id),
    start_date DATE,
    due_date DATE,
    completed_date DATE,
    estimated_hours FLOAT,
    actual_hours FLOAT,
    progress_percent FLOAT NOT NULL DEFAULT 0.0,
    dependencies JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_pm_tasks_project_id ON pm_tasks(project_id);
CREATE INDEX IF NOT EXISTS ix_pm_tasks_status ON pm_tasks(status);
CREATE INDEX IF NOT EXISTS ix_pm_tasks_assignee_id ON pm_tasks(assignee_id);
"@

$createTablesSQL | Out-File -FilePath "create_pm_tables.sql" -Encoding UTF8
scp -i $SSH_KEY -o StrictHostKeyChecking=no "create_pm_tables.sql" "${SERVER}:${SERVER_PATH}/create_pm_tables.sql"

$createTablesResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < $SERVER_PATH/create_pm_tables.sql 2>&1"
Write-Host $createTablesResult

# 6. 在服务器上导入数据
Write-Host ""
Write-Host "6. 在服务器上导入数据..." -ForegroundColor Yellow
$importResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform < $SERVER_PATH/pm_data_import.sql 2>&1"
Write-Host $importResult

# 7. 验证数据
Write-Host ""
Write-Host "7. 验证服务器数据..." -ForegroundColor Yellow
$verifyResult = ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SERVER "docker exec -i enterprise-ai-postgres psql -U ai_user -d ai_platform -c 'SELECT COUNT(*) as project_count FROM pm_projects; SELECT COUNT(*) as task_count FROM pm_tasks;' 2>&1"
Write-Host $verifyResult

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 数据同步完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green


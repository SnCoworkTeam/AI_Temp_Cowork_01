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

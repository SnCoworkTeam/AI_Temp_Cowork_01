"""
手动创建项目管理表（如果迁移未执行）
"""
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ai_platform',
    'user': 'ai_user',
    'password': 'ai_password'
}

def create_pm_tables():
    """创建项目管理表"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # 创建 pm_project_phases 表
        print("创建 pm_project_phases 表...")
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
        print("✅ pm_project_phases 表已创建")
        
        # 创建 pm_milestones 表
        print("创建 pm_milestones 表...")
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
        print("✅ pm_milestones 表已创建")
        
        # 创建 pm_tasks 表
        print("创建 pm_tasks 表...")
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
        print("✅ pm_tasks 表已创建")
        
        conn.commit()
        print("\n✅ 所有项目管理表已创建")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    create_pm_tables()












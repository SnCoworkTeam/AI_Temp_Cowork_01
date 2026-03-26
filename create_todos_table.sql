-- 创建待办事项相关枚举类型
DO $$ BEGIN
    CREATE TYPE todocategory AS ENUM ('work', 'personal', 'urgent', 'project', 'other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE todopriority AS ENUM ('high', 'medium', 'low');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE todostatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 创建待办事项表
CREATE TABLE IF NOT EXISTS user_todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category todocategory NOT NULL DEFAULT 'work',
    priority todopriority NOT NULL DEFAULT 'medium',
    status todostatus NOT NULL DEFAULT 'pending',
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    project_id UUID REFERENCES pm_projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES pm_tasks(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_todos_user_id ON user_todos(user_id);
CREATE INDEX IF NOT EXISTS idx_user_todos_status ON user_todos(status);
CREATE INDEX IF NOT EXISTS idx_user_todos_due_date ON user_todos(due_date);
CREATE INDEX IF NOT EXISTS idx_user_todos_category ON user_todos(category);
CREATE INDEX IF NOT EXISTS idx_user_todos_priority ON user_todos(priority);
CREATE INDEX IF NOT EXISTS idx_user_todos_project_id ON user_todos(project_id);
CREATE INDEX IF NOT EXISTS idx_user_todos_task_id ON user_todos(task_id);
CREATE INDEX IF NOT EXISTS idx_user_todos_user_status ON user_todos(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_todos_user_due_date ON user_todos(user_id, due_date);

-- 添加表注释
COMMENT ON TABLE user_todos IS '用户待办事项表';
COMMENT ON COLUMN user_todos.id IS '待办事项ID';
COMMENT ON COLUMN user_todos.user_id IS '用户ID';
COMMENT ON COLUMN user_todos.title IS '标题';
COMMENT ON COLUMN user_todos.description IS '描述';
COMMENT ON COLUMN user_todos.category IS '分类';
COMMENT ON COLUMN user_todos.priority IS '优先级';
COMMENT ON COLUMN user_todos.status IS '状态';
COMMENT ON COLUMN user_todos.due_date IS '截止日期';
COMMENT ON COLUMN user_todos.completed_at IS '完成时间';
COMMENT ON COLUMN user_todos.project_id IS '关联项目ID';
COMMENT ON COLUMN user_todos.task_id IS '关联任务ID';
COMMENT ON COLUMN user_todos.metadata IS '扩展元数据';
COMMENT ON COLUMN user_todos.created_at IS '创建时间';
COMMENT ON COLUMN user_todos.updated_at IS '更新时间';




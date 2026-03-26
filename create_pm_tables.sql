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

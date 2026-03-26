-- 创建基础数据分类表
CREATE TABLE IF NOT EXISTS pm_basic_data_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_type VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_id UUID,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    CONSTRAINT fk_basic_data_categories_parent 
        FOREIGN KEY (parent_id) 
        REFERENCES pm_basic_data_categories(id) 
        ON DELETE SET NULL,
    
    -- 唯一约束
    CONSTRAINT uq_category_type_code 
        UNIQUE (category_type, code)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_basic_data_categories_type 
    ON pm_basic_data_categories(category_type);
CREATE INDEX IF NOT EXISTS idx_basic_data_categories_code 
    ON pm_basic_data_categories(code);
CREATE INDEX IF NOT EXISTS idx_basic_data_categories_parent 
    ON pm_basic_data_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_basic_data_categories_active 
    ON pm_basic_data_categories(is_active);

-- 创建项目基础数据关联表
CREATE TABLE IF NOT EXISTS pm_project_basic_data_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    category_id UUID NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    CONSTRAINT fk_project_basic_data_project 
        FOREIGN KEY (project_id) 
        REFERENCES pm_projects(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_project_basic_data_category 
        FOREIGN KEY (category_id) 
        REFERENCES pm_basic_data_categories(id) 
        ON DELETE CASCADE,
    
    -- 唯一约束
    CONSTRAINT uq_project_category 
        UNIQUE (project_id, category_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_project_basic_data_project 
    ON pm_project_basic_data_mapping(project_id);
CREATE INDEX IF NOT EXISTS idx_project_basic_data_category 
    ON pm_project_basic_data_mapping(category_id);

-- 添加表注释
COMMENT ON TABLE pm_basic_data_categories IS '基础数据分类表';
COMMENT ON TABLE pm_project_basic_data_mapping IS '项目基础数据关联表';


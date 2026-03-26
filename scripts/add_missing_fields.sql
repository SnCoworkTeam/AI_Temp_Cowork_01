-- 添加缺失的字段（如果不存在）
DO $$ 
BEGIN
    -- ApplicationSystem
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='code') THEN
        ALTER TABLE application_systems ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_application_systems_code ON application_systems(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='deployment_model') THEN
        ALTER TABLE application_systems ADD COLUMN deployment_model VARCHAR(50);
    END IF;
    
    -- BusinessCapability
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='code') THEN
        ALTER TABLE business_capabilities ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_business_capabilities_code ON business_capabilities(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='maturity_level') THEN
        ALTER TABLE business_capabilities ADD COLUMN maturity_level VARCHAR(50);
    END IF;
    
    -- BusinessProcess
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='code') THEN
        ALTER TABLE business_processes ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_business_processes_code ON business_processes(code);
    END IF;
    
    -- ApplicationService
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='code') THEN
        ALTER TABLE application_services ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_application_services_code ON application_services(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='status') THEN
        ALTER TABLE application_services ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    -- TechnologyInstance
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='technology_instances' AND column_name='description') THEN
        ALTER TABLE technology_instances ADD COLUMN description TEXT;
    END IF;
END $$;


-- 完整添加所有缺失字段
DO $$ 
BEGIN
    -- BusinessCapability
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='code') THEN
        ALTER TABLE business_capabilities ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_business_capabilities_code ON business_capabilities(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='maturity_level') THEN
        ALTER TABLE business_capabilities ADD COLUMN maturity_level VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='business_value') THEN
        ALTER TABLE business_capabilities ADD COLUMN business_value VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_capabilities' AND column_name='investment_priority') THEN
        ALTER TABLE business_capabilities ADD COLUMN investment_priority VARCHAR(50);
    END IF;
    
    -- BusinessProcess
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='code') THEN
        ALTER TABLE business_processes ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_business_processes_code ON business_processes(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='priority') THEN
        ALTER TABLE business_processes ADD COLUMN priority VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='kpi_metrics') THEN
        ALTER TABLE business_processes ADD COLUMN kpi_metrics JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='pain_points') THEN
        ALTER TABLE business_processes ADD COLUMN pain_points JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='business_processes' AND column_name='improvement_opportunities') THEN
        ALTER TABLE business_processes ADD COLUMN improvement_opportunities JSONB;
    END IF;
    
    -- ApplicationSystem
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='code') THEN
        ALTER TABLE application_systems ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_application_systems_code ON application_systems(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='deployment_model') THEN
        ALTER TABLE application_systems ADD COLUMN deployment_model VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='criticality') THEN
        ALTER TABLE application_systems ADD COLUMN criticality VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='availability_requirement') THEN
        ALTER TABLE application_systems ADD COLUMN availability_requirement VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='support_team') THEN
        ALTER TABLE application_systems ADD COLUMN support_team VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='cost_center') THEN
        ALTER TABLE application_systems ADD COLUMN cost_center VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='license_info') THEN
        ALTER TABLE application_systems ADD COLUMN license_info JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_systems' AND column_name='integration_points') THEN
        ALTER TABLE application_systems ADD COLUMN integration_points JSONB;
    END IF;
    
    -- ApplicationService
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='code') THEN
        ALTER TABLE application_services ADD COLUMN code VARCHAR(100);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_application_services_code ON application_services(code);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='status') THEN
        ALTER TABLE application_services ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='version') THEN
        ALTER TABLE application_services ADD COLUMN version VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='health_check_endpoint') THEN
        ALTER TABLE application_services ADD COLUMN health_check_endpoint VARCHAR(500);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='application_services' AND column_name='service_dependencies') THEN
        ALTER TABLE application_services ADD COLUMN service_dependencies JSONB;
    END IF;
    
    -- APIInterface
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='status') THEN
        ALTER TABLE api_interfaces ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='version') THEN
        ALTER TABLE api_interfaces ADD COLUMN version VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='request_schema') THEN
        ALTER TABLE api_interfaces ADD COLUMN request_schema JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='response_schema') THEN
        ALTER TABLE api_interfaces ADD COLUMN response_schema JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='authentication_type') THEN
        ALTER TABLE api_interfaces ADD COLUMN authentication_type VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='api_interfaces' AND column_name='rate_limit') THEN
        ALTER TABLE api_interfaces ADD COLUMN rate_limit VARCHAR(100);
    END IF;
    
    -- DataEntity
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='status') THEN
        ALTER TABLE data_entities ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='sensitivity_level') THEN
        ALTER TABLE data_entities ADD COLUMN sensitivity_level VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='retention_policy') THEN
        ALTER TABLE data_entities ADD COLUMN retention_policy VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='backup_frequency') THEN
        ALTER TABLE data_entities ADD COLUMN backup_frequency VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='data_volume') THEN
        ALTER TABLE data_entities ADD COLUMN data_volume VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_entities' AND column_name='access_control') THEN
        ALTER TABLE data_entities ADD COLUMN access_control JSONB;
    END IF;
    
    -- DataModel
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_models' AND column_name='model_type') THEN
        ALTER TABLE data_models ADD COLUMN model_type VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_models' AND column_name='application_system_id') THEN
        ALTER TABLE data_models ADD COLUMN application_system_id UUID REFERENCES application_systems(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_models' AND column_name='status') THEN
        ALTER TABLE data_models ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    -- DataFlow
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='flow_type') THEN
        ALTER TABLE data_flows ADD COLUMN flow_type VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='source_system_id') THEN
        ALTER TABLE data_flows ADD COLUMN source_system_id UUID REFERENCES application_systems(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='target_system_id') THEN
        ALTER TABLE data_flows ADD COLUMN target_system_id UUID REFERENCES application_systems(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='frequency') THEN
        ALTER TABLE data_flows ADD COLUMN frequency VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='volume') THEN
        ALTER TABLE data_flows ADD COLUMN volume VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='data_flows' AND column_name='status') THEN
        ALTER TABLE data_flows ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
    
    -- TechnologyInstance
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='technology_instances' AND column_name='description') THEN
        ALTER TABLE technology_instances ADD COLUMN description TEXT;
    END IF;
    
    RAISE NOTICE '所有字段添加完成';
END $$;


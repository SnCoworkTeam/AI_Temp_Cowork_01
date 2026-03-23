-- 添加缺失的列
ALTER TABLE business_processes ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organization_units(id);
ALTER TABLE business_capabilities ADD COLUMN IF NOT EXISTS owner_organization_id UUID REFERENCES organization_units(id);
ALTER TABLE application_systems ADD COLUMN IF NOT EXISTS business_owner_org_id UUID REFERENCES organization_units(id);
ALTER TABLE application_systems ADD COLUMN IF NOT EXISTS system_category VARCHAR(50);
ALTER TABLE data_entities ADD COLUMN IF NOT EXISTS code VARCHAR(100);
ALTER TABLE data_entities ADD COLUMN IF NOT EXISTS application_system_id UUID REFERENCES application_systems(id);
ALTER TABLE api_interfaces ADD COLUMN IF NOT EXISTS code VARCHAR(100);
ALTER TABLE api_interfaces ADD COLUMN IF NOT EXISTS application_system_id UUID REFERENCES application_systems(id);


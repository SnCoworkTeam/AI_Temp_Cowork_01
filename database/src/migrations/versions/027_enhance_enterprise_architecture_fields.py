"""enhance enterprise architecture fields

Revision ID: 027
Revises: 026
Create Date: 2025-12-12

增强企业架构模型字段，补充缺失的字段
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 增强ApplicationSystem字段
    op.add_column('application_systems', sa.Column('deployment_model', sa.String(50), nullable=True, comment='部署模式: on-premise, cloud, hybrid'))
    op.add_column('application_systems', sa.Column('code', sa.String(100), nullable=True, comment='系统编码'))
    op.add_column('application_systems', sa.Column('criticality', sa.String(50), nullable=True, comment='关键性: critical, high, medium, low'))
    op.add_column('application_systems', sa.Column('availability_requirement', sa.String(50), nullable=True, comment='可用性要求: 99.9%, 99.99%, 99.999%'))
    op.add_column('application_systems', sa.Column('support_team', sa.String(255), nullable=True, comment='支持团队'))
    op.add_column('application_systems', sa.Column('cost_center', sa.String(100), nullable=True, comment='成本中心'))
    op.add_column('application_systems', sa.Column('license_info', JSONB(), nullable=True, comment='许可证信息'))
    op.add_column('application_systems', sa.Column('integration_points', JSONB(), nullable=True, comment='集成点列表'))
    
    # 2. 增强ApplicationService字段
    op.add_column('application_services', sa.Column('code', sa.String(100), nullable=True, comment='服务编码'))
    op.add_column('application_services', sa.Column('status', sa.String(50), nullable=True, default='active', comment='状态'))
    op.add_column('application_services', sa.Column('version', sa.String(50), nullable=True, comment='版本'))
    op.add_column('application_services', sa.Column('health_check_endpoint', sa.String(500), nullable=True, comment='健康检查端点'))
    op.add_column('application_services', sa.Column('service_dependencies', JSONB(), nullable=True, comment='服务依赖列表'))
    
    # 3. 增强APIInterface字段
    op.add_column('api_interfaces', sa.Column('status', sa.String(50), nullable=True, default='active', comment='状态'))
    op.add_column('api_interfaces', sa.Column('version', sa.String(50), nullable=True, comment='API版本'))
    op.add_column('api_interfaces', sa.Column('request_schema', JSONB(), nullable=True, comment='请求Schema'))
    op.add_column('api_interfaces', sa.Column('response_schema', JSONB(), nullable=True, comment='响应Schema'))
    op.add_column('api_interfaces', sa.Column('authentication_type', sa.String(50), nullable=True, comment='认证类型'))
    op.add_column('api_interfaces', sa.Column('rate_limit', sa.String(100), nullable=True, comment='限流配置'))
    
    # 4. 增强DataEntity字段
    op.add_column('data_entities', sa.Column('status', sa.String(50), nullable=True, default='active', comment='状态'))
    op.add_column('data_entities', sa.Column('sensitivity_level', sa.String(50), nullable=True, comment='敏感度级别'))
    op.add_column('data_entities', sa.Column('retention_policy', sa.String(255), nullable=True, comment='保留策略'))
    op.add_column('data_entities', sa.Column('backup_frequency', sa.String(100), nullable=True, comment='备份频率'))
    op.add_column('data_entities', sa.Column('data_volume', sa.String(100), nullable=True, comment='数据量'))
    op.add_column('data_entities', sa.Column('access_control', JSONB(), nullable=True, comment='访问控制规则'))
    
    # 5. 增强DataModel字段
    op.add_column('data_models', sa.Column('model_type', sa.String(100), nullable=True, comment='模型类型: conceptual, logical, physical'))
    op.add_column('data_models', sa.Column('application_system_id', sa.UUID(), sa.ForeignKey('application_systems.id', ondelete='SET NULL'), nullable=True, comment='所属应用系统ID'))
    op.add_column('data_models', sa.Column('status', sa.String(50), nullable=True, default='active', comment='状态'))
    
    # 6. 增强DataFlow字段
    op.add_column('data_flows', sa.Column('flow_type', sa.String(100), nullable=True, comment='数据流类型: batch, real-time, near-real-time'))
    op.add_column('data_flows', sa.Column('source_system_id', sa.UUID(), sa.ForeignKey('application_systems.id', ondelete='SET NULL'), nullable=True, comment='源系统ID'))
    op.add_column('data_flows', sa.Column('target_system_id', sa.UUID(), sa.ForeignKey('application_systems.id', ondelete='SET NULL'), nullable=True, comment='目标系统ID'))
    op.add_column('data_flows', sa.Column('frequency', sa.String(100), nullable=True, comment='传输频率'))
    op.add_column('data_flows', sa.Column('volume', sa.String(100), nullable=True, comment='数据量'))
    op.add_column('data_flows', sa.Column('status', sa.String(50), nullable=True, default='active', comment='状态'))
    
    # 7. 增强BusinessProcess字段
    op.add_column('business_processes', sa.Column('code', sa.String(100), nullable=True, comment='流程编码'))
    op.add_column('business_processes', sa.Column('priority', sa.String(50), nullable=True, comment='优先级'))
    op.add_column('business_processes', sa.Column('kpi_metrics', JSONB(), nullable=True, comment='KPI指标'))
    op.add_column('business_processes', sa.Column('pain_points', JSONB(), nullable=True, comment='痛点列表'))
    op.add_column('business_processes', sa.Column('improvement_opportunities', JSONB(), nullable=True, comment='改进机会'))
    
    # 8. 增强BusinessCapability字段
    op.add_column('business_capabilities', sa.Column('code', sa.String(100), nullable=True, comment='能力编码'))
    op.add_column('business_capabilities', sa.Column('maturity_level', sa.String(50), nullable=True, comment='成熟度级别'))
    op.add_column('business_capabilities', sa.Column('business_value', sa.String(100), nullable=True, comment='业务价值'))
    op.add_column('business_capabilities', sa.Column('investment_priority', sa.String(50), nullable=True, comment='投资优先级'))
    
    # 9. 增强TechnologyInstance字段（补充description）
    op.add_column('technology_instances', sa.Column('description', sa.Text(), nullable=True, comment='实例描述'))
    
    # 创建索引
    op.create_index('idx_application_systems_code', 'application_systems', ['code'])
    op.create_index('idx_application_services_code', 'application_services', ['code'])
    op.create_index('idx_business_processes_code', 'business_processes', ['code'])
    op.create_index('idx_business_capabilities_code', 'business_capabilities', ['code'])


def downgrade():
    # 删除索引
    op.drop_index('idx_business_capabilities_code', 'business_capabilities')
    op.drop_index('idx_business_processes_code', 'business_processes')
    op.drop_index('idx_application_services_code', 'application_services')
    op.drop_index('idx_application_systems_code', 'application_systems')
    
    # 删除字段
    op.drop_column('technology_instances', 'description')
    op.drop_column('business_capabilities', 'investment_priority')
    op.drop_column('business_capabilities', 'business_value')
    op.drop_column('business_capabilities', 'maturity_level')
    op.drop_column('business_capabilities', 'code')
    op.drop_column('business_processes', 'improvement_opportunities')
    op.drop_column('business_processes', 'pain_points')
    op.drop_column('business_processes', 'kpi_metrics')
    op.drop_column('business_processes', 'priority')
    op.drop_column('business_processes', 'code')
    op.drop_column('data_flows', 'status')
    op.drop_column('data_flows', 'volume')
    op.drop_column('data_flows', 'frequency')
    op.drop_column('data_flows', 'target_system_id')
    op.drop_column('data_flows', 'source_system_id')
    op.drop_column('data_flows', 'flow_type')
    op.drop_column('data_models', 'status')
    op.drop_column('data_models', 'application_system_id')
    op.drop_column('data_models', 'model_type')
    op.drop_column('data_entities', 'access_control')
    op.drop_column('data_entities', 'data_volume')
    op.drop_column('data_entities', 'backup_frequency')
    op.drop_column('data_entities', 'retention_policy')
    op.drop_column('data_entities', 'sensitivity_level')
    op.drop_column('data_entities', 'status')
    op.drop_column('api_interfaces', 'rate_limit')
    op.drop_column('api_interfaces', 'authentication_type')
    op.drop_column('api_interfaces', 'response_schema')
    op.drop_column('api_interfaces', 'request_schema')
    op.drop_column('api_interfaces', 'version')
    op.drop_column('api_interfaces', 'status')
    op.drop_column('application_services', 'service_dependencies')
    op.drop_column('application_services', 'health_check_endpoint')
    op.drop_column('application_services', 'version')
    op.drop_column('application_services', 'status')
    op.drop_column('application_services', 'code')
    op.drop_column('application_systems', 'integration_points')
    op.drop_column('application_systems', 'license_info')
    op.drop_column('application_systems', 'cost_center')
    op.drop_column('application_systems', 'support_team')
    op.drop_column('application_systems', 'availability_requirement')
    op.drop_column('application_systems', 'criticality')
    op.drop_column('application_systems', 'code')
    op.drop_column('application_systems', 'deployment_model')


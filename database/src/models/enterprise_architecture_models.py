"""
企业架构相关数据模型
业务架构、应用架构、数据架构、技术架构
"""
from sqlalchemy import (
    Column, String, Integer, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from .base import BaseModel, TimestampMixin


# ========== 业务架构模型 ==========

class BusinessProcess(BaseModel, TimestampMixin):
    """业务流程模型"""
    __tablename__ = "business_processes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="流程ID")
    name = Column(String(255), nullable=False, index=True, comment="流程名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="流程编码")
    description = Column(Text, nullable=True, comment="流程描述")
    owner = Column(String(255), nullable=True, comment="负责人")
    status = Column(String(50), nullable=True, default="active", index=True, comment="状态")
    classification = Column(String(100), nullable=True, comment="分类")
    level = Column(Integer, nullable=True, default=1, comment="层级")
    priority = Column(String(50), nullable=True, comment="优先级")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("business_processes.id", ondelete="SET NULL"), nullable=True, index=True, comment="父流程ID")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True, comment="负责组织ID")
    kpi_metrics = Column(JSONB, nullable=True, comment="KPI指标")
    pain_points = Column(JSONB, nullable=True, comment="痛点列表")
    improvement_opportunities = Column(JSONB, nullable=True, comment="改进机会")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    parent = relationship("BusinessProcess", remote_side=[id], backref="children")
    organization = relationship("OrganizationUnit", backref="processes")
    
    __table_args__ = (
        Index('idx_business_processes_name', 'name'),
        Index('idx_business_processes_status', 'status'),
    )
    
    def __repr__(self):
        return f"<BusinessProcess(id={self.id}, name={self.name})>"


class BusinessCapability(BaseModel, TimestampMixin):
    """业务能力模型"""
    __tablename__ = "business_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="能力ID")
    name = Column(String(255), nullable=False, index=True, comment="能力名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="能力编码")
    description = Column(Text, nullable=True, comment="能力描述")
    level = Column(Integer, nullable=True, default=1, comment="层级")
    maturity_level = Column(String(50), nullable=True, comment="成熟度级别")
    business_value = Column(String(100), nullable=True, comment="业务价值")
    investment_priority = Column(String(50), nullable=True, comment="投资优先级")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("business_capabilities.id", ondelete="SET NULL"), nullable=True, index=True, comment="父能力ID")
    owner_organization_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True, comment="拥有组织ID")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    parent = relationship("BusinessCapability", remote_side=[id], backref="children")
    owner_organization = relationship("OrganizationUnit", backref="owned_capabilities")
    
    __table_args__ = (
        Index('idx_business_capabilities_name', 'name'),
    )
    
    def __repr__(self):
        return f"<BusinessCapability(id={self.id}, name={self.name})>"


class BusinessService(BaseModel, TimestampMixin):
    """业务服务模型"""
    __tablename__ = "business_services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="服务ID")
    name = Column(String(255), nullable=False, index=True, comment="服务名称")
    description = Column(Text, nullable=True, comment="服务描述")
    service_type = Column(String(100), nullable=True, comment="服务类型")
    endpoint = Column(String(500), nullable=True, comment="服务端点")
    status = Column(String(50), nullable=True, default="active", index=True, comment="状态")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    __table_args__ = (
        Index('idx_business_services_name', 'name'),
    )
    
    def __repr__(self):
        return f"<BusinessService(id={self.id}, name={self.name})>"


# ========== 应用架构模型 ==========

class ApplicationSystem(BaseModel, TimestampMixin):
    """应用系统模型"""
    __tablename__ = "application_systems"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="系统ID")
    name = Column(String(255), nullable=False, index=True, comment="系统名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="系统编码")
    description = Column(Text, nullable=True, comment="系统描述")
    system_type = Column(String(100), nullable=True, comment="系统类型")
    system_category = Column(String(50), nullable=True, index=True, comment="系统分类: Core, Peripheral, Custom")
    vendor = Column(String(255), nullable=True, comment="供应商")
    version = Column(String(50), nullable=True, comment="版本")
    deployment_model = Column(String(50), nullable=True, comment="部署模式: on-premise, cloud, hybrid")
    status = Column(String(50), nullable=True, default="active", index=True, comment="状态")
    owner = Column(String(255), nullable=True, comment="负责人")
    criticality = Column(String(50), nullable=True, comment="关键性: critical, high, medium, low")
    availability_requirement = Column(String(50), nullable=True, comment="可用性要求: 99.9%, 99.99%, 99.999%")
    support_team = Column(String(255), nullable=True, comment="支持团队")
    cost_center = Column(String(100), nullable=True, comment="成本中心")
    business_owner_org_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True, comment="业务拥有组织ID")
    license_info = Column(JSONB, nullable=True, comment="许可证信息")
    integration_points = Column(JSONB, nullable=True, comment="集成点列表")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    services = relationship("ApplicationService", back_populates="application", cascade="all, delete-orphan")
    business_owner_org = relationship("OrganizationUnit", backref="managed_systems")
    
    __table_args__ = (
        Index('idx_application_systems_name', 'name'),
    )
    
    def __repr__(self):
        return f"<ApplicationSystem(id={self.id}, name={self.name})>"


class ApplicationService(BaseModel, TimestampMixin):
    """应用服务模型"""
    __tablename__ = "application_services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="服务ID")
    application_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="CASCADE"), nullable=True, index=True, comment="应用系统ID")
    name = Column(String(255), nullable=False, index=True, comment="服务名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="服务编码")
    description = Column(Text, nullable=True, comment="服务描述")
    service_type = Column(String(100), nullable=True, comment="服务类型")
    protocol = Column(String(50), nullable=True, comment="协议")
    endpoint = Column(String(500), nullable=True, comment="服务端点")
    version = Column(String(50), nullable=True, comment="版本")
    status = Column(String(50), nullable=True, default="active", comment="状态")
    health_check_endpoint = Column(String(500), nullable=True, comment="健康检查端点")
    service_dependencies = Column(JSONB, nullable=True, comment="服务依赖列表")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    application = relationship("ApplicationSystem", back_populates="services")
    api_interfaces = relationship("APIInterface", back_populates="service", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_application_services_name', 'name'),
    )
    
    def __repr__(self):
        return f"<ApplicationService(id={self.id}, name={self.name})>"


class APIInterface(BaseModel, TimestampMixin):
    """API接口模型"""
    __tablename__ = "api_interfaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="接口ID")
    name = Column(String(255), nullable=True, comment="接口名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="接口编码")
    service_id = Column(UUID(as_uuid=True), ForeignKey("application_services.id", ondelete="CASCADE"), nullable=True, index=True, comment="应用服务ID")
    application_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属应用系统ID")
    path = Column(String(500), nullable=False, comment="接口路径")
    endpoint = Column(String(500), nullable=True, comment="接口端点（完整URL）")
    method = Column(String(10), nullable=False, comment="HTTP方法")
    interface_type = Column(String(100), nullable=True, index=True, comment="接口类型: REST, SOAP, GraphQL等")
    protocol = Column(String(50), nullable=True, comment="协议")
    version = Column(String(50), nullable=True, comment="API版本")
    status = Column(String(50), nullable=True, default="active", comment="状态")
    description = Column(Text, nullable=True, comment="接口描述")
    request_schema = Column(JSONB, nullable=True, comment="请求Schema")
    response_schema = Column(JSONB, nullable=True, comment="响应Schema")
    authentication_type = Column(String(50), nullable=True, comment="认证类型")
    rate_limit = Column(String(100), nullable=True, comment="限流配置")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    service = relationship("ApplicationService", back_populates="api_interfaces")
    application_system = relationship("ApplicationSystem", backref="api_interfaces")
    
    __table_args__ = (
        Index('idx_api_interfaces_path_method', 'path', 'method'),
    )
    
    def __repr__(self):
        return f"<APIInterface(id={self.id}, path={self.path}, method={self.method})>"


# ========== 数据架构模型 ==========

class DataEntity(BaseModel, TimestampMixin):
    """数据实体模型"""
    __tablename__ = "data_entities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="实体ID")
    name = Column(String(255), nullable=False, index=True, comment="实体名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="实体编码")
    description = Column(Text, nullable=True, comment="实体描述")
    schema = Column(JSONB, nullable=True, comment="数据模式")
    schema_name = Column(String(255), nullable=True, comment="Schema名称")
    table_name = Column(String(255), nullable=True, index=True, comment="表名（如果是数据库表）")
    entity_type = Column(String(100), nullable=True, comment="实体类型")
    storage_location = Column(String(500), nullable=True, comment="存储位置")
    application_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属应用系统ID")
    technology_system_id = Column(UUID(as_uuid=True), ForeignKey("technology_instances.id", ondelete="SET NULL"), nullable=True, index=True, comment="存储的技术系统ID（数据库）")
    data_model_id = Column(UUID(as_uuid=True), ForeignKey("data_models.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属数据模型ID")
    status = Column(String(50), nullable=True, default="active", comment="状态")
    sensitivity_level = Column(String(50), nullable=True, comment="敏感度级别")
    retention_policy = Column(String(255), nullable=True, comment="保留策略")
    backup_frequency = Column(String(100), nullable=True, comment="备份频率")
    data_volume = Column(String(100), nullable=True, comment="数据量")
    access_control = Column(JSONB, nullable=True, comment="访问控制规则")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    source_flows = relationship("DataFlow", foreign_keys="DataFlow.source_entity_id", back_populates="source_entity")
    target_flows = relationship("DataFlow", foreign_keys="DataFlow.target_entity_id", back_populates="target_entity")
    application_system = relationship("ApplicationSystem", backref="data_entities")
    technology_system = relationship("TechnologyInstance", backref="stored_entities")
    data_model = relationship("DataModel", backref="entities")
    
    __table_args__ = (
        Index('idx_data_entities_name', 'name'),
    )
    
    def __repr__(self):
        return f"<DataEntity(id={self.id}, name={self.name})>"


class DataModel(BaseModel, TimestampMixin):
    """数据模型模型"""
    __tablename__ = "data_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="模型ID")
    name = Column(String(255), nullable=False, index=True, comment="模型名称")
    description = Column(Text, nullable=True, comment="模型描述")
    model_type = Column(String(100), nullable=True, comment="模型类型: conceptual, logical, physical")
    version = Column(String(50), nullable=True, comment="版本")
    application_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属应用系统ID")
    definition = Column(JSONB, nullable=True, comment="模型定义")
    status = Column(String(50), nullable=True, default="active", comment="状态")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    __table_args__ = (
        Index('idx_data_models_name', 'name'),
    )
    
    def __repr__(self):
        return f"<DataModel(id={self.id}, name={self.name})>"


class DataFlow(BaseModel, TimestampMixin):
    """数据流模型"""
    __tablename__ = "data_flows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="数据流ID")
    name = Column(String(255), nullable=False, comment="数据流名称")
    description = Column(Text, nullable=True, comment="数据流描述")
    flow_type = Column(String(100), nullable=True, comment="数据流类型: batch, real-time, near-real-time")
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("data_entities.id", ondelete="SET NULL"), nullable=True, index=True, comment="源实体ID")
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("data_entities.id", ondelete="SET NULL"), nullable=True, index=True, comment="目标实体ID")
    source_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="源系统ID")
    target_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="目标系统ID")
    transformation = Column(Text, nullable=True, comment="转换规则")
    frequency = Column(String(100), nullable=True, comment="传输频率")
    volume = Column(String(100), nullable=True, comment="数据量")
    status = Column(String(50), nullable=True, default="active", comment="状态")
    neo4j_relationship_id = Column(String(255), nullable=True, comment="Neo4j关系ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    source_entity = relationship("DataEntity", foreign_keys=[source_entity_id], back_populates="source_flows")
    target_entity = relationship("DataEntity", foreign_keys=[target_entity_id], back_populates="target_flows")
    
    def __repr__(self):
        return f"<DataFlow(id={self.id}, name={self.name})>"


# ========== 技术架构模型 ==========

class TechnologyComponent(BaseModel, TimestampMixin):
    """技术组件模型"""
    __tablename__ = "technology_components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="组件ID")
    name = Column(String(255), nullable=False, index=True, comment="组件名称")
    description = Column(Text, nullable=True, comment="组件描述")
    component_type = Column(String(100), nullable=True, comment="组件类型")
    version = Column(String(50), nullable=True, comment="版本")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    __table_args__ = (
        Index('idx_technology_components_name', 'name'),
    )
    
    def __repr__(self):
        return f"<TechnologyComponent(id={self.id}, name={self.name})>"


class TechnologyStack(BaseModel, TimestampMixin):
    """技术栈模型"""
    __tablename__ = "technology_stacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="技术栈ID")
    name = Column(String(255), nullable=False, index=True, comment="技术栈名称")
    description = Column(Text, nullable=True, comment="技术栈描述")
    category = Column(String(100), nullable=True, comment="类别")
    components = Column(JSONB, nullable=True, comment="组件列表")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    __table_args__ = (
        Index('idx_technology_stacks_name', 'name'),
    )
    
    def __repr__(self):
        return f"<TechnologyStack(id={self.id}, name={self.name})>"


class InfrastructureComponent(BaseModel, TimestampMixin):
    """基础设施组件模型"""
    __tablename__ = "infrastructure_components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="基础设施组件ID")
    name = Column(String(255), nullable=False, index=True, comment="组件名称")
    description = Column(Text, nullable=True, comment="组件描述")
    component_type = Column(String(100), nullable=True, comment="组件类型")
    specifications = Column(JSONB, nullable=True, comment="规格说明")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    __table_args__ = (
        Index('idx_infrastructure_components_name', 'name'),
    )
    
    def __repr__(self):
        return f"<InfrastructureComponent(id={self.id}, name={self.name})>"


# ========== 架构关系模型 ==========

class ArchitectureRelationship(BaseModel, TimestampMixin):
    """架构关系模型"""
    __tablename__ = "architecture_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="关系ID")
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="源实体ID")
    source_type = Column(String(100), nullable=False, index=True, comment="源实体类型")
    target_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="目标实体ID")
    target_type = Column(String(100), nullable=False, index=True, comment="目标实体类型")
    relationship_type = Column(String(100), nullable=False, index=True, comment="关系类型")
    description = Column(Text, nullable=True, comment="关系描述")
    neo4j_relationship_id = Column(String(255), nullable=True, comment="Neo4j关系ID")
    properties = Column(JSONB, nullable=True, default=dict, comment="关系属性")
    
    __table_args__ = (
        Index('idx_architecture_relationships_source', 'source_type', 'source_id'),
        Index('idx_architecture_relationships_target', 'target_type', 'target_id'),
        Index('idx_architecture_relationships_type', 'relationship_type'),
    )
    
    def __repr__(self):
        return f"<ArchitectureRelationship(id={self.id}, {self.source_type}:{self.source_id} -> {self.target_type}:{self.target_id})>"


# ========== 组织架构模型 ==========

class OrganizationUnit(BaseModel, TimestampMixin):
    """组织单元模型"""
    __tablename__ = "organization_units"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="组织ID")
    name = Column(String(255), nullable=False, index=True, comment="组织名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="组织编码")
    description = Column(Text, nullable=True, comment="组织描述")
    organization_type = Column(String(100), nullable=True, index=True, comment="组织类型: Department, Team, Division等")
    level = Column(Integer, nullable=True, default=1, comment="组织层级")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True, comment="上级组织ID")
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="负责人ID")
    location = Column(String(255), nullable=True, comment="地理位置")
    status = Column(String(50), nullable=True, default="active", index=True, comment="状态")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    parent = relationship("OrganizationUnit", remote_side=[id], backref="children")
    
    __table_args__ = (
        Index('idx_organization_units_name', 'name'),
        Index('idx_organization_units_code', 'code'),
        Index('idx_organization_units_status', 'status'),
        Index('idx_organization_units_type', 'organization_type'),
    )
    
    def __repr__(self):
        return f"<OrganizationUnit(id={self.id}, name={self.name})>"


class BusinessRole(BaseModel, TimestampMixin):
    """业务角色模型"""
    __tablename__ = "business_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="角色ID")
    name = Column(String(255), nullable=False, index=True, comment="角色名称")
    code = Column(String(100), nullable=True, unique=True, index=True, comment="角色编码")
    description = Column(Text, nullable=True, comment="角色描述")
    role_type = Column(String(100), nullable=True, index=True, comment="角色类型")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属组织ID")
    responsibilities = Column(JSONB, nullable=True, comment="职责列表")
    required_skills = Column(JSONB, nullable=True, comment="所需技能")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    organization = relationship("OrganizationUnit", backref="roles")
    
    __table_args__ = (
        Index('idx_business_roles_name', 'name'),
        Index('idx_business_roles_code', 'code'),
    )
    
    def __repr__(self):
        return f"<BusinessRole(id={self.id}, name={self.name})>"


# ========== 技术架构增强模型 ==========

class TechnologyType(BaseModel, TimestampMixin):
    """技术类型模型（按技术分类）"""
    __tablename__ = "technology_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="类型ID")
    name = Column(String(255), nullable=False, unique=True, index=True, comment="技术名称，如Oracle")
    category = Column(String(100), nullable=False, index=True, comment="技术类别: Database, Middleware, Infrastructure, AIPlatform")
    description = Column(Text, nullable=True, comment="技术描述")
    standard_version = Column(String(50), nullable=True, comment="企业标准版本，如19c")
    recommended_version = Column(String(50), nullable=True, comment="推荐版本")
    lifecycle_status = Column(String(50), nullable=True, default="strategic", index=True, comment="生命周期状态: strategic(战略), tactical(战术), legacy(遗留)")
    owner_team = Column(String(255), nullable=True, comment="技术负责人团队")
    governance_status = Column(String(50), nullable=True, comment="治理状态: approved(已批准), under_review(审查中), deprecated(已弃用)")
    usage_guidelines = Column(Text, nullable=True, comment="使用指南")
    instance_count = Column(Integer, nullable=True, default=0, comment="实例数量")
    version_diversity = Column(JSONB, nullable=True, comment="版本多样性统计")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    instances = relationship("TechnologyInstance", foreign_keys="TechnologyInstance.technology_type_id", back_populates="technology_type_ref", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_technology_types_category', 'category'),
        Index('idx_technology_types_lifecycle', 'lifecycle_status'),
    )
    
    def __repr__(self):
        return f"<TechnologyType(id={self.id}, name={self.name})>"


class TechnologyInstance(BaseModel, TimestampMixin):
    """技术实例模型（按系统分类）"""
    __tablename__ = "technology_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="实例ID")
    name = Column(String(255), nullable=False, index=True, comment="实例名称，如Oracle-SAP-ERP-001")
    instance_id = Column(String(255), nullable=True, unique=True, index=True, comment="实例标识")
    application_system_id = Column(UUID(as_uuid=True), ForeignKey("application_systems.id", ondelete="SET NULL"), nullable=True, index=True, comment="归属应用系统ID")
    owner_department = Column(String(255), nullable=True, comment="负责部门")
    owner_team = Column(String(255), nullable=True, comment="负责团队")
    technology_type = Column(String(100), nullable=False, index=True, comment="技术类型: Database, Middleware, Infrastructure, AIPlatform")
    technology_name = Column(String(255), nullable=False, index=True, comment="技术名称: Oracle, Redis, Docker等")
    technology_type_id = Column(UUID(as_uuid=True), ForeignKey("technology_types.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联技术类型ID")
    vendor = Column(String(255), nullable=True, comment="供应商")
    version = Column(String(50), nullable=True, comment="版本")
    deployment_type = Column(String(50), nullable=True, default="independent", index=True, comment="部署类型: independent(独立), dedicated(专用), shared(共享)")
    host = Column(String(255), nullable=True, comment="主机地址")
    port = Column(Integer, nullable=True, comment="端口")
    location = Column(String(255), nullable=True, comment="部署位置")
    capacity = Column(String(100), nullable=True, comment="容量，如500GB")
    resource_allocation = Column(String(50), nullable=True, default="dedicated", comment="资源分配: dedicated(专用), shared(共享)")
    description = Column(Text, nullable=True, comment="实例描述")
    status = Column(String(50), nullable=True, default="active", index=True, comment="状态: active, inactive, planned, deprecated")
    lifecycle_status = Column(String(50), nullable=True, comment="生命周期状态: strategic, tactical, legacy")
    neo4j_node_id = Column(String(255), nullable=True, comment="Neo4j节点ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    application_system = relationship("ApplicationSystem", backref="technology_instances")
    technology_type_ref = relationship("TechnologyType", foreign_keys=[technology_type_id], back_populates="instances")
    
    __table_args__ = (
        Index('idx_tech_instances_app', 'application_system_id'),
        Index('idx_tech_instances_tech_name', 'technology_name'),
        Index('idx_tech_instances_tech_type', 'technology_type'),
        Index('idx_tech_instances_type', 'technology_type_id'),
        Index('idx_tech_instances_deployment', 'deployment_type'),
    )
    
    def __repr__(self):
        return f"<TechnologyInstance(id={self.id}, name={self.name})>"


class OrganizationBusinessRelationship(BaseModel, TimestampMixin):
    """组织与业务关系模型"""
    __tablename__ = "organization_business_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="关系ID")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organization_units.id", ondelete="CASCADE"), nullable=False, index=True, comment="组织ID")
    entity_type = Column(String(100), nullable=False, index=True, comment="实体类型: BusinessCapability, BusinessProcess, ApplicationSystem等")
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="实体ID")
    relationship_type = Column(String(100), nullable=False, index=True, comment="关系类型: OWNS, EXECUTES, USES, MANAGES等")
    responsibility_level = Column(String(50), nullable=True, comment="责任级别: primary, secondary, supporting")
    neo4j_relationship_id = Column(String(255), nullable=True, comment="Neo4j关系ID")
    meta_data = Column(JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    organization = relationship("OrganizationUnit", backref="business_relationships")
    
    __table_args__ = (
        Index('idx_org_business_rel_org', 'organization_id'),
        Index('idx_org_business_rel_entity', 'entity_type', 'entity_id'),
        Index('idx_org_business_rel_type', 'relationship_type'),
    )
    
    def __repr__(self):
        return f"<OrganizationBusinessRelationship(id={self.id}, org={self.organization_id}, entity={self.entity_type})>"


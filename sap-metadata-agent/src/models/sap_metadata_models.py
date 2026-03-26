"""
SAP元数据模型定义
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SAPAssetType(str, Enum):
    """SAP资产类型"""
    BUSINESS_OBJECT = "business_object"      # 业务对象（销售订单、采购订单等）
    MASTER_DATA = "master_data"              # 主数据（客户、物料、供应商）
    TRANSACTION_DATA = "transaction_data"    # 事务数据（订单、发票、交货单）
    CONFIGURATION = "configuration"          # 配置数据（组织架构、参数）
    REPORT = "report"                        # 报表和查询
    WORKFLOW = "workflow"                    # 业务流程
    INTERFACE = "interface"                  # 接口和集成点
    TABLE = "table"                         # 数据库表
    VIEW = "view"                           # 数据库视图


class SAPBusinessDomain(str, Enum):
    """SAP业务领域"""
    SALES = "sales"                          # 销售与分销
    MATERIAL_MANAGEMENT = "material_management"  # 物料管理
    FINANCE = "finance"                      # 财务会计
    CONTROLLING = "controlling"              # 管理会计
    HUMAN_RESOURCES = "human_resources"      # 人力资源
    PRODUCTION = "production"                # 生产计划
    QUALITY_MANAGEMENT = "quality_management" # 质量管理
    WAREHOUSE_MANAGEMENT = "warehouse_management"  # 仓库管理
    PLANT_MAINTENANCE = "plant_maintenance"  # 工厂维护


class SAPDataAsset(BaseModel):
    """SAP数据资产模型"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    asset_type: SAPAssetType
    sap_table_name: Optional[str] = None  # SAP表名（如KNA1）
    sap_object_type: Optional[str] = None  # SAP对象类型
    sap_module: Optional[SAPBusinessDomain] = None
    odata_service: Optional[str] = None
    odata_entity: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    classification: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # 语义增强字段
    business_terms: List[str] = Field(default_factory=list, description="关联的业务术语")
    semantic_embedding: Optional[List[float]] = Field(None, description="语义向量嵌入，用于语义搜索")
    semantic_relationships: List[Dict[str, Any]] = Field(default_factory=list, description="语义关系列表")


class SAPBusinessEntity(BaseModel):
    """SAP业务实体模型"""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    entity_type: str  # customer, vendor, material, product, etc.
    sap_table_name: Optional[str] = None
    key_fields: List[str] = Field(default_factory=list)
    related_tables: List[str] = Field(default_factory=list)
    business_domain: Optional[SAPBusinessDomain] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SAPBusinessProcess(BaseModel):
    """SAP业务流程模型"""
    name: str
    display_name: str
    description: Optional[str] = None
    domain: SAPBusinessDomain
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    involved_data_assets: List[str] = Field(default_factory=list)
    sap_transactions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SAPTableInfo(BaseModel):
    """SAP表信息模型"""
    table_name: str
    table_type: str  # TRANSP, CLUSTER, POOL
    description: Optional[str] = None
    fields: List[Dict[str, Any]] = Field(default_factory=list)
    primary_key: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = Field(default_factory=list)
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None


class SAPDiscoveryResult(BaseModel):
    """SAP发现结果"""
    data_assets: List[SAPDataAsset] = Field(default_factory=list)
    business_entities: List[SAPBusinessEntity] = Field(default_factory=list)
    business_processes: List[SAPBusinessProcess] = Field(default_factory=list)
    tables_discovered: int = 0
    odata_services_discovered: int = 0
    discovery_time: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)



"""
数据资产元数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from database.src.models.base import Base, TimestampMixin
from shared_libs.src.models.metadata_models import DataQualityMetrics


class DataAssetType(str, enum.Enum):
    """数据资产类型"""
    DATASET = "dataset"
    TABLE = "table"
    VIEW = "view"
    FILE = "file"
    STREAM = "stream"
    API = "api"


class DataAssetStatus(str, enum.Enum):
    """数据资产状态"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class DataAsset(Base, TimestampMixin):
    """数据资产元数据表"""
    __tablename__ = "data_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    # 使用native_enum=False和values_callable确保使用枚举值而不是名称
    asset_type = Column(SQLEnum(DataAssetType, native_enum=False, values_callable=lambda x: [e.value for e in DataAssetType]), nullable=False, index=True)
    status = Column(SQLEnum(DataAssetStatus, native_enum=False, values_callable=lambda x: [e.value for e in DataAssetStatus]), default=DataAssetStatus.ACTIVE, index=True)
    
    # 数据源信息
    source_system = Column(String(100))
    source_path = Column(String(500))
    source_connection = Column(String(255))
    
    # 数据特征
    schema_info = Column(JSON)  # 数据schema信息
    sample_data = Column(JSON)  # 样本数据
    data_quality_metrics = Column(JSON)  # 数据质量指标
    
    # 业务信息
    business_owner = Column(String(100))
    technical_owner = Column(String(100))
    tags = Column(JSON)  # 标签列表（旧字段，保留向后兼容）
    classification = Column(String(50))  # 数据分类（主分类，保留向后兼容）
    
    # 分类维度（新字段，支持三层分类体系）
    classification_dimensions = Column(JSON, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    standardized_tags = Column(JSON, nullable=True, comment='标准化标签列表')
    
    # 兼容属性：从新字段或旧字段获取主分类
    @property
    def primary_classification(self) -> Optional[str]:
        """从新字段或旧字段获取主分类"""
        if self.classification_dimensions and isinstance(self.classification_dimensions, dict):
            return self.classification_dimensions.get('primary')
        return self.classification
    
    # 统计信息
    record_count = Column(Integer)
    size_bytes = Column(Integer)
    last_updated = Column(DateTime)
    update_frequency = Column(String(50))  # 更新频率
    
    # 元数据
    extra_metadata = Column("metadata", JSON)  # 扩展元数据（使用 metadata 作为数据库列名）


class DataAssetSchema(BaseModel):
    """数据资产Schema（API响应）"""
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    asset_type: DataAssetType
    status: DataAssetStatus
    source_system: Optional[str] = None
    source_path: Optional[str] = None
    source_connection: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    data_quality_metrics: Optional[Dict[str, Any]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification: Optional[str] = None  # 主分类，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    record_count: Optional[int] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None
    update_frequency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataAssetCreate(BaseModel):
    """创建数据资产请求"""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    asset_type: DataAssetType
    status: DataAssetStatus = DataAssetStatus.ACTIVE
    source_system: Optional[str] = None
    source_path: Optional[str] = None
    source_connection: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    data_quality_metrics: Optional[Dict[str, Any]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification: Optional[str] = None  # 主分类，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    record_count: Optional[int] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None
    update_frequency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class DataAssetUpdate(BaseModel):
    """更新数据资产请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DataAssetStatus] = None
    source_system: Optional[str] = None
    source_path: Optional[str] = None
    source_connection: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    data_quality_metrics: Optional[Dict[str, Any]] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification: Optional[str] = None  # 主分类，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    record_count: Optional[int] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None
    update_frequency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class DataAssetDetail(BaseModel):
    """数据资产详情（包含扩展信息）"""
    # 基础信息
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    asset_type: DataAssetType
    status: DataAssetStatus
    
    # 数据源信息
    source_system: Optional[str] = None
    source_path: Optional[str] = None
    source_connection: Optional[str] = None
    
    # 数据特征
    schema_info: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, Any]] = None
    data_quality_metrics: Optional[Dict[str, Any]] = None
    
    # 业务信息
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification: Optional[str] = None  # 主分类，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    category: Optional[str] = None  # 分类（旧字段，保留）
    domain: Optional[str] = None   # 业务域（旧字段，保留）
    
    # 统计信息
    record_count: Optional[int] = None
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None
    update_frequency: Optional[str] = None
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    
    # 血缘关系（简化版）
    upstream_lineage: Optional[List[Dict[str, Any]]] = None  # 上游血缘
    downstream_lineage: Optional[List[Dict[str, Any]]] = None  # 下游血缘
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchResults(BaseModel):
    """搜索结果"""
    query: str
    total: int
    results: List[Dict[str, Any]]
    facets: Optional[Dict[str, Any]] = None  # 分面信息（如按类型分组）
    
    class Config:
        from_attributes = True


"""
数据血缘模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from database.src.models.base import Base, TimestampMixin


class LineageType(str, enum.Enum):
    """血缘类型"""
    DATA_FLOW = "data_flow"
    TRANSFORMATION = "transformation"
    DEPENDENCY = "dependency"
    DERIVATION = "derivation"


class LineageRelationType(str, enum.Enum):
    """血缘关系类型"""
    READS = "reads"
    WRITES = "writes"
    TRANSFORMS = "transforms"
    DEPENDS_ON = "depends_on"
    DERIVES = "derives"


class DataLineage(Base, TimestampMixin):
    """数据血缘表"""
    __tablename__ = "data_lineage"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(50), nullable=False)  # 源类型：data_asset, ai_model, workflow等
    source_id = Column(String(255), nullable=False, index=True)  # 源ID
    source_asset = Column(String(255), nullable=True, index=True)  # 源资产（便捷字段，格式：type:id）
    target_type = Column(String(50), nullable=False)  # 目标类型
    target_id = Column(String(255), nullable=False, index=True)  # 目标ID
    target_asset = Column(String(255), nullable=True, index=True)  # 目标资产（便捷字段，格式：type:id）
    relation_type = Column(SQLEnum(LineageRelationType), nullable=False)
    lineage_type = Column(SQLEnum(LineageType), nullable=False)
    
    # 关系信息
    transformation = Column(String(255))  # 转换过程名称
    transformation_logic = Column(Text)  # 转换逻辑描述
    transformation_code = Column(Text)  # 转换代码
    business_rules = Column(JSON)  # 业务规则列表
    data_quality_impact = Column(JSON)  # 数据质量影响
    extra_metadata = Column("metadata", JSON)  # 扩展信息（使用 metadata 作为数据库列名）
    
    # 时间信息
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    
    # 索引：复合索引用于快速查询
    __table_args__ = (
        {"comment": "数据血缘关系表，记录数据资产之间的依赖和转换关系"}
    )


class LineageNode(BaseModel):
    """血缘节点（用于图谱展示）"""
    id: str
    type: str  # data_asset, ai_model, workflow等
    name: str
    display_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class LineageEdge(BaseModel):
    """血缘边（用于图谱展示）"""
    source: str
    target: str
    relation_type: LineageRelationType
    lineage_type: LineageType
    transformation_logic: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class LineageGraph(BaseModel):
    """血缘图谱"""
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    
    class Config:
        from_attributes = True


class ImpactAnalysis(BaseModel):
    """影响分析（下游影响）"""
    asset_id: str
    asset_type: str
    asset_name: str
    total_impacted: int  # 受影响的总数
    direct_impacted: int  # 直接受影响的数量
    indirect_impacted: int  # 间接受影响的数量
    impacted_assets: List[Dict[str, Any]]  # 受影响的资产列表
    impact_paths: List[Dict[str, Any]]  # 影响路径
    risk_level: str  # 风险等级：low, medium, high, critical
    recommendations: List[str]  # 建议措施
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    
    class Config:
        from_attributes = True


class RootCauseAnalysis(BaseModel):
    """根因分析（上游溯源）"""
    asset_id: str
    asset_type: str
    asset_name: str
    total_sources: int  # 总来源数
    direct_sources: int  # 直接来源数
    indirect_sources: int  # 间接来源数
    source_assets: List[Dict[str, Any]]  # 来源资产列表
    source_paths: List[Dict[str, Any]]  # 来源路径
    critical_paths: List[Dict[str, Any]]  # 关键路径
    data_quality_issues: List[Dict[str, Any]]  # 数据质量问题
    recommendations: List[str]  # 建议措施
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    
    class Config:
        from_attributes = True


class DataLineageDetail(BaseModel):
    """数据血缘详情（包含完整图谱和分析）"""
    asset_id: str
    asset_type: str
    asset_name: str
    lineage_graph: LineageGraph  # 完整血缘图谱
    upstream_count: int  # 上游数量
    downstream_count: int  # 下游数量
    total_relations: int  # 总关系数
    impact_analysis: Optional[ImpactAnalysis] = None  # 影响分析
    root_cause_analysis: Optional[RootCauseAnalysis] = None  # 根因分析
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    
    class Config:
        from_attributes = True


class DataLineageSchema(BaseModel):
    """数据血缘Schema（API响应）"""
    id: int
    source_type: str
    source_id: str
    source_asset: Optional[str] = None  # 源资产（格式：type:id）
    target_type: str
    target_id: str
    target_asset: Optional[str] = None  # 目标资产（格式：type:id）
    relation_type: LineageRelationType
    lineage_type: LineageType
    transformation: Optional[str] = None
    transformation_logic: Optional[str] = None
    transformation_code: Optional[str] = None
    business_rules: Optional[List[str]] = None
    data_quality_impact: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataLineageCreate(BaseModel):
    """创建数据血缘请求"""
    # 支持两种方式：使用source_asset/target_asset或source_type/source_id/target_type/target_id
    source_asset: Optional[str] = Field(None, description="源资产（格式：type:id），如果提供则自动解析为source_type和source_id")
    source_type: Optional[str] = Field(None, min_length=1, max_length=50, description="源类型")
    source_id: Optional[str] = Field(None, min_length=1, max_length=255, description="源ID")
    target_asset: Optional[str] = Field(None, description="目标资产（格式：type:id），如果提供则自动解析为target_type和target_id")
    target_type: Optional[str] = Field(None, min_length=1, max_length=50, description="目标类型")
    target_id: Optional[str] = Field(None, min_length=1, max_length=255, description="目标ID")
    relation_type: LineageRelationType
    lineage_type: LineageType
    transformation: Optional[str] = Field(None, description="转换过程名称")
    transformation_logic: Optional[str] = Field(None, description="转换逻辑描述")
    transformation_code: Optional[str] = Field(None, description="转换代码")
    business_rules: Optional[List[str]] = Field(None, description="业务规则列表")
    data_quality_impact: Optional[Dict[str, Any]] = Field(None, description="数据质量影响")
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    @model_validator(mode='after')
    def validate_and_parse_assets(self):
        """验证并解析asset字段"""
        # 解析source_asset
        if self.source_asset and not (self.source_type and self.source_id):
            parts = self.source_asset.split(":", 1)
            if len(parts) == 2:
                self.source_type = parts[0]
                self.source_id = parts[1]
        
        # 解析target_asset
        if self.target_asset and not (self.target_type and self.target_id):
            parts = self.target_asset.split(":", 1)
            if len(parts) == 2:
                self.target_type = parts[0]
                self.target_id = parts[1]
        
        # 验证必需字段
        if not (self.source_type and self.source_id):
            raise ValueError("Either source_asset or both source_type and source_id must be provided")
        if not (self.target_type and self.target_id):
            raise ValueError("Either target_asset or both target_type and target_id must be provided")
        
        # 设置asset字段（如果未提供）
        if not self.source_asset:
            self.source_asset = f"{self.source_type}:{self.source_id}"
        if not self.target_asset:
            self.target_asset = f"{self.target_type}:{self.target_id}"
        
        return self


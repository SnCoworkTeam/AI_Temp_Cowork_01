"""
核心元数据模型
提供跨服务使用的元数据Pydantic模型
"""
from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from .enums.data_types import (
    DataAssetType,
    ModelType,
    EntityType,
    WorkflowType,
    LineageRelationType
)
from .enums.quality_levels import (
    QualityLevel,
    QualityScore,
    CompletenessLevel,
    AccuracyLevel
)


class DataAssetMetadata(BaseModel):
    """数据资产元数据模型"""
    id: Optional[str] = Field(None, description="数据资产ID")
    name: str = Field(..., min_length=1, max_length=255, description="资产名称")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    asset_type: DataAssetType = Field(..., description="资产类型")
    source_system: Optional[str] = Field(None, description="源系统")
    source_path: Optional[str] = Field(None, description="源路径")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Schema信息")
    tags: List[str] = Field(default_factory=list, description="标签")
    classification: Optional[str] = Field(None, description="分类")
    business_owner: Optional[str] = Field(None, description="业务负责人")
    technical_owner: Optional[str] = Field(None, description="技术负责人")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AIModelMetadata(BaseModel):
    """AI模型元数据 - 描述AI模型特性"""
    model_id: str = Field(..., description="模型ID")
    model_name: str = Field(..., min_length=1, max_length=255, description="模型名称")
    model_version: str = Field(..., description="模型版本")
    model_type: str = Field(..., description="模型类型")
    framework: str = Field(..., description="框架")
    input_schema: Dict[str, Any] = Field(..., description="输入Schema")
    output_schema: Dict[str, Any] = Field(..., description="输出Schema")
    training_data: str = Field(..., description="训练数据")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")
    fairness_metrics: Dict[str, Any] = Field(default_factory=dict, description="公平性指标")
    deployed_environment: str = Field(..., description="部署环境")
    model_owner: str = Field(..., description="模型负责人")
    approval_status: str = Field(..., description="审批状态")
    # 保留原有字段以保持兼容性
    id: Optional[str] = Field(None, description="模型ID（兼容字段）")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    model_path: Optional[str] = Field(None, description="模型路径")
    training_dataset: Optional[str] = Field(None, description="训练数据集（兼容字段）")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="准确率")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="精确率")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="召回率")
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="F1分数")
    deployment_endpoint: Optional[str] = Field(None, description="部署端点")
    tags: List[str] = Field(default_factory=list, description="标签")
    use_cases: List[str] = Field(default_factory=list, description="使用场景")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def __init__(self, **data):
        """初始化时处理兼容性字段"""
        # 如果提供了 model_id 但没有 id，则设置 id
        if 'model_id' in data and 'id' not in data:
            data['id'] = data['model_id']
        # 如果提供了 id 但没有 model_id，则设置 model_id
        if 'id' in data and 'model_id' not in data:
            data['model_id'] = data['id']
        # 如果提供了 training_dataset 但没有 training_data，则设置 training_data
        if 'training_dataset' in data and 'training_data' not in data:
            data['training_data'] = data['training_dataset']
        super().__init__(**data)


class BusinessEntityMetadata(BaseModel):
    """业务实体元数据模型"""
    id: Optional[str] = Field(None, description="实体ID")
    name: str = Field(..., min_length=1, max_length=255, description="实体名称")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    entity_type: EntityType = Field(..., description="实体类型")
    parent_id: Optional[str] = Field(None, description="父实体ID")
    business_definition: Optional[str] = Field(None, description="业务定义")
    business_rules: Optional[Dict[str, Any]] = Field(None, description="业务规则")
    data_dictionary: Optional[Dict[str, Any]] = Field(None, description="数据字典")
    related_entities: List[str] = Field(default_factory=list, description="关联实体ID列表")
    related_data_assets: List[str] = Field(default_factory=list, description="关联数据资产ID列表")
    data_steward: Optional[str] = Field(None, description="数据管家")
    business_owner: Optional[str] = Field(None, description="业务负责人")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WorkflowMetadata(BaseModel):
    """工作流元数据模型"""
    id: Optional[str] = Field(None, description="工作流ID")
    workflow_id: str = Field(..., description="工作流引擎中的ID")
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    workflow_type: Optional[WorkflowType] = Field(None, description="工作流类型")
    version: Optional[str] = Field(None, description="版本")
    category: Optional[str] = Field(None, description="分类")
    definition: Optional[Dict[str, Any]] = Field(None, description="工作流定义")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="输入Schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="输出Schema")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="依赖关系")
    data_sources: List[str] = Field(default_factory=list, description="数据源列表")
    data_sinks: List[str] = Field(default_factory=list, description="数据输出列表")
    tags: List[str] = Field(default_factory=list, description="标签")
    use_cases: List[str] = Field(default_factory=list, description="使用场景")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DataLineageRelation(BaseModel):
    """数据血缘关系模型"""
    id: Optional[str] = Field(None, description="关系ID")
    source_asset: str = Field(..., description="源资产（格式：type:id）")
    target_asset: str = Field(..., description="目标资产（格式：type:id）")
    source_type: Optional[str] = Field(None, description="源类型（从source_asset解析）")
    source_id: Optional[str] = Field(None, description="源ID（从source_asset解析）")
    target_type: Optional[str] = Field(None, description="目标类型（从target_asset解析）")
    target_id: Optional[str] = Field(None, description="目标ID（从target_asset解析）")
    relation_type: LineageRelationType = Field(..., description="关系类型")
    transformation: Optional[str] = Field(None, description="转换过程名称")
    transformation_logic: Optional[str] = Field(None, description="转换逻辑")
    transformation_code: Optional[str] = Field(None, description="转换代码")
    business_rules: Optional[List[str]] = Field(None, description="业务规则列表")
    data_quality_impact: Optional[Dict[str, Any]] = Field(None, description="数据质量影响")
    lineage_type: Optional[str] = Field(None, description="血缘类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展信息")
    first_seen: Optional[datetime] = Field(None, description="首次发现时间")
    last_seen: Optional[datetime] = Field(None, description="最后发现时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @model_validator(mode='after')
    def parse_assets(self):
        """从asset字段解析type和id"""
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
        
        return self


class DataQualityMetrics(BaseModel):
    """数据质量指标模型（核心指标）"""
    completeness: float = Field(..., ge=0.0, le=1.0, description="完整性")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="准确性")
    consistency: float = Field(..., ge=0.0, le=1.0, description="一致性")
    timeliness: float = Field(..., ge=0.0, le=1.0, description="及时性")
    validity: float = Field(..., ge=0.0, le=1.0, description="有效性")
    uniqueness: float = Field(..., ge=0.0, le=1.0, description="唯一性")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="总体评分")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 4) if v else 0.0
        }
    
    def calculate_overall_score(
        self,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        计算总体评分
        
        Args:
            weights: 各指标的权重，如果为None则使用等权重
        
        Returns:
            总体评分
        """
        if weights is None:
            # 默认等权重
            weights = {
                "completeness": 1.0,
                "accuracy": 1.0,
                "consistency": 1.0,
                "timeliness": 1.0,
                "validity": 1.0,
                "uniqueness": 1.0
            }
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        
        # 加权平均
        weighted_sum = (
            self.completeness * weights.get("completeness", 1.0) +
            self.accuracy * weights.get("accuracy", 1.0) +
            self.consistency * weights.get("consistency", 1.0) +
            self.timeliness * weights.get("timeliness", 1.0) +
            self.validity * weights.get("validity", 1.0) +
            self.uniqueness * weights.get("uniqueness", 1.0)
        )
        
        return weighted_sum / total_weight
    
    def update_overall_score(self, weights: Optional[Dict[str, float]] = None) -> "DataQualityMetrics":
        """
        更新总体评分
        
        Args:
            weights: 各指标的权重
        
        Returns:
            更新后的实例
        """
        self.overall_score = self.calculate_overall_score(weights)
        return self
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> "DataQualityMetrics":
        """
        从字典创建实例，自动计算总体评分
        
        Args:
            data: 包含质量指标的字典
            weights: 各指标的权重
        
        Returns:
            DataQualityMetrics实例
        """
        metrics = cls(**data)
        if "overall_score" not in data or data.get("overall_score") is None:
            metrics.overall_score = metrics.calculate_overall_score(weights)
        return metrics
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "consistency": self.consistency,
            "timeliness": self.timeliness,
            "validity": self.validity,
            "uniqueness": self.uniqueness,
            "overall_score": self.overall_score
        }
    
    def get_quality_level(self) -> QualityLevel:
        """获取质量等级"""
        return QualityScore.get_level(self.overall_score)


class QualityMetrics(BaseModel):
    """数据质量指标模型（扩展版）"""
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="质量分数")
    quality_level: Optional[QualityLevel] = Field(None, description="质量等级")
    completeness: Optional[float] = Field(None, ge=0.0, le=1.0, description="完整性")
    completeness_level: Optional[CompletenessLevel] = Field(None, description="完整性等级")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="准确性")
    accuracy_level: Optional[AccuracyLevel] = Field(None, description="准确性等级")
    consistency: Optional[float] = Field(None, ge=0.0, le=1.0, description="一致性")
    timeliness: Optional[float] = Field(None, ge=0.0, le=1.0, description="及时性")
    validity: Optional[float] = Field(None, ge=0.0, le=1.0, description="有效性")
    uniqueness: Optional[float] = Field(None, ge=0.0, le=1.0, description="唯一性")
    metrics: Optional[Dict[str, Any]] = Field(None, description="其他指标")
    last_checked: Optional[datetime] = Field(None, description="最后检查时间")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def calculate_quality_level(self) -> Optional[QualityLevel]:
        """计算质量等级"""
        if self.quality_score is not None:
            return QualityScore.get_level(self.quality_score)
        return None
    
    def to_data_quality_metrics(self, weights: Optional[Dict[str, float]] = None) -> DataQualityMetrics:
        """
        转换为DataQualityMetrics
        
        Args:
            weights: 各指标的权重
        
        Returns:
            DataQualityMetrics实例
        """
        return DataQualityMetrics(
            completeness=self.completeness or 0.0,
            accuracy=self.accuracy or 0.0,
            consistency=self.consistency or 0.0,
            timeliness=self.timeliness or 0.0,
            validity=self.validity or 0.0,
            uniqueness=self.uniqueness or 0.0,
            overall_score=self.quality_score or 0.0
        )


class MetadataSearchResult(BaseModel):
    """元数据搜索结果模型"""
    entity_type: str = Field(..., description="实体类型")
    entity_id: str = Field(..., description="实体ID")
    name: str = Field(..., description="名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    score: Optional[float] = Field(None, description="匹配分数")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="高亮片段")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class MetadataFilter(BaseModel):
    """元数据过滤模型"""
    entity_types: Optional[List[str]] = Field(None, description="实体类型列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    search: Optional[str] = Field(None, description="搜索关键词")
    owner: Optional[str] = Field(None, description="负责人")
    classification: Optional[str] = Field(None, description="分类")
    created_after: Optional[datetime] = Field(None, description="创建时间（之后）")
    created_before: Optional[datetime] = Field(None, description="创建时间（之前）")
    updated_after: Optional[datetime] = Field(None, description="更新时间（之后）")
    updated_before: Optional[datetime] = Field(None, description="更新时间（之前）")
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="自定义过滤条件")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TechnicalMetadata(BaseModel):
    """技术元数据 - 描述数据的技术特性"""
    data_source: str = Field(..., description="数据源")
    data_format: str = Field(..., description="数据格式")
    schema_definition: Dict[str, Any] = Field(..., description="Schema定义")
    storage_location: str = Field(..., description="存储位置")
    data_size: int = Field(..., ge=0, description="数据大小（字节）")
    update_frequency: str = Field(..., description="更新频率")
    retention_policy: str = Field(..., description="保留策略")
    access_permissions: List[str] = Field(default_factory=list, description="访问权限")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class BusinessMetadata(BaseModel):
    """业务元数据 - 描述数据的业务含义"""
    business_owner: str = Field(..., description="业务负责人")
    business_domain: str = Field(..., description="业务领域")
    business_glossary: Dict[str, Any] = Field(default_factory=dict, description="业务术语表")
    sensitivity_level: str = Field(..., description="敏感级别")
    compliance_requirements: List[str] = Field(default_factory=list, description="合规要求")
    business_rules: List[str] = Field(default_factory=list, description="业务规则")
    kpi_definition: Optional[str] = Field(None, description="KPI定义")
    data_quality_requirements: Dict[str, Any] = Field(default_factory=dict, description="数据质量要求")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OperationalMetadata(BaseModel):
    """操作元数据 - 描述数据的操作特性"""
    usage_statistics: Dict[str, Any] = Field(default_factory=dict, description="使用统计")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")
    error_rates: Optional[float] = Field(None, ge=0.0, le=1.0, description="错误率")
    last_access_time: Optional[datetime] = Field(None, description="最后访问时间")
    access_patterns: List[str] = Field(default_factory=list, description="访问模式")
    cost_metrics: Dict[str, Any] = Field(default_factory=dict, description="成本指标")
    service_level_agreement: Dict[str, Any] = Field(default_factory=dict, description="SLA协议")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MetadataResponse(BaseModel):
    """元数据响应模型"""
    success: bool = Field(True, description="是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    total: Optional[int] = Field(None, description="总记录数")
    page: Optional[int] = Field(None, description="页码")
    page_size: Optional[int] = Field(None, description="每页大小")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


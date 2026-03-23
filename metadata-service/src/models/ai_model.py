"""
AI模型元数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON, DateTime, Integer, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
import enum

from database.src.models.base import Base, TimestampMixin


class ModelType(str, enum.Enum):
    """模型类型"""
    LLM = "llm"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    CUSTOM = "custom"


class ModelStatus(str, enum.Enum):
    """模型状态"""
    TRAINING = "training"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AIModel(Base, TimestampMixin):
    """AI模型元数据表"""
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    # 使用native_enum=False和values_callable确保使用枚举值而不是名称
    model_type = Column(SQLEnum(ModelType, native_enum=False, values_callable=lambda x: [e.value for e in ModelType]), nullable=False, index=True)
    status = Column(SQLEnum(ModelStatus, native_enum=False, values_callable=lambda x: [e.value for e in ModelStatus]), default=ModelStatus.ACTIVE, index=True)
    
    # 模型信息
    model_version = Column(String(50))
    framework = Column(String(100))  # 框架（如：PyTorch, TensorFlow, HuggingFace）
    model_path = Column(String(500))  # 模型存储路径
    model_size = Column(Integer)  # 模型大小（字节）
    
    # 训练信息
    training_dataset = Column(String(255))
    training_config = Column(JSON)  # 训练配置
    hyperparameters = Column(JSON)  # 超参数
    training_metrics = Column(JSON)  # 训练指标
    
    # 性能指标
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    performance_metrics = Column(JSON)  # 其他性能指标
    
    # 部署信息
    deployment_endpoint = Column(String(500))
    deployment_config = Column(JSON)
    inference_latency = Column(Float)  # 推理延迟（毫秒）
    
    # 业务信息
    business_owner = Column(String(100))
    technical_owner = Column(String(100))
    tags = Column(JSON)  # 标签列表（旧字段，保留向后兼容）
    use_cases = Column(JSON)  # 使用场景
    
    # 分类维度（新字段，支持三层分类体系）
    classification_dimensions = Column(JSON, nullable=True, comment='分类维度（业务、技术、生命周期、治理）')
    standardized_tags = Column(JSON, nullable=True, comment='标准化标签列表')
    
    # 兼容属性：从新字段或旧字段获取主分类
    @property
    def primary_classification(self) -> Optional[str]:
        """从新字段或旧字段获取主分类"""
        if self.classification_dimensions and isinstance(self.classification_dimensions, dict):
            return self.classification_dimensions.get('primary')
        # 如果没有新字段，使用model_type作为主分类
        return self.model_type.value if self.model_type else None
    
    # 元数据
    extra_metadata = Column("metadata", JSON)  # 使用 metadata 作为数据库列名


class AIModelSchema(BaseModel):
    """AI模型Schema（API响应）"""
    id: int
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    model_type: ModelType
    status: ModelStatus
    model_version: Optional[str] = None
    framework: Optional[str] = None
    model_path: Optional[str] = None
    model_size: Optional[int] = None
    training_dataset: Optional[str] = None
    training_config: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    deployment_endpoint: Optional[str] = None
    deployment_config: Optional[Dict[str, Any]] = None
    inference_latency: Optional[float] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None  # 旧字段，保留向后兼容
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AIModelCreate(BaseModel):
    """创建AI模型请求"""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    model_type: ModelType
    status: ModelStatus = ModelStatus.ACTIVE
    model_version: Optional[str] = None
    framework: Optional[str] = None
    model_path: Optional[str] = None
    model_size: Optional[int] = None
    training_dataset: Optional[str] = None
    training_config: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    deployment_endpoint: Optional[str] = None
    deployment_config: Optional[Dict[str, Any]] = None
    inference_latency: Optional[float] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


class AIModelUpdate(BaseModel):
    """更新AI模型请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ModelStatus] = None
    classification_dimensions: Optional[Dict[str, Any]] = None  # 分类维度（新字段）
    standardized_tags: Optional[List[str]] = None  # 标准化标签（新字段）
    model_version: Optional[str] = None
    framework: Optional[str] = None
    model_path: Optional[str] = None
    model_size: Optional[int] = None
    training_dataset: Optional[str] = None
    training_config: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    deployment_endpoint: Optional[str] = None
    deployment_config: Optional[Dict[str, Any]] = None
    inference_latency: Optional[float] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    tags: Optional[List[str]] = None
    use_cases: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata", serialization_alias="metadata")


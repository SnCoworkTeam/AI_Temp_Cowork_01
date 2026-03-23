"""
数据类型枚举
定义元数据中使用的各种数据类型枚举
"""
from enum import Enum


class DataAssetType(str, Enum):
    """数据资产类型"""
    DATASET = "dataset"
    TABLE = "table"
    VIEW = "view"
    FILE = "file"
    STREAM = "stream"
    API = "api"
    DATABASE = "database"
    SCHEMA = "schema"
    COLUMN = "column"


class ModelType(str, Enum):
    """AI模型类型"""
    LLM = "llm"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"
    CUSTOM = "custom"


class EntityType(str, Enum):
    """业务实体类型"""
    DOMAIN = "domain"
    CONCEPT = "concept"
    TERM = "term"
    GLOSSARY = "glossary"
    POLICY = "policy"
    RULE = "rule"
    STANDARD = "standard"
    METRIC = "metric"


class WorkflowType(str, Enum):
    """工作流类型"""
    DATA_PIPELINE = "data_pipeline"
    ML_PIPELINE = "ml_pipeline"
    ETL = "etl"
    BATCH = "batch"
    STREAMING = "streaming"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CUSTOM = "custom"


class LineageRelationType(str, Enum):
    """数据血缘关系类型"""
    READS = "reads"
    WRITES = "writes"
    TRANSFORMS = "transforms"
    DEPENDS_ON = "depends_on"
    DERIVES = "derives"
    CONTAINS = "contains"
    PART_OF = "part_of"
    VERSION_OF = "version_of"


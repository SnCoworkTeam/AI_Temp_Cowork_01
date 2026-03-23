"""
知识库相关数据模型
文档、向量块、知识图谱
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Float, Index, func, TypeDecorator
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
from enum import Enum

from .base import BaseModel, TimestampMixin


class EnumValueType(TypeDecorator):
    """确保SQLAlchemy使用枚举的value而不是name"""
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        """将枚举对象转换为数据库值（使用value）"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            # 关键：使用枚举的value（小写字符串）而不是name（大写）
            result = value.value
            return result
        # 如果已经是字符串，直接返回（但应该是小写的）
        if isinstance(value, str):
            return value.lower()
        return value
    
    def process_result_value(self, value, dialect):
        """从数据库值恢复枚举对象"""
        if value is None:
            return None
        # 从value（小写字符串）恢复枚举对象
        try:
            return self.enum_class(value)
        except ValueError:
            # 如果值不匹配，尝试通过name匹配（向后兼容）
            try:
                return self.enum_class[value.upper()]
            except KeyError:
                return self.enum_class.UNKNOWN if hasattr(self.enum_class, 'UNKNOWN') else None


class DocumentType(str, Enum):
    """文档类型"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    TEXT = "text"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """文档状态"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class KnowledgeBaseStatus(str, Enum):
    """知识库状态"""
    ACTIVE = "active"
    INDEXING = "indexing"
    PAUSED = "paused"
    ARCHIVED = "archived"
    FAILED = "failed"


class KnowledgeBase(BaseModel):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="知识库ID")
    name = Column(String(200), nullable=False, index=True, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    status = Column(SQLEnum(KnowledgeBaseStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=KnowledgeBaseStatus.ACTIVE, nullable=False, comment="知识库状态")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="创建者ID")
    
    # 配置信息
    embedding_model = Column(String(100), default="default", nullable=False, comment="嵌入模型")
    chunk_strategy = Column(String(50), default="fixed", nullable=False, comment="分块策略: fixed, semantic, sliding")
    chunk_size = Column(Integer, default=1000, nullable=False, comment="分块大小（字符数）")
    chunk_overlap = Column(Integer, default=200, nullable=False, comment="分块重叠（字符数）")
    
    # 设置信息（JSON格式存储额外配置）
    settings = Column(JSONB, nullable=True, default=dict, comment="知识库设置")
    
    # 关系
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_kb_name', 'name'),
        Index('idx_kb_status', 'status'),
        Index('idx_kb_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(BaseModel):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="文档ID")
    filename = Column(String(500), nullable=False, index=True, comment="文件名")
    file_type = Column(SQLEnum(DocumentType, native_enum=False, values_callable=lambda x: [e.value for e in x]), nullable=False, comment="文件类型")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_path = Column(String(1000), nullable=False, comment="文件存储路径")
    status = Column(SQLEnum(DocumentStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=DocumentStatus.UPLOADING, nullable=False, comment="文档状态")
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="上传者ID")
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=True, index=True, comment="所属知识库ID")
    version = Column(Integer, default=1, nullable=False, comment="文档版本")
    tags = Column(ARRAY(String), nullable=True, default=list, comment="标签列表")
    category = Column(String(100), nullable=True, index=True, comment="文档分类（保留用于向后兼容）")
    quality_score = Column(Float, nullable=True, comment="质量评分")
    summary = Column(Text, nullable=True, comment="文档摘要")
    
    # 元数据（统一命名：document_metadata，映射到数据库的 metadata 列）
    # 注意：不能使用 metadata 作为属性名，因为它是 SQLAlchemy 的保留属性
    document_metadata = Column('metadata', JSONB, nullable=True, default=dict, comment="文档元数据")
    
    # 时间戳（继承自TimestampMixin）
    processed_at = Column(DateTime, nullable=True, comment="处理完成时间")
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_documents_status', 'status'),
        Index('idx_documents_category', 'category'),
        Index('idx_documents_kb_id', 'knowledge_base_id'),
        Index('idx_documents_tags', 'tags', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(BaseModel):
    """文档块模型"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="块ID")
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True, comment="文档ID")
    chunk_index = Column(Integer, nullable=False, comment="块索引")
    content = Column(Text, nullable=False, comment="块内容")
    start_char = Column(Integer, nullable=True, comment="起始字符位置")
    end_char = Column(Integer, nullable=True, comment="结束字符位置")
    page_number = Column(Integer, nullable=True, comment="页码")
    
    # 向量信息
    embedding = Column(JSONB, nullable=True, comment="嵌入向量")
    embedding_model = Column(String(100), nullable=True, comment="嵌入模型")
    
    # 元数据
    chunk_metadata = Column(JSONB, nullable=True, default=dict, comment="块元数据")
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunks_document_index', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class KnowledgeGraphNode(BaseModel):
    """知识图谱节点模型"""
    __tablename__ = "knowledge_graph_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="节点ID")
    label = Column(String(200), nullable=False, index=True, comment="节点标签")
    node_type = Column(String(100), nullable=True, index=True, comment="节点类型")
    properties = Column(JSONB, nullable=True, default=dict, comment="节点属性")
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, comment="关联文档ID")
    
    # 关系
    source_edges = relationship("KnowledgeGraphEdge", foreign_keys="KnowledgeGraphEdge.source_node_id", back_populates="source_node")
    target_edges = relationship("KnowledgeGraphEdge", foreign_keys="KnowledgeGraphEdge.target_node_id", back_populates="target_node")
    
    __table_args__ = (
        Index('idx_kg_nodes_label', 'label'),
        Index('idx_kg_nodes_type', 'node_type'),
    )
    
    def __repr__(self):
        return f"<KnowledgeGraphNode(id={self.id}, label={self.label})>"


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边模型"""
    __tablename__ = "knowledge_graph_edges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="边ID")
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False, index=True, comment="源节点ID")
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id"), nullable=False, index=True, comment="目标节点ID")
    relationship_type = Column(String(100), nullable=False, comment="关系类型")
    weight = Column(Float, nullable=True, comment="关系权重")
    # 注意：不能使用metadata作为属性名，因为它是SQLAlchemy的保留属性
    # 使用edge_metadata映射到数据库的metadata列
    edge_metadata = Column('metadata', JSONB, nullable=True, default=dict, comment="边元数据")
    
    # 关系
    source_node = relationship("KnowledgeGraphNode", foreign_keys=[source_node_id], back_populates="source_edges")
    target_node = relationship("KnowledgeGraphNode", foreign_keys=[target_node_id], back_populates="target_edges")
    
    __table_args__ = (
        Index('idx_kg_edges_source', 'source_node_id'),
        Index('idx_kg_edges_target', 'target_node_id'),
    )
    
    def __repr__(self):
        return f"<KnowledgeGraphEdge(id={self.id}, source={self.source_node_id}, target={self.target_node_id})>"


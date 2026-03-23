"""
文档数据模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    TEXT = "text"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class ChunkMetadata(BaseModel):
    """文档块元数据"""
    chunk_id: str = Field(..., description="块ID")
    chunk_index: int = Field(..., description="块索引")
    start_char: int = Field(..., description="起始字符位置")
    end_char: int = Field(..., description="结束字符位置")
    page_number: Optional[int] = Field(None, description="页码（如果适用）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class DocumentChunk(BaseModel):
    """文档块"""
    chunk_id: str = Field(..., description="块ID")
    content: str = Field(..., description="块内容")
    metadata: ChunkMetadata = Field(..., description="块元数据")
    embedding: Optional[List[float]] = Field(None, description="嵌入向量")


class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: Optional[str] = Field(None, description="文档标题")
    author: Optional[str] = Field(None, description="作者")
    creation_date: Optional[datetime] = Field(None, description="创建日期")
    modification_date: Optional[datetime] = Field(None, description="修改日期")
    page_count: Optional[int] = Field(None, description="页数")
    word_count: Optional[int] = Field(None, description="字数")
    language: Optional[str] = Field(None, description="语言")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="自定义元数据")


class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    file_type: DocumentType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    file_path: str = Field(..., description="文件存储路径")
    status: DocumentStatus = Field(..., description="文档状态")
    metadata: DocumentMetadata = Field(..., description="文档元数据")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="文档块列表")
    total_chunks: int = Field(default=0, description="总块数")
    uploaded_at: datetime = Field(..., description="上传时间")
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")
    version: int = Field(default=1, description="文档版本")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    filename: str = Field(..., description="文件名")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="自定义元数据")
    process_async: bool = Field(default=True, description="是否异步处理")


class DocumentCreateRequest(BaseModel):
    """文档创建请求（支持JSON数据）"""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    category: Optional[str] = Field(None, description="文档分类")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    process_async: bool = Field(default=False, description="是否异步处理（默认同步处理）")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    status: DocumentStatus = Field(..., description="文档状态")
    message: str = Field(..., description="响应消息")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[Document] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class DocumentFilterParams(BaseModel):
    """文档过滤参数"""
    file_type: Optional[DocumentType] = Field(None, description="文件类型过滤")
    status: Optional[DocumentStatus] = Field(None, description="状态过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    search: Optional[str] = Field(None, description="搜索关键词")
    created_by: Optional[str] = Field(None, description="创建者过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    knowledge_base_id: Optional[str] = Field(None, description="限定知识库ID")
    document_ids: Optional[List[str]] = Field(None, description="限定文档ID列表")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="最小相似度分数")
    filters: Optional[Dict[str, Any]] = Field(None, description="额外过滤条件")


class KeywordSearchRequest(BaseModel):
    """关键词搜索请求"""
    keywords: List[str] = Field(..., min_items=1, description="关键词列表")
    knowledge_base_id: Optional[str] = Field(None, description="限定知识库ID")
    document_ids: Optional[List[str]] = Field(None, description="限定文档ID列表")
    match_all: bool = Field(default=False, description="是否匹配所有关键词")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: str = Field(..., description="块ID")
    document_id: str = Field(..., description="文档ID")
    document_name: str = Field(..., description="文档名称")
    content: str = Field(..., description="内容片段")
    score: float = Field(..., description="相似度分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    chunk_metadata: ChunkMetadata = Field(..., description="块元数据")


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[SearchResult] = Field(..., description="搜索结果")
    total: int = Field(..., description="总结果数")
    query: str = Field(..., description="查询内容")
    search_type: Optional[str] = Field(None, description="搜索类型")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    search_id: Optional[str] = Field(None, description="搜索历史ID")


class KnowledgeGraphNode(BaseModel):
    """知识图谱节点"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    type: str = Field(..., description="节点类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: str = Field(..., description="边标签")
    properties: Dict[str, Any] = Field(default_factory=dict, description="边属性")


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应"""
    nodes: List[KnowledgeGraphNode] = Field(..., description="节点列表")
    edges: List[KnowledgeGraphEdge] = Field(..., description="边列表")
    total_nodes: int = Field(..., description="总节点数")
    total_edges: int = Field(..., description="总边数")










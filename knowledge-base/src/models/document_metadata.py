"""
增强的文档元数据模型
用于与元数据服务集成的文档元数据定义
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    """增强的文档元数据模型"""
    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., min_length=1, description="文档标题")
    document_type: str = Field(..., description="文档类型")
    source: str = Field(..., description="文档来源")
    author: str = Field(..., description="作者")
    created_date: datetime = Field(..., description="创建日期")
    modified_date: datetime = Field(..., description="修改日期")
    language: str = Field(..., description="语言")
    topics: List[str] = Field(default_factory=list, description="主题列表")
    entities: List[str] = Field(default_factory=list, description="实体列表")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="质量分数")
    access_level: str = Field(..., description="访问级别")
    vector_embedding_status: str = Field(..., description="向量嵌入状态")
    search_popularity: int = Field(default=0, ge=0, description="搜索热度")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    file_path: Optional[str] = Field(None, description="文件路径")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DocumentMetadataCreate(BaseModel):
    """创建文档元数据请求"""
    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., min_length=1, description="文档标题")
    document_type: str = Field(..., description="文档类型")
    source: str = Field(..., description="文档来源")
    author: str = Field(..., description="作者")
    created_date: datetime = Field(..., description="创建日期")
    modified_date: datetime = Field(..., description="修改日期")
    language: str = Field(..., description="语言")
    topics: Optional[List[str]] = Field(None, description="主题列表")
    entities: Optional[List[str]] = Field(None, description="实体列表")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="质量分数")
    access_level: Optional[str] = Field(None, description="访问级别")
    vector_embedding_status: Optional[str] = Field(None, description="向量嵌入状态")
    search_popularity: Optional[int] = Field(None, ge=0, description="搜索热度")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    file_path: Optional[str] = Field(None, description="文件路径")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


class DocumentMetadataUpdate(BaseModel):
    """更新文档元数据请求"""
    title: Optional[str] = Field(None, min_length=1, description="文档标题")
    document_type: Optional[str] = Field(None, description="文档类型")
    source: Optional[str] = Field(None, description="文档来源")
    author: Optional[str] = Field(None, description="作者")
    created_date: Optional[datetime] = Field(None, description="创建日期")
    modified_date: Optional[datetime] = Field(None, description="修改日期")
    language: Optional[str] = Field(None, description="语言")
    topics: Optional[List[str]] = Field(None, description="主题列表")
    entities: Optional[List[str]] = Field(None, description="实体列表")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="质量分数")
    access_level: Optional[str] = Field(None, description="访问级别")
    vector_embedding_status: Optional[str] = Field(None, description="向量嵌入状态")
    search_popularity: Optional[int] = Field(None, ge=0, description="搜索热度")
    filename: Optional[str] = Field(None, description="文件名")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    file_path: Optional[str] = Field(None, description="文件路径")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


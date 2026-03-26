"""
知识库管理API路由
提供知识库的创建、查询、更新、删除功能
知识库作为独立实体管理
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..services.knowledge_base_service import KnowledgeBaseService
from ..services.document_service import DocumentService
from ..dependencies.database import get_db
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response
from sqlalchemy.orm import Session

router = APIRouter()
logger = setup_logger(__name__)


class KnowledgeBaseCreateRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    embedding_model: Optional[str] = Field("default", description="嵌入模型")
    chunk_strategy: Optional[str] = Field("fixed", description="分块策略: fixed, semantic, sliding")
    chunk_size: Optional[int] = Field(1000, description="分块大小（字符数）")
    chunk_overlap: Optional[int] = Field(200, description="分块重叠（字符数）")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="知识库设置")


class KnowledgeBaseUpdateRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    status: Optional[str] = Field(None, description="知识库状态: active, indexing, paused, archived, failed")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    chunk_strategy: Optional[str] = Field(None, description="分块策略")
    chunk_size: Optional[int] = Field(None, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, description="分块重叠")
    settings: Optional[Dict[str, Any]] = Field(None, description="知识库设置（会与现有设置合并）")


class KnowledgeBase(BaseModel):
    """知识库模型"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: str = Field(default="", description="知识库描述")
    status: str = Field(..., description="知识库状态")
    document_count: int = Field(default=0, description="文档数量")
    total_chunks: int = Field(default=0, description="总块数")
    embedding_model: str = Field(default="default", description="嵌入模型")
    chunk_strategy: str = Field(default="fixed", description="分块策略")
    chunk_size: int = Field(default=1000, description="分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠")
    settings: Dict[str, Any] = Field(default_factory=dict, description="知识库设置")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    knowledge_bases: List[KnowledgeBase] = Field(..., description="知识库列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


def get_knowledge_base_service(db: Session = Depends(get_db)) -> KnowledgeBaseService:
    """获取知识库服务"""
    return KnowledgeBaseService(db)


@router.get(
    "/knowledge-bases",
    response_model=KnowledgeBaseListResponse,
    summary="获取知识库列表",
    description="获取所有知识库列表，支持分页、搜索和过滤",
    tags=["Knowledge Bases"]
)
async def list_knowledge_bases(
    status: Optional[str] = Query(None, description="状态过滤"),
    created_by: Optional[str] = Query(None, description="创建者ID过滤"),
    search: Optional[str] = Query(None, description="搜索关键词（名称或描述）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
) -> KnowledgeBaseListResponse:
    """获取知识库列表"""
    try:
        service = get_knowledge_base_service(db)
        result = await service.list_knowledge_bases(
            status=status,
            created_by=created_by,
            search=search,
            page=page,
            page_size=page_size
        )
        
        knowledge_bases = [KnowledgeBase(**kb) for kb in result["knowledge_bases"]]
        
        return KnowledgeBaseListResponse(
            knowledge_bases=knowledge_bases,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing knowledge bases: {str(e)}")


@router.post(
    "/knowledge-bases",
    response_model=KnowledgeBase,
    summary="创建知识库",
    description="创建新知识库",
    tags=["Knowledge Bases"]
)
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db),
    created_by: Optional[str] = None  # 可以从认证中间件获取
) -> KnowledgeBase:
    """创建知识库"""
    try:
        service = get_knowledge_base_service(db)
        result = await service.create_knowledge_base(
            name=request.name,
            description=request.description,
            created_by=created_by,
            embedding_model=request.embedding_model or "default",
            chunk_strategy=request.chunk_strategy or "fixed",
            chunk_size=request.chunk_size or 1000,
            chunk_overlap=request.chunk_overlap or 200,
            settings=request.settings or {}
        )
        
        return KnowledgeBase(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating knowledge base: {str(e)}")


@router.get(
    "/knowledge-bases/{kb_id}",
    response_model=KnowledgeBase,
    summary="获取知识库详情",
    description="根据ID获取知识库详情",
    tags=["Knowledge Bases"]
)
async def get_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db)
) -> KnowledgeBase:
    """获取知识库详情"""
    try:
        service = get_knowledge_base_service(db)
        result = await service.get_knowledge_base(kb_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        return KnowledgeBase(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting knowledge base: {str(e)}")


@router.put(
    "/knowledge-bases/{kb_id}",
    response_model=KnowledgeBase,
    summary="更新知识库",
    description="完整更新知识库信息",
    tags=["Knowledge Bases"]
)
async def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db)
) -> KnowledgeBase:
    """更新知识库（PUT - 完整更新）"""
    try:
        service = get_knowledge_base_service(db)
        
        # 构建更新数据
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status
        if request.embedding_model is not None:
            updates["embedding_model"] = request.embedding_model
        if request.chunk_strategy is not None:
            updates["chunk_strategy"] = request.chunk_strategy
        if request.chunk_size is not None:
            updates["chunk_size"] = request.chunk_size
        if request.chunk_overlap is not None:
            updates["chunk_overlap"] = request.chunk_overlap
        if request.settings is not None:
            updates["settings"] = request.settings
        
        result = await service.update_knowledge_base(kb_id, **updates)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        return KnowledgeBase(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating knowledge base: {str(e)}")


@router.patch(
    "/knowledge-bases/{kb_id}",
    response_model=KnowledgeBase,
    summary="部分更新知识库",
    description="部分更新知识库信息（只更新提供的字段）",
    tags=["Knowledge Bases"]
)
async def patch_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db)
) -> KnowledgeBase:
    """部分更新知识库（PATCH - 只更新提供的字段）"""
    try:
        service = get_knowledge_base_service(db)
        
        # 只更新提供的字段
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status
        if request.embedding_model is not None:
            updates["embedding_model"] = request.embedding_model
        if request.chunk_strategy is not None:
            updates["chunk_strategy"] = request.chunk_strategy
        if request.chunk_size is not None:
            updates["chunk_size"] = request.chunk_size
        if request.chunk_overlap is not None:
            updates["chunk_overlap"] = request.chunk_overlap
        if request.settings is not None:
            updates["settings"] = request.settings
        
        if not updates:
            # 如果没有提供任何更新字段，返回当前知识库
            result = await service.get_knowledge_base(kb_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
            return KnowledgeBase(**result)
        
        result = await service.update_knowledge_base(kb_id, **updates)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        return KnowledgeBase(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error patching knowledge base: {str(e)}")


@router.delete(
    "/knowledge-bases/{kb_id}",
    summary="删除知识库",
    description="删除知识库及其所有文档",
    tags=["Knowledge Bases"]
)
async def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """删除知识库"""
    try:
        service = get_knowledge_base_service(db)
        success = await service.delete_knowledge_base(kb_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        return {
            "message": f"Knowledge base '{kb_id}' deleted successfully",
            "id": kb_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting knowledge base: {str(e)}")


@router.get(
    "/knowledge-bases/{kb_id}/stats",
    summary="获取知识库统计信息",
    description="获取知识库的统计信息",
    tags=["Knowledge Bases"]
)
async def get_knowledge_base_stats(
    kb_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取知识库统计信息"""
    try:
        service = get_knowledge_base_service(db)
        result = await service.get_knowledge_base_stats(kb_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting knowledge base stats: {str(e)}")


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    summary="获取知识库下的文档列表",
    description="获取指定知识库下的所有文档",
    tags=["Knowledge Bases"]
)
async def get_knowledge_base_documents(
    kb_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取知识库下的文档列表"""
    try:
        # 验证知识库存在
        kb_service = get_knowledge_base_service(db)
        kb = await kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
        
        # 获取文档列表
        doc_service = DocumentService(db)
        result = await doc_service.list_documents(
            page=page,
            page_size=page_size,
            knowledge_base_id=kb_id,
            status=None,
            category=None,
            tags=None,
            search=None,
            uploaded_by=None
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting knowledge base documents: {str(e)}")

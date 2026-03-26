"""
向量协调API路由
"""
from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..services.vector_coordinator_service import VectorCoordinatorService
import logging

router = APIRouter(prefix="/api/vectors", tags=["Vector Coordinator"])
logger = logging.getLogger(__name__)


class VectorRegisterRequest(BaseModel):
    """向量注册请求"""
    entity_uri: str = Field(..., description="实体URI")
    modality: str = Field(..., description="模态（metadata, knowledge, permission等）")
    vector: List[float] = Field(..., description="向量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class VectorFuseRequest(BaseModel):
    """向量融合请求"""
    vectors: Dict[str, List[float]] = Field(..., description="向量字典，key为模态名称")
    weights: Optional[Dict[str, float]] = Field(None, description="权重字典（可选）")


class SimilaritySearchRequest(BaseModel):
    """相似度搜索请求"""
    query: str = Field(..., description="查询文本")
    modalities: Optional[List[str]] = Field(None, description="模态列表（可选）")
    limit: int = Field(10, ge=1, le=100, description="返回数量限制")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="相似度阈值（可选）")


@router.post("/register", summary="注册向量")
async def register_vector(
    request: VectorRegisterRequest,
    priority: Optional[str] = Body(None, description="优先级：realtime, normal, batch")
):
    """
    注册向量到统一向量空间（支持实时+批量策略）
    
    将来自不同服务的向量注册到统一向量空间，用于后续的融合和相似度计算
    
    **持久化策略**:
    - realtime: 立即写入（用于关键数据如元数据实体、知识图谱节点）
    - normal/batch: 批量写入（用于大量数据如文档向量）
    """
    try:
        service = VectorCoordinatorService()
        success = await service.register_vector(
            entity_uri=request.entity_uri,
            modality=request.modality,
            vector=request.vector,
            metadata=request.metadata,
            priority=priority or "auto"
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register vector")
        return {
            "success": True,
            "entity_uri": request.entity_uri,
            "modality": request.modality,
            "priority": priority
        }
    except Exception as e:
        logger.error(f"Failed to register vector: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fuse", summary="融合向量")
async def fuse_vectors(request: VectorFuseRequest):
    """
    融合多个模态的向量
    
    支持不同的融合策略（加权平均、拼接、注意力机制）
    """
    try:
        service = VectorCoordinatorService()
        fused_vector = service.fuse_vectors(
            vectors=request.vectors,
            weights=request.weights
        )
        return {
            "success": True,
            "fused_vector": fused_vector,
            "dimension": len(fused_vector)
        }
    except Exception as e:
        logger.error(f"Failed to fuse vectors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar", summary="查找相似向量")
async def find_similar_vectors(request: SimilaritySearchRequest):
    """
    查找相似向量（带缓存优化）
    
    基于查询文本，在统一向量空间中查找相似的实体
    """
    try:
        service = VectorCoordinatorService()
        results = await service.find_similar_vectors(
            query=request.query,
            modalities=request.modalities,
            limit=request.limit,
            threshold=request.threshold
        )
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Failed to find similar vectors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{entity_uri}", summary="获取向量信息")
async def get_vector_info(
    entity_uri: str,
    modality: str = Query(..., description="模态")
):
    """获取指定实体的向量信息"""
    try:
        service = VectorCoordinatorService()
        info = service.get_vector_info(entity_uri, modality)
        if not info:
            raise HTTPException(status_code=404, detail="Vector not found")
        return {
            "success": True,
            "info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vector info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="获取统计信息")
async def get_stats():
    """获取向量协调服务统计信息"""
    try:
        service = VectorCoordinatorService()
        stats = service.get_registry_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



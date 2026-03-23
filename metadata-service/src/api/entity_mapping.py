"""
实体映射API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..services.entity_mapping_service import EntityMappingService
from database.src.models.entity_mapping import (
    EntityMappingCreate,
    EntityMappingSchema
)
import logging

router = APIRouter(prefix="/api/entity-mapping", tags=["Entity Mapping"])
logger = logging.getLogger(__name__)


class AutoMapRequest(BaseModel):
    """自动映射请求"""
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="相似度阈值")


@router.post("/auto-map", summary="自动映射实体")
async def auto_map_entities(
    request: AutoMapRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    自动映射knowledge-base和metadata-service的实体
    
    基于名称相似度自动创建映射关系
    """
    try:
        service = EntityMappingService(db)
        mappings = await service.auto_map_entities(request.similarity_threshold)
        await service.close()
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to auto map entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings", summary="获取实体映射列表")
async def get_mappings(
    source_uri: Optional[str] = Query(None, description="源实体URI"),
    target_uri: Optional[str] = Query(None, description="目标实体URI"),
    status: Optional[str] = Query(None, description="状态：pending, confirmed, rejected"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取实体映射列表"""
    try:
        service = EntityMappingService(db)
        mappings = service.get_mappings(
            source_uri=source_uri,
            target_uri=target_uri,
            status=status,
            skip=skip,
            limit=limit
        )
        await service.close()
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Failed to get mappings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mappings", summary="创建实体映射")
async def create_mapping(
    mapping_data: EntityMappingCreate,
    db: Session = Depends(get_db)
):
    """创建实体映射"""
    try:
        service = EntityMappingService(db)
        mapping = service.create_mapping(mapping_data)
        await service.close()
        return {
            "success": True,
            "mapping": mapping
        }
    except Exception as e:
        logger.error(f"Failed to create mapping: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mappings/{mapping_id}/status", summary="更新映射状态")
async def update_mapping_status(
    mapping_id: int,
    status: str = Body(..., description="新状态：pending, confirmed, rejected"),
    db: Session = Depends(get_db)
):
    """更新映射状态"""
    try:
        service = EntityMappingService(db)
        mapping = service.update_mapping_status(mapping_id, status)
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        await service.close()
        return {
            "success": True,
            "mapping": mapping
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update mapping status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


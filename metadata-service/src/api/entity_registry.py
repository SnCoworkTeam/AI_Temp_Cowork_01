"""
实体注册API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.entity_registry_service import EntityRegistryService
from ..services.entity_id_service import EntityIDService
from database.src.models.entity_registry import EntityRegistryCreate, EntityRegistrySchema
from ..utils.entity_uri import EntityURI
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/entity-registry", tags=["Entity Registry"])
logger = setup_logger(__name__)


@router.post("/register", summary="注册实体")
async def register_entity(
    domain: str = Body(..., description="实体域（metadata, knowledge, sap, workflow）"),
    entity_type: str = Body(..., description="实体类型"),
    internal_id: str = Body(..., description="服务内部ID"),
    service_name: str = Body(..., description="服务名称"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="额外元数据"),
    db: Session = Depends(get_db)
):
    """注册实体，分配统一实体URI"""
    try:
        service = EntityRegistryService(db)
        registry = service.register_entity(
            domain=domain,
            entity_type=entity_type,
            internal_id=internal_id,
            service_name=service_name,
            metadata=metadata
        )
        return {
            "success": True,
            "entity": registry
        }
    except Exception as e:
        logger.error(f"Failed to register entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_uri:path}", summary="获取实体信息")
async def get_entity(
    entity_uri: str,
    db: Session = Depends(get_db)
):
    """根据统一实体URI获取实体信息"""
    try:
        service = EntityRegistryService(db)
        entity = service.get_entity_by_uri(entity_uri)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "entity": entity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities", summary="列出实体")
async def list_entities(
    domain: Optional[str] = Query(None, description="实体域过滤"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    service_name: Optional[str] = Query(None, description="服务名称过滤"),
    status: str = Query("active", description="状态过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """列出实体"""
    try:
        service = EntityRegistryService(db)
        entities = service.list_entities(
            domain=domain,
            entity_type=entity_type,
            service_name=service_name,
            status=status,
            skip=skip,
            limit=limit
        )
        return {
            "success": True,
            "entities": entities,
            "count": len(entities)
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entity/{entity_uri:path}/status", summary="更新实体状态")
async def update_entity_status(
    entity_uri: str,
    status: str = Body(..., description="新状态（active, deleted, merged）"),
    db: Session = Depends(get_db)
):
    """更新实体状态"""
    try:
        service = EntityRegistryService(db)
        entity = service.update_entity_status(entity_uri, status)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "entity": entity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update entity status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge", summary="合并实体")
async def merge_entities(
    source_uri: str = Body(..., description="源实体URI"),
    target_uri: str = Body(..., description="目标实体URI"),
    db: Session = Depends(get_db)
):
    """合并实体（将源实体合并到目标实体）"""
    try:
        service = EntityRegistryService(db)
        entity = service.merge_entities(source_uri, target_uri)
        
        if not entity:
            raise HTTPException(status_code=400, detail="Cannot merge entities")
        
        return {
            "success": True,
            "entity": entity
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="获取统计信息")
async def get_statistics(
    db: Session = Depends(get_db)
):
    """获取实体注册统计信息"""
    try:
        service = EntityRegistryService(db)
        stats = service.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-uri", summary="验证实体URI格式")
async def validate_uri(
    request: Dict[str, Any] = Body(..., description="请求体，包含uri字段"),
    db: Session = Depends(get_db)
):
    """验证实体URI格式"""
    try:
        uri = request.get("uri") if isinstance(request, dict) else request
        if not uri:
            raise HTTPException(status_code=400, detail="uri field is required")
        
        id_service = EntityIDService(db)
        is_valid = id_service.validate_entity_uri(uri)
        
        if is_valid:
            entity_uri = id_service.parse_entity_uri(uri)
            return {
                "success": True,
                "valid": True,
                "parsed": {
                    "domain": entity_uri.domain,
                    "entity_type": entity_uri.entity_type,
                    "entity_id": entity_uri.entity_id
                }
            }
        else:
            return {
                "success": True,
                "valid": False,
                "error": "Invalid URI format"
            }
    except Exception as e:
        logger.error(f"Failed to validate URI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


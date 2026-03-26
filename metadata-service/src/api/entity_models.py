"""
业务实体模型API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..services.business_entity_modeler import BusinessEntityModeler
from ..services.metadata_catalog import MetadataCatalogService
from ..services.data_lineage import DataLineageService
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/models", tags=["Entity Models"])
logger = setup_logger(__name__)


class EntityModelCreateRequest(BaseModel):
    """创建实体模型请求"""
    entity_ids: Optional[List[int]] = None


def get_entity_modeler(db: Session = Depends(get_db)) -> BusinessEntityModeler:
    """获取业务实体建模器"""
    catalog = MetadataCatalogService(db)
    lineage_service = DataLineageService(db)
    return BusinessEntityModeler(db, catalog, lineage_service)


@router.post("/entities", summary="创建业务实体模型")
async def create_entity_model(
    request: EntityModelCreateRequest = Body(...),
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """
    创建业务实体模型，构建关系图谱
    
    - 如果entity_ids为空，则从SAP自动识别实体
    - 如果提供entity_ids，则基于这些实体构建关系图谱
    """
    try:
        entity_ids = request.entity_ids
        
        if not entity_ids:
            # 自动识别实体
            entities = await modeler.identify_entities_from_sap()
            entity_ids = [e.id for e in entities]
        
        # 构建关系图谱
        graph = await modeler.build_entity_relationship_graph(entity_ids)
        
        return {
            "success": True,
            "graph": graph,
            "entity_count": len(entity_ids)
        }
    except Exception as e:
        logger.error(f"Failed to create entity model: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()


@router.get("/entities", summary="获取实体模型列表")
async def get_entity_models(
    skip: int = 0,
    limit: int = 100,
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """获取所有业务实体模型"""
    try:
        entities = modeler.catalog.list_business_entities(skip=skip, limit=limit)
        return {
            "success": True,
            "entities": [e.model_dump() for e in entities],
            "total": len(entities)
        }
    except Exception as e:
        logger.error(f"Failed to get entity models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()


@router.get("/entities/{entity_id}/similarity/{target_id}", summary="计算实体相似度")
async def calculate_similarity(
    entity_id: int,
    target_id: int,
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """计算两个实体的相似度"""
    try:
        similarity = await modeler.calculate_entity_similarity(entity_id, target_id)
        return {
            "success": True,
            "entity_id": entity_id,
            "target_id": target_id,
            "similarity": similarity
        }
    except Exception as e:
        logger.error(f"Failed to calculate similarity: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()


@router.get("/entities/{entity_id}/relationships", summary="获取实体关系图谱")
async def get_entity_relationships(
    entity_id: int,
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """获取指定实体的关系图谱"""
    try:
        graph = await modeler.build_entity_relationship_graph([entity_id])
        return {
            "success": True,
            "entity_id": entity_id,
            "graph": graph
        }
    except Exception as e:
        logger.error(f"Failed to get entity relationships: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()


@router.post("/entities/sap-relationships", summary="构建SAP实体关系")
async def build_sap_relationships(
    request: EntityModelCreateRequest = Body(...),
    modeler: BusinessEntityModeler = Depends(get_entity_modeler)
):
    """
    基于SAP NavigationProperty构建实体关系
    
    从SAP实体的navigation_properties中提取关系，并更新实体的related_entities字段
    """
    try:
        result = await modeler.build_sap_entity_relationships(request.entity_ids)
        return result
    except Exception as e:
        logger.error(f"Failed to build SAP relationships: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await modeler.close()


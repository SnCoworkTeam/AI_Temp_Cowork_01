"""
数据血缘API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.lineage import (
    DataLineageSchema,
    DataLineageCreate,
    LineageGraph,
    LineageRelationType,
    ImpactAnalysis,
    RootCauseAnalysis,
    DataLineageDetail
)
from ..services.data_lineage import DataLineageService
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_lineage_service(db: Session = Depends(get_db)) -> DataLineageService:
    """获取数据血缘服务"""
    return DataLineageService(db)


@router.post(
    "/lineage",
    response_model=DataLineageSchema,
    summary="创建血缘关系",
    tags=["Lineage"]
)
async def create_lineage(
    lineage_data: DataLineageCreate,
    service: DataLineageService = Depends(get_lineage_service)
):
    """创建数据血缘关系"""
    try:
        return service.create_lineage(lineage_data)
    except Exception as e:
        logger.error(f"Failed to create lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage",
    response_model=List[DataLineageSchema],
    summary="列出血缘关系",
    tags=["Lineage"]
)
async def list_lineage(
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    relation_type: Optional[LineageRelationType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: DataLineageService = Depends(get_lineage_service)
):
    """列出血缘关系"""
    try:
        return service.list_lineage(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relation_type=relation_type,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to list lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage/upstream/{entity_type}/{entity_id}",
    response_model=LineageGraph,
    summary="获取上游血缘",
    tags=["Lineage"]
)
async def get_upstream_lineage(
    entity_type: str,
    entity_id: str,
    max_depth: int = Query(10, ge=1, le=20),
    service: DataLineageService = Depends(get_lineage_service)
):
    """获取数据的上游血缘（数据来源）"""
    try:
        return service.get_upstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
    except Exception as e:
        logger.error(f"Failed to get upstream lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage/downstream/{entity_type}/{entity_id}",
    response_model=LineageGraph,
    summary="获取下游血缘",
    tags=["Lineage"]
)
async def get_downstream_lineage(
    entity_type: str,
    entity_id: str,
    max_depth: int = Query(10, ge=1, le=20),
    service: DataLineageService = Depends(get_lineage_service)
):
    """获取数据的下游血缘（数据去向）"""
    try:
        return service.get_downstream_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
    except Exception as e:
        logger.error(f"Failed to get downstream lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage/full/{entity_type}/{entity_id}",
    response_model=LineageGraph,
    summary="获取完整血缘",
    tags=["Lineage"]
)
async def get_full_lineage(
    entity_type: str,
    entity_id: str,
    max_depth: int = Query(10, ge=1, le=20),
    service: DataLineageService = Depends(get_lineage_service)
):
    """获取完整血缘（上游+下游）"""
    try:
        return service.get_full_lineage(
            entity_type=entity_type,
            entity_id=entity_id,
            max_depth=max_depth
        )
    except Exception as e:
        logger.error(f"Failed to get full lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/lineage/{lineage_id}",
    summary="删除血缘关系",
    tags=["Lineage"]
)
async def delete_lineage(
    lineage_id: int,
    service: DataLineageService = Depends(get_lineage_service)
):
    """删除血缘关系"""
    success = service.delete_lineage(lineage_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return {"message": "Lineage deleted successfully"}


@router.get(
    "/lineage/impact/{asset_id}",
    response_model=ImpactAnalysis,
    summary="影响分析 - 下游影响",
    tags=["Lineage Analysis"]
)
async def get_impact_analysis(
    asset_id: str,
    max_depth: int = Query(10, ge=1, le=20, description="最大深度"),
    service: DataLineageService = Depends(get_lineage_service)
):
    """影响分析 - 分析资产变更对下游的影响"""
    try:
        return service.get_impact_analysis(asset_id, max_depth=max_depth)
    except Exception as e:
        logger.error(f"Failed to get impact analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage/lineage/{asset_id}",
    response_model=DataLineageDetail,
    summary="获取数据血缘详情",
    tags=["Lineage Analysis"]
)
async def get_data_lineage(
    asset_id: str,
    max_depth: int = Query(10, ge=1, le=20, description="最大深度"),
    service: DataLineageService = Depends(get_lineage_service)
):
    """获取数据血缘详情（包含完整图谱和分析）"""
    try:
        return service.get_data_lineage_detail(asset_id, max_depth=max_depth)
    except Exception as e:
        logger.error(f"Failed to get data lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lineage/root-cause/{asset_id}",
    response_model=RootCauseAnalysis,
    summary="根因分析 - 上游溯源",
    tags=["Lineage Analysis"]
)
async def get_root_cause_analysis(
    asset_id: str,
    max_depth: int = Query(10, ge=1, le=20, description="最大深度"),
    service: DataLineageService = Depends(get_lineage_service)
):
    """根因分析 - 分析资产问题的上游根因"""
    try:
        return service.get_root_cause_analysis(asset_id, max_depth=max_depth)
    except Exception as e:
        logger.error(f"Failed to get root cause analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


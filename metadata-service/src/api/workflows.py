"""
工作流元数据API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.workflow_metadata import WorkflowMetadataSchema, WorkflowMetadataCreate, WorkflowMetadataUpdate
from ..services.metadata_catalog import MetadataCatalogService
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


def get_catalog_service(db: Session = Depends(get_db)) -> MetadataCatalogService:
    """获取元数据目录服务"""
    return MetadataCatalogService(db)


@router.post(
    "/workflows",
    response_model=WorkflowMetadataSchema,
    summary="创建工作流元数据",
    tags=["Workflows"]
)
async def create_workflow_metadata(
    workflow_data: WorkflowMetadataCreate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """创建工作流元数据"""
    try:
        return service.create_workflow_metadata(workflow_data)
    except Exception as e:
        logger.error(f"Failed to create workflow metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workflows",
    response_model=List[WorkflowMetadataSchema],
    summary="列出工作流元数据",
    tags=["Workflows"]
)
async def list_workflow_metadata(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    business_domain: Optional[str] = Query(None, description="业务领域（classification_dimensions.business.domain）"),
    standardized_tag: Optional[str] = Query(None, description="标准化标签（standardized_tags）"),
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """列出工作流元数据"""
    try:
        return service.list_workflow_metadata(
            skip=skip,
            limit=limit,
            status=status,
            category=category,
            search=search,
            business_domain=business_domain,
            standardized_tag=standardized_tag
        )
    except Exception as e:
        logger.error(f"Failed to list workflow metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowMetadataSchema,
    summary="获取工作流元数据",
    tags=["Workflows"]
)
async def get_workflow_metadata(
    workflow_id: str,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """获取工作流元数据详情（通过workflow_id）"""
    workflow = service.get_workflow_metadata(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow metadata not found")
    return workflow


@router.put(
    "/workflows/{workflow_id}",
    response_model=WorkflowMetadataSchema,
    summary="更新工作流元数据",
    tags=["Workflows"]
)
async def update_workflow_metadata(
    workflow_id: str,
    workflow_data: WorkflowMetadataUpdate,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """更新工作流元数据"""
    workflow = service.update_workflow_metadata(workflow_id, workflow_data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow metadata not found")
    return workflow


@router.delete(
    "/workflows/{workflow_id}",
    summary="删除工作流元数据",
    tags=["Workflows"]
)
async def delete_workflow_metadata(
    workflow_id: str,
    service: MetadataCatalogService = Depends(get_catalog_service)
):
    """删除工作流元数据"""
    success = service.delete_workflow_metadata(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow metadata not found")
    return {"message": "Workflow metadata deleted successfully"}


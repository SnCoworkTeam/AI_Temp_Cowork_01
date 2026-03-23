"""
企业架构数据同步API
提供数据同步和迁移的API接口
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.enterprise_architecture_sync_service import EnterpriseArchitectureSyncService
from database.src.core.neo4j_client import get_neo4j_client
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/enterprise-architecture/sync", tags=["Enterprise Architecture Sync"])
logger = setup_logger(__name__)


def get_sync_service(db: Session = Depends(get_db)) -> EnterpriseArchitectureSyncService:
    """获取同步服务实例"""
    neo4j_client = get_neo4j_client()
    return EnterpriseArchitectureSyncService(db, neo4j_client)


@router.post("/all", summary="同步所有企业架构数据到Neo4j")
async def sync_all_data(
    service: EnterpriseArchitectureSyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """同步所有企业架构数据到Neo4j"""
    try:
        # 调用同步服务的同步方法
        await service.sync_all_ea_data()
        return {
            "status": "success",
            "message": "All enterprise architecture data synchronized to Neo4j"
        }
    except AttributeError as e:
        # 如果方法不存在，尝试其他方法名
        logger.warning(f"Method sync_all_ea_data not found, trying alternative: {str(e)}")
        try:
            # 尝试调用sync_all_enterprise_architecture
            if hasattr(service, 'sync_all_enterprise_architecture'):
                result = await service.sync_all_enterprise_architecture()
                return {
                    "status": "success",
                    "message": "All enterprise architecture data synchronized to Neo4j",
                    "results": result
                }
            else:
                raise HTTPException(status_code=500, detail="Sync method not found in service")
        except Exception as e2:
            logger.error(f"Failed to sync all data: {str(e2)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e2))
    except Exception as e:
        logger.error(f"Failed to sync all data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organizations", summary="同步组织架构数据")
async def sync_organizations(
    service: EnterpriseArchitectureSyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """同步组织架构数据到Neo4j"""
    try:
        await service.sync_organization_units()
        return {
            "status": "success",
            "message": "Organization units synchronized to Neo4j"
        }
    except Exception as e:
        logger.error(f"Failed to sync organizations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-processes", summary="同步业务流程数据")
async def sync_business_processes(
    service: EnterpriseArchitectureSyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """同步业务流程数据到Neo4j"""
    try:
        await service.sync_business_processes()
        return {
            "status": "success",
            "message": "Business processes synchronized to Neo4j"
        }
    except Exception as e:
        logger.error(f"Failed to sync business processes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/application-systems", summary="同步应用系统数据")
async def sync_application_systems(
    service: EnterpriseArchitectureSyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """同步应用系统数据到Neo4j"""
    try:
        await service.sync_application_systems()
        return {
            "status": "success",
            "message": "Application systems synchronized to Neo4j"
        }
    except Exception as e:
        logger.error(f"Failed to sync application systems: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technology-instances", summary="同步技术实例数据")
async def sync_technology_instances(
    service: EnterpriseArchitectureSyncService = Depends(get_sync_service)
) -> Dict[str, Any]:
    """同步技术实例数据到Neo4j"""
    try:
        await service.sync_technology_instances()
        return {
            "status": "success",
            "message": "Technology instances synchronized to Neo4j"
        }
    except Exception as e:
        logger.error(f"Failed to sync technology instances: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


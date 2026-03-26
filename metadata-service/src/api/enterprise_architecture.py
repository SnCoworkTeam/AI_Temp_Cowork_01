"""
企业架构API路由
提供企业架构数据的API接口
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.enterprise_architecture_service import EnterpriseArchitectureService
from ..services.organization_architecture_service import OrganizationArchitectureService
from ..services.technology_instance_service import TechnologyInstanceService
from database.src.core.neo4j_client import get_neo4j_client
from luminaos_common.common.logger import setup_logger

router = APIRouter(prefix="/api/enterprise-architecture", tags=["Enterprise Architecture"])
logger = setup_logger(__name__)


def get_ea_service(db: Session = Depends(get_db)) -> EnterpriseArchitectureService:
    """获取企业架构服务实例"""
    return EnterpriseArchitectureService(db)


def get_org_service(db: Session = Depends(get_db)) -> OrganizationArchitectureService:
    """获取组织架构服务实例"""
    neo4j_client = get_neo4j_client()
    return OrganizationArchitectureService(db, neo4j_client)


def get_tech_instance_service(db: Session = Depends(get_db)) -> TechnologyInstanceService:
    """获取技术实例服务实例"""
    neo4j_client = get_neo4j_client()
    return TechnologyInstanceService(db, neo4j_client)


@router.get("/overview", summary="获取企业架构总览")
async def get_overview(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """
    获取企业架构总览数据
    包括业务架构、应用架构、数据架构、技术架构的统计
    """
    try:
        return await service.get_overview()
    except Exception as e:
        logger.error(f"Failed to get EA overview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business", summary="获取业务架构")
async def get_business_architecture(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """获取业务架构数据"""
    try:
        return await service.get_business_architecture()
    except Exception as e:
        logger.error(f"Failed to get business architecture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application", summary="获取应用架构")
async def get_application_architecture(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """获取应用架构数据"""
    try:
        return await service.get_application_architecture()
    except Exception as e:
        logger.error(f"Failed to get application architecture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data", summary="获取数据架构")
async def get_data_architecture(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """获取数据架构数据"""
    try:
        return await service.get_data_architecture()
    except Exception as e:
        logger.error(f"Failed to get data architecture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technology", summary="获取技术架构")
async def get_technology_architecture(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """获取技术架构数据"""
    try:
        return await service.get_technology_architecture()
    except Exception as e:
        logger.error(f"Failed to get technology architecture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph", summary="获取架构关系图")
async def get_architecture_graph(
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """获取架构关系图数据"""
    try:
        return await service.get_architecture_graph()
    except Exception as e:
        logger.error(f"Failed to get architecture graph: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact-analysis", summary="影响分析")
async def analyze_impact(
    entity_id: str,
    entity_type: str,
    service: EnterpriseArchitectureService = Depends(get_ea_service)
) -> Dict[str, Any]:
    """
    分析架构影响
    
    - **entity_id**: 实体ID
    - **entity_type**: 实体类型（business_process, application_system, data_entity等）
    """
    try:
        return await service.analyze_impact(entity_id, entity_type)
    except Exception as e:
        logger.error(f"Failed to analyze impact: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 组织架构API ==========

@router.get("/organizations", summary="获取组织架构列表")
async def get_organizations(
    service: OrganizationArchitectureService = Depends(get_org_service)
) -> Dict[str, Any]:
    """获取所有组织单元"""
    try:
        orgs = await service.get_all_organizations()
        return {
            "organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "code": org.code,
                    "description": org.description,
                    "organization_type": org.organization_type,
                    "level": org.level,
                    "parent_id": str(org.parent_id) if org.parent_id else None,
                    "manager_id": str(org.manager_id) if org.manager_id else None,
                    "location": org.location,
                    "status": org.status,
                    "created_at": org.created_at.isoformat() if org.created_at else None,
                    "updated_at": org.updated_at.isoformat() if org.updated_at else None
                }
                for org in orgs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get organizations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{org_id}/hierarchy", summary="获取组织层级结构")
async def get_organization_hierarchy(
    org_id: str,
    service: OrganizationArchitectureService = Depends(get_org_service)
) -> Dict[str, Any]:
    """获取组织单元的层级结构"""
    try:
        from uuid import UUID
        hierarchy = await service.get_organization_hierarchy(UUID(org_id))
        return {"hierarchy": hierarchy}
    except Exception as e:
        logger.error(f"Failed to get organization hierarchy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/root", summary="获取根组织列表")
async def get_root_organizations(
    service: OrganizationArchitectureService = Depends(get_org_service)
) -> Dict[str, Any]:
    """获取所有根组织（没有父组织的组织）"""
    try:
        root_orgs = await service.get_root_organizations()
        return {
            "organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "code": org.code,
                    "description": org.description,
                    "organization_type": org.organization_type,
                    "level": org.level,
                    "status": org.status
                }
                for org in root_orgs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get root organizations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 技术实例API ==========

@router.get("/technology/instances", summary="获取技术实例列表")
async def get_technology_instances(
    system_id: Optional[str] = Query(None, description="应用系统ID"),
    technology_name: Optional[str] = Query(None, description="技术名称"),
    service: TechnologyInstanceService = Depends(get_tech_instance_service)
) -> Dict[str, Any]:
    """获取技术实例列表"""
    try:
        from uuid import UUID
        
        if system_id:
            instances = await service.get_instances_by_system(UUID(system_id))
        elif technology_name:
            instances = await service.get_instances_by_technology(technology_name)
        else:
            # 获取所有实例
            from database.src.models.enterprise_architecture_models import TechnologyInstance
            instances = service.db.query(TechnologyInstance).all()
        
        return {
            "instances": [
                {
                    "id": str(inst.id),
                    "name": inst.name,
                    "instance_id": inst.instance_id,
                    "application_system_id": str(inst.application_system_id) if inst.application_system_id else None,
                    "application_system_name": inst.application_system.name if inst.application_system else None,
                    "technology_type": inst.technology_type,
                    "technology_name": inst.technology_name,
                    "technology_type_id": str(inst.technology_type_id) if inst.technology_type_id else None,
                    "vendor": inst.vendor,
                    "version": inst.version,
                    "deployment_type": inst.deployment_type,
                    "owner_department": inst.owner_department,
                    "owner_team": inst.owner_team,
                    "host": inst.host,
                    "port": inst.port,
                    "location": inst.location,
                    "capacity": inst.capacity,
                    "status": inst.status,
                    "created_at": inst.created_at.isoformat() if inst.created_at else None,
                    "updated_at": inst.updated_at.isoformat() if inst.updated_at else None
                }
                for inst in instances
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get technology instances: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technology/instances/by-system/{system_id}", summary="按系统获取技术实例")
async def get_instances_by_system(
    system_id: str,
    service: TechnologyInstanceService = Depends(get_tech_instance_service)
) -> Dict[str, Any]:
    """按应用系统获取技术实例"""
    try:
        from uuid import UUID
        instances = await service.get_instances_by_system(UUID(system_id))
        return {
            "instances": [
                {
                    "id": str(inst.id),
                    "name": inst.name,
                    "instance_id": inst.instance_id,
                    "technology_type": inst.technology_type,
                    "technology_name": inst.technology_name,
                    "version": inst.version,
                    "vendor": inst.vendor,
                    "status": inst.status
                }
                for inst in instances
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get instances by system: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technology/standardization", summary="获取技术标准化分析")
async def get_technology_standardization(
    service: TechnologyInstanceService = Depends(get_tech_instance_service)
) -> Dict[str, Any]:
    """获取技术标准化分析数据"""
    try:
        # 获取所有技术类型及其实例
        from database.src.models.enterprise_architecture_models import TechnologyType
        from sqlalchemy import func
        
        tech_types = service.db.query(TechnologyType).all()
        
        standardization_data = []
        for tech_type in tech_types:
            instances = service.db.query(TechnologyInstance).filter(
                TechnologyInstance.technology_type_id == tech_type.id
            ).all()
            
            # 统计版本分布
            version_dist = {}
            for inst in instances:
                version = inst.version or "unknown"
                version_dist[version] = version_dist.get(version, 0) + 1
            
            standardization_data.append({
                "technology_name": tech_type.name,
                "category": tech_type.category,
                "total_instances": len(instances),
                "version_distribution": version_dist,
                "lifecycle_status": tech_type.lifecycle_status,
                "compliance_rate": tech_type.compliance_rate or 0.0
            })
        
        return {
            "standardization": standardization_data,
            "total_technologies": len(tech_types),
            "total_instances": sum(item["total_instances"] for item in standardization_data)
        }
    except Exception as e:
        logger.error(f"Failed to get technology standardization: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


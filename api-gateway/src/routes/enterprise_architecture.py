"""
企业架构API路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import httpx
import logging
from ..config import settings

router = APIRouter(prefix="/api/enterprise-architecture", tags=["Enterprise Architecture"])
logger = logging.getLogger(__name__)


def get_metadata_service_url() -> str:
    """获取metadata-service的URL"""
    use_localhost = settings.LOCAL_DEV or settings.USE_LOCALHOST
    if use_localhost:
        return "http://localhost:8005"
    else:
        return "http://metadata-service:8005"


async def call_metadata_service(endpoint: str) -> Dict[str, Any]:
    """调用metadata-service的API"""
    try:
        metadata_url = get_metadata_service_url()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{metadata_url}{endpoint}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Metadata service returned {response.status_code} for {endpoint}")
                return {}
    except Exception as e:
        logger.error(f"Failed to call metadata service {endpoint}: {e}", exc_info=True)
        return {}


@router.get("/overview", summary="获取企业架构总览")
async def get_overview() -> Dict[str, Any]:
    """
    获取企业架构总览数据
    包括业务架构、应用架构、数据架构、技术架构的统计
    """
    try:
        # 直接调用metadata-service的企业架构API
        result = await call_metadata_service("/api/enterprise-architecture/overview")
        if result:
            return result
        
        # 如果失败，返回空数据
        return {
            "organization_architecture": {"organizations_count": 0, "departments_count": 0, "teams_count": 0, "roles_count": 0},
            "business_architecture": {"processes_count": 0, "capabilities_count": 0, "services_count": 0},
            "application_architecture": {"systems_count": 0, "services_count": 0},
            "data_architecture": {"entities_count": 0, "models_count": 0, "flows_count": 0},
            "technology_architecture": {"components_count": 0, "stacks_count": 0, "infrastructure_count": 0}
        }
    except Exception as e:
        logger.error(f"Failed to get EA overview: {e}", exc_info=True)
        return {
            "organization_architecture": {"organizations_count": 0, "departments_count": 0, "teams_count": 0, "roles_count": 0},
            "business_architecture": {"processes_count": 0, "capabilities_count": 0, "services_count": 0},
            "application_architecture": {"systems_count": 0, "services_count": 0},
            "data_architecture": {"entities_count": 0, "models_count": 0, "flows_count": 0},
            "technology_architecture": {"components_count": 0, "stacks_count": 0, "infrastructure_count": 0}
        }


@router.get("/business", summary="获取业务架构")
async def get_business_architecture() -> Dict[str, Any]:
    """获取业务架构数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/business")
        return result if result else {"processes": [], "capabilities": [], "services": []}
    except Exception as e:
        logger.error(f"Failed to get business architecture: {e}", exc_info=True)
        return {"processes": [], "capabilities": [], "services": []}


@router.get("/application", summary="获取应用架构")
async def get_application_architecture() -> Dict[str, Any]:
    """获取应用架构数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/application")
        return result if result else {"systems": [], "services": [], "apis": []}
    except Exception as e:
        logger.error(f"Failed to get application architecture: {e}", exc_info=True)
        return {"systems": [], "services": [], "apis": []}


@router.get("/data", summary="获取数据架构")
async def get_data_architecture() -> Dict[str, Any]:
    """获取数据架构数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/data")
        return result if result else {"entities": [], "models": [], "flows": []}
    except Exception as e:
        logger.error(f"Failed to get data architecture: {e}", exc_info=True)
        return {"entities": [], "models": [], "flows": []}


@router.get("/technology", summary="获取技术架构")
async def get_technology_architecture() -> Dict[str, Any]:
    """获取技术架构数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/technology")
        return result if result else {"components": [], "stacks": [], "infrastructure": []}
    except Exception as e:
        logger.error(f"Failed to get technology architecture: {e}", exc_info=True)
        return {"components": [], "stacks": [], "infrastructure": []}


@router.get("/graph", summary="获取架构关系图")
async def get_graph() -> Dict[str, Any]:
    """获取架构关系图数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/graph")
        return result if result else {"nodes": [], "links": []}
    except Exception as e:
        logger.error(f"Failed to get architecture graph: {e}", exc_info=True)
        return {"nodes": [], "links": []}


@router.post("/impact-analysis", summary="影响分析")
async def analyze_impact(request: Dict[str, Any]) -> Dict[str, Any]:
    """影响分析"""
    try:
        entity_id = request.get("entity_id")
        entity_type = request.get("entity_type")
        
        if not entity_id or not entity_type:
            raise HTTPException(status_code=400, detail="entity_id and entity_type are required")
        
        # 调用metadata-service的影响分析API
        metadata_url = get_metadata_service_url()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{metadata_url}/api/enterprise-architecture/impact-analysis",
                params={"entity_id": entity_id, "entity_type": entity_type}
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Impact analysis returned {response.status_code}")
                return {
                    "dependencies": [],
                    "impacts": [],
                    "risk_level": "low"
                }
    except Exception as e:
        logger.error(f"Failed to analyze impact: {e}", exc_info=True)
        return {"dependencies": [], "impacts": [], "risk_level": "low"}


# ========== 组织架构API ==========

@router.get("/organizations", summary="获取组织架构列表")
async def get_organizations() -> Dict[str, Any]:
    """获取所有组织单元"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/organizations")
        return result if result else {"organizations": []}
    except Exception as e:
        logger.error(f"Failed to get organizations: {e}", exc_info=True)
        return {"organizations": []}


@router.get("/organizations/{org_id}/hierarchy", summary="获取组织层级结构")
async def get_organization_hierarchy(org_id: str) -> Dict[str, Any]:
    """获取组织单元的层级结构"""
    try:
        result = await call_metadata_service(f"/api/enterprise-architecture/organizations/{org_id}/hierarchy")
        return result if result else {"hierarchy": []}
    except Exception as e:
        logger.error(f"Failed to get organization hierarchy: {e}", exc_info=True)
        return {"hierarchy": []}


@router.get("/organizations/root", summary="获取根组织列表")
async def get_root_organizations() -> Dict[str, Any]:
    """获取所有根组织"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/organizations/root")
        return result if result else {"organizations": []}
    except Exception as e:
        logger.error(f"Failed to get root organizations: {e}", exc_info=True)
        return {"organizations": []}


# ========== 技术实例API ==========

@router.get("/technology/instances", summary="获取技术实例列表")
async def get_technology_instances(
    system_id: Optional[str] = None,
    technology_name: Optional[str] = None
) -> Dict[str, Any]:
    """获取技术实例列表"""
    try:
        params = {}
        if system_id:
            params["system_id"] = system_id
        if technology_name:
            params["technology_name"] = technology_name
        
        metadata_url = get_metadata_service_url()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{metadata_url}/api/enterprise-architecture/technology/instances",
                params=params
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Technology instances returned {response.status_code}")
                return {"instances": []}
    except Exception as e:
        logger.error(f"Failed to get technology instances: {e}", exc_info=True)
        return {"instances": []}


@router.get("/technology/instances/by-system/{system_id}", summary="按系统获取技术实例")
async def get_instances_by_system(system_id: str) -> Dict[str, Any]:
    """按应用系统获取技术实例"""
    try:
        result = await call_metadata_service(f"/api/enterprise-architecture/technology/instances/by-system/{system_id}")
        return result if result else {"instances": []}
    except Exception as e:
        logger.error(f"Failed to get instances by system: {e}", exc_info=True)
        return {"instances": []}


@router.get("/technology/standardization", summary="获取技术标准化分析")
async def get_technology_standardization() -> Dict[str, Any]:
    """获取技术标准化分析数据"""
    try:
        result = await call_metadata_service("/api/enterprise-architecture/technology/standardization")
        return result if result else {"standardization": [], "total_technologies": 0, "total_instances": 0}
    except Exception as e:
        logger.error(f"Failed to get technology standardization: {e}", exc_info=True)
        return {"standardization": [], "total_technologies": 0, "total_instances": 0}


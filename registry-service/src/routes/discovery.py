"""
服务发现路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Dict, Any, Optional
import logging
from ..services.registry_service import RegistryService
from ..models.service_models import ServiceInfo

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_registry_service(request: Request):
    """获取注册服务实例"""
    # 详细诊断日志
    if not hasattr(request.app.state, 'registry_service'):
        logger.error(f"❌ app.state has no 'registry_service' attribute. Available attributes: {dir(request.app.state)}")
        raise HTTPException(status_code=503, detail="Registry service not initialized: app.state has no 'registry_service' attribute")
    
    service = getattr(request.app.state, 'registry_service', None)
    if service is None:
        logger.error(f"❌ app.state.registry_service is None. app.state contents: {dir(request.app.state)}")
        raise HTTPException(status_code=503, detail="Registry service not initialized: app.state.registry_service is None")
    
    logger.debug(f"✅ Successfully retrieved registry_service from app.state: {type(service)}")
    return service


@router.get("/discover/{service_name}", response_model=ServiceInfo)
async def discover_service(
    service_name: str,
    request: Request,
    load_balancing: Optional[str] = Query("round_robin", description="负载均衡策略: round_robin, random, least_connections"),
    registry: RegistryService = Depends(get_registry_service)
):
    """服务发现 - 返回一个可用的服务实例"""
    try:
        service = await registry.discover_service(service_name, load_balancing)
        if not service:
            # 如果没有健康服务，尝试返回不健康的服务
            services = await registry.get_services_by_name(service_name)
            if services:
                # 返回第一个服务实例（即使不健康）
                return services[0]
            raise HTTPException(status_code=404, detail=f"No instance of service '{service_name}' found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering service {service_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover-all/{service_name}", response_model=List[ServiceInfo])
async def discover_all_services(
    service_name: str,
    request: Request,
    include_unhealthy: bool = Query(False, description="是否包含不健康的服务实例"),
    registry: RegistryService = Depends(get_registry_service)
):
    """获取服务的所有实例"""
    try:
        services = await registry.discover_all_services(service_name, include_unhealthy)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints/{service_name}")
async def get_service_endpoints(
    service_name: str,
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """获取服务的所有端点URL"""
    try:
        endpoints = await registry.get_service_endpoints(service_name)
        return {
            "service_name": service_name,
            "endpoints": endpoints,
            "count": len(endpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_discovery_stats(
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """获取服务发现统计信息"""
    try:
        stats = await registry.get_discovery_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
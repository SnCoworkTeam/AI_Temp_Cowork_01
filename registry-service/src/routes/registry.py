"""
服务注册路由
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from ..models.service_models import ServiceRegistration, ServiceInfo, ServiceStatus
from ..services.registry_service import RegistryService

router = APIRouter()

async def get_registry_service(request: Request):
    """获取注册服务实例"""
    import logging
    logger = logging.getLogger(__name__)
    
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


@router.post("/register", response_model=Dict[str, Any])
async def register_service(
    registration: ServiceRegistration,
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """注册服务"""
    try:
        service_id = await registry.register_service(registration)
        return {
            "success": True,
            "service_id": service_id,
            "message": f"Service '{registration.name}' registered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/unregister/{service_id}")
async def unregister_service(
    service_id: str,
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """注销服务"""
    try:
        await registry.unregister_service(service_id)
        return {
            "success": True,
            "message": f"Service {service_id} unregistered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/heartbeat/{service_id}")
async def heartbeat(
    service_id: str,
    request: Request,
    status: Optional[ServiceStatus] = None,
    registry: RegistryService = Depends(get_registry_service)
):
    """服务心跳"""
    try:
        await registry.update_heartbeat(service_id, status)
        return {
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/services", response_model=List[ServiceInfo])
async def list_services(
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """获取所有已注册服务"""
    try:
        services = await registry.get_all_services()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_name}", response_model=List[ServiceInfo])
async def get_service_by_name(
    service_name: str,
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """根据服务名获取服务实例"""
    try:
        services = await registry.get_services_by_name(service_name)
        if not services:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{service_id}")
async def get_service_health(
    service_id: str,
    request: Request,
    registry: RegistryService = Depends(get_registry_service)
):
    """获取服务健康状态"""
    try:
        health_info = await registry.get_service_health(service_id)
        return health_info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
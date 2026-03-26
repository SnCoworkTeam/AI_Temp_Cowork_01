"""
健康检查路由
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """服务健康检查"""
    return {
        "status": "healthy",
        "service": "registry-service",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(request: Request):
    """服务就绪检查"""
    try:
        # 检查Redis连接
        registry_service = getattr(request.app.state, 'registry_service', None)
        if registry_service is None:
            raise HTTPException(status_code=503, detail="Registry service not initialized")

        # 尝试ping Redis
        await registry_service.ping()

        return {
            "status": "ready",
            "service": "registry-service",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "redis": "connected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/metrics")
async def get_metrics(request: Request):
    """获取服务指标"""
    registry_service = getattr(request.app.state, 'registry_service', None)
    if registry_service is None:
        raise HTTPException(status_code=503, detail="Registry service not initialized")

    try:
        metrics = await registry_service.get_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
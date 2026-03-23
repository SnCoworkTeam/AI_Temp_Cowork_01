"""
Registry Service主应用
提供服务注册与发现功能
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging
import asyncio
from typing import AsyncGenerator

from .config import settings
from .routes import registry, discovery, health
from .services.registry_service import RegistryService
from .services.health_checker import HealthChecker

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 全局变量
redis_client: redis.Redis = None
registry_service: RegistryService = None
health_checker: HealthChecker = None
health_check_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期管理"""
    global redis_client, registry_service, health_checker, health_check_task

    # 启动时初始化
    logger.info("Starting Registry Service...")

    try:
        # 初始化Redis连接
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        if settings.REDIS_PASSWORD:
            redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

        redis_client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        # 测试Redis连接
        await redis_client.ping()
        logger.info("Redis connection established")

        # 初始化服务
        registry_service = RegistryService(redis_client, settings.SERVICE_TTL)
        health_checker = HealthChecker(registry_service)
        
        # 将服务实例存储到 app.state
        app.state.registry_service = registry_service
        app.state.health_checker = health_checker
        
        # 验证 app.state 是否设置成功
        if not hasattr(app.state, 'registry_service') or app.state.registry_service is None:
            raise RuntimeError("Failed to set registry_service in app.state")
        logger.info(f"✅ registry_service stored in app.state: {type(app.state.registry_service)}")

        # 启动健康检查循环
        health_check_task = asyncio.create_task(
            health_checker.start_health_check_loop(settings.HEALTH_CHECK_INTERVAL)
        )

        logger.info(f"Registry Service started successfully on {settings.HOST}:{settings.PORT}")
        logger.info(f"✅ App state initialized: registry_service={hasattr(app.state, 'registry_service')}, health_checker={hasattr(app.state, 'health_checker')}")

        yield

    except Exception as e:
        logger.error(f"Failed to start Registry Service: {e}")
        raise

    finally:
        # 关闭时清理资源
        logger.info("Shutting down Registry Service...")

        if health_check_task:
            health_check_task.cancel()
            try:
                await health_check_task
            except asyncio.CancelledError:
                pass

        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")

        logger.info("Registry Service shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="Registry Service",
    description="服务注册与发现中心",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["Health"])
app.include_router(registry.router, prefix="/api", tags=["Registry"])
app.include_router(discovery.router, prefix="/api", tags=["Discovery"])


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Registry Service",
        "version": "1.0.0",
        "status": "running",
    }


# 提供全局访问
def get_registry_service() -> RegistryService:
    """获取registry service实例"""
    return registry_service

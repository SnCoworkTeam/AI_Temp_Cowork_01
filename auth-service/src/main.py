"""
认证服务主应用
支持SSL单点登录（SSO）的认证服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .routes import health, auth, users, monitoring
from .routes.monitoring import _update_api_stats
from .routes.admin import users as admin_users, roles, permissions, menus
from .sso.cache_manager import cache_manager
from .core.database import init_database, close_database
from shared_libs.luminaos_common.common.logger import setup_logger
from shared_libs.luminaos_common.common.error_handler import create_error_response

# 导入统一错误处理框架
try:
    from shared_libs.luminaos_common.common.error_middleware import setup_exception_handlers
    from shared_libs.luminaos_common.common.request_tracking import setup_request_tracking
    ERROR_FRAMEWORK_AVAILABLE = True
except ImportError:
    ERROR_FRAMEWORK_AVAILABLE = False
    logging.warning("统一错误处理框架不可用，使用基础错误处理")

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Auth Service starting up...")

    # 初始化数据库连接
    try:
        if init_database():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # 不阻止启动，但会影响数据库功能

    # 初始化Redis连接
    try:
        await cache_manager.connect()
        logger.info("Cache manager connected")
    except Exception as e:
        logger.error(f"Failed to connect cache manager: {str(e)}")
        # 不阻止启动，但会影响缓存功能

    # 注册服务到registry-service
    service_id = None
    try:
        import httpx
        import os
        registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{registry_url}/api/register",
                json={
                    "name": "auth-service",
                    "host": os.getenv("SERVICE_HOST", "auth-service"),
                    "port": int(os.getenv("SERVICE_PORT", "8003")),
                    "service_type": "http",  # 必须是小写
                    "health_check_url": "/health",
                    "metadata": {"version": "1.0.0"},
                    "tags": ["auth", "authentication"]
                },
                timeout=10.0  # 增加超时时间
            )
            if response.status_code in [200, 201]:
                result = response.json()
                service_id = result.get("service_id")
                logger.info(f"✅ Service registered successfully with ID: {service_id}")
            else:
                logger.warning(f"❌ Failed to register service: {response.status_code}, response: {response.text}")
    except Exception as e:
        logger.warning(f"❌ Failed to register with registry-service: {str(e)}", exc_info=True)
        # 不阻止启动

    yield

    # 清理资源
    logger.info("Auth Service shutting down...")

    # 注销服务
    if service_id:
        try:
            import httpx
            import os
            registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{registry_url}/api/unregister/{service_id}",
                    timeout=5.0
                )
                logger.info(f"Service unregistered: {service_id}")
        except Exception as e:
            logger.warning(f"Failed to unregister service: {str(e)}")

    try:
        await cache_manager.disconnect()
    except Exception as e:
        logger.error(f"Failed to disconnect cache manager: {str(e)}")

    try:
        close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="LuminaOS - 认证服务",
    description="支持SSL单点登录（SSO）的认证服务，提供OAuth 2.0/OpenID Connect集成",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置统一错误处理和请求追踪
if ERROR_FRAMEWORK_AVAILABLE:
    try:
        setup_request_tracking(app)
        setup_exception_handlers(app)
        logger.info("✅ 统一错误处理框架已启用")
    except Exception as e:
        logger.error(f"Failed to setup error framework: {e}")
        # 降级到基础错误处理
        @app.exception_handler(Exception)
        async def global_exception_handler(request, exc):
            """全局异常处理（降级）"""
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            return create_error_response(
                status_code=500,
                message="Internal server error",
                details=str(exc)
            )
else:
    # 基础全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """全局异常处理"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return create_error_response(
            status_code=500,
            message="Internal server error",
            details=str(exc)
        )

# 注册路由
app.include_router(health.router)
app.include_router(auth.router)  # 保留SSO相关路由
app.include_router(users.router)

# 注册增强的认证路由（集成数据库）
from .routes import auth_enhanced
app.include_router(auth_enhanced.router)

# 注册管理后台路由
app.include_router(admin_users.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(menus.router)

# 注册监控路由
app.include_router(monitoring.router, tags=["Monitoring"])

# 注册数据分类路由
from .routes import data_classification
app.include_router(data_classification.router)

# 注册请求日志和监控中间件
@app.middleware("http")
async def log_and_monitor_requests(request, call_next):
    """记录请求日志和监控统计"""
    import time
    start_time = time.time()
    
    # 注意：不要读取request.body()，这会消费请求体，导致FastAPI无法解析JSON
    # 如果需要记录请求体，应该使用request.stream()或request.form()，但不要在这里读取
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # 更新监控统计
    _update_api_stats(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        response_time=process_time
    )
    
    return response


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "status": "running"
    }

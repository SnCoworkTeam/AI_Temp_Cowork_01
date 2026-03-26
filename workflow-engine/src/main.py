"""
Workflow Engine - LangGraph主应用
提供业务流程自动化引擎服务
"""
import sys
import os

# 添加 shared_libs 到 Python 路径（必须在导入 shared_libs 之前）
# 获取项目根目录（workflow-engine的父目录）
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_dir))
_shared_libs_path = os.path.join(_project_root, 'shared_libs')

# 添加shared_libs路径（支持Windows和Linux）
if _shared_libs_path not in sys.path:
    sys.path.insert(0, _shared_libs_path)
# 兼容Docker环境路径
if '/shared_libs' not in sys.path:
    sys.path.insert(0, '/shared_libs')
if '/app/../shared_libs' not in sys.path:
    sys.path.insert(0, '/app/../shared_libs')

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from .routes import health, workflows, monitoring
from .routes.monitoring import _update_api_stats
from .config import settings
from .core.database import init_database, close_database
from shared_libs.luminaos_common.common.logger import setup_logger
from shared_libs.luminaos_common.common.error_handler import create_error_response

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Workflow Engine starting up...")
    
    # 初始化数据库连接
    try:
        if init_database():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # 不阻止启动，但会影响数据库功能
    
    # 从配置中心加载LLM配置
    try:
        from .routes.ai_client import AIClient
        # AIClient 会在初始化时尝试从配置中心加载配置
        logger.info("LLM configuration will be loaded from config center on first use")
    except Exception as e:
        logger.warning(f"Failed to initialize AI client: {e}")
    
    # LangGraph运行时通过DynamicWorkflowEngine动态初始化
    # 当工作流被创建时，会自动构建LangGraph图
    # 无需在启动时预先初始化
    yield
    
    # 清理资源
    logger.info("Workflow Engine shutting down...")
    try:
        close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="Workflow Engine API",
    description="LuminaOS - 工作流引擎服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求验证错误处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证错误处理器"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8') if body else 'Empty body'
    except Exception:
        body_str = 'Could not read body'
    
    logger.error(f"Validation error on {request.method} {request.url.path}")
    
    # 安全地序列化错误信息
    errors = exc.errors()
    serializable_errors = []
    for error in errors:
        try:
            # 确保所有值都是可序列化的
            serializable_error = {}
            for key, value in error.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serializable_error[key] = value
                elif isinstance(value, (list, dict)):
                    serializable_error[key] = value
                else:
                    serializable_error[key] = str(value)
            serializable_errors.append(serializable_error)
        except Exception as e:
            logger.warning(f"Error serializing validation error: {e}")
            serializable_errors.append({"msg": str(error)})
    
    logger.error(f"Validation errors: {serializable_errors}")
    logger.error(f"Request body: {body_str[:500]}")  # 只记录前500字符
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": serializable_errors,
            "body_preview": body_str[:200] if body_str else None
        }
    )


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        status_code=500,
        message="Internal server error",
        details=str(exc)
    )


# 请求日志和监控中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志和监控统计"""
    start_time = time.time()
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


# API版本前缀
API_V1_PREFIX = "/api/v1"

# 注册路由 - 全部使用v1版本前缀
app.include_router(health.router, prefix=API_V1_PREFIX, tags=["Health"])

# 注册工作流设计器路由（优先注册，因为它有更完整的 list_workflows 实现）
from .routes import workflow_designer, workflow_execution, workflow_versions, workflow_metrics, agent_api
app.include_router(
    workflow_designer.router,
    prefix=f"{API_V1_PREFIX}/workflows",
    tags=["Workflow Designer"]
)

# 注册旧的工作流路由（向后兼容，但 list_workflows 已注释）
app.include_router(workflows.router, prefix=f"{API_V1_PREFIX}/workflows", tags=["Workflows"])

# 注册执行管理路由
app.include_router(workflow_execution.router, prefix=API_V1_PREFIX)

# 注册版本管理路由
app.include_router(workflow_versions.router, prefix=API_V1_PREFIX)

# 注册性能监控路由
app.include_router(workflow_metrics.router, prefix=API_V1_PREFIX)

# 注册监控路由
app.include_router(monitoring.router, prefix=API_V1_PREFIX, tags=["Monitoring"])

# 注册智能体管理路由
app.include_router(agent_api.router, tags=["Agents"])

# 注册智能体工作流路由（前端AgentWorkflowInterface所需）
from .routes import agent_workflow_routes
app.include_router(agent_workflow_routes.router, tags=["Agent Workflow"])

# 注册BPMN路由
from .routes import bpmn_routes
app.include_router(bpmn_routes.router, prefix=API_V1_PREFIX, tags=["BPMN"])

# 保留旧的/api路由以实现向后兼容（标记为deprecated）
app.include_router(health.router, prefix="/api", tags=["Health (deprecated)"], deprecated=True)
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows (deprecated)"], deprecated=True)
# 向后兼容：工作流设计器路由也注册到 /api/workflows
app.include_router(
    workflow_designer.router,
    prefix="/api/workflows",
    tags=["Workflow Designer (deprecated)"],
    deprecated=True
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Workflow Engine",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


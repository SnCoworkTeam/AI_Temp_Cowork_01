"""
Knowledge Base - FastAPI主应用
提供企业知识库管理服务
"""
import sys
import os
import importlib.util

# 确保 shared_libs 可以被导入（必须在导入 shared_libs 之前）
# 方法1: 添加路径到 sys.path
for path in ['/shared_libs', '/app/../shared_libs']:
    if os.path.exists(path):
        real_path = os.path.realpath(path)
        if real_path not in sys.path:
            sys.path.insert(0, real_path)
        if path not in sys.path and path != real_path:
            sys.path.insert(0, path)

# 方法2: 如果标准导入失败，使用 importlib 强制加载
if 'shared_libs' not in sys.modules:
    try:
        spec = importlib.util.spec_from_file_location(
            "shared_libs",
            "/shared_libs/__init__.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules['shared_libs'] = module
    except Exception:
        pass  # 如果失败，尝试标准导入

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import os
import asyncio
import httpx
from contextlib import asynccontextmanager
from datetime import datetime

from .routes import health, documents, search, knowledge_graph, maintenance
from .config import settings
from .core.database import init_database, close_database
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

# 设置日志
logger = setup_logger(__name__)

# 服务注册相关变量
service_id: str | None = None
http_client: httpx.AsyncClient | None = None
heartbeat_task: asyncio.Task | None = None


async def register_to_registry():
    """注册到服务发现中心"""
    global service_id, http_client
    
    registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
    service_host = os.getenv("SERVICE_HOST", "knowledge-base")
    service_port = int(os.getenv("PORT", str(settings.PORT)))
    
    http_client = httpx.AsyncClient(timeout=10.0)
    
    registration_data = {
        "name": "knowledge-base",
        "host": service_host,
        "port": service_port,
        "service_type": "http",
        "health_check_url": f"http://{service_host}:{service_port}/api/health",
        "metadata": {
            "description": "知识库管理服务，提供文档管理、搜索和知识图谱功能",
            "version": "1.0.0"
        },
        "tags": ["knowledge", "document", "search", "vector"]
    }
    
    try:
        response = await http_client.post(
            f"{registry_url}/api/register",
            json=registration_data
        )
        response.raise_for_status()
        result = response.json()
        service_id = result.get("service_id")
        logger.info(f"Knowledge Base Service registered successfully, service_id: {service_id}")
        return service_id
    except Exception as e:
        logger.warning(f"Failed to register to registry service: {str(e)}")
        return None


async def send_heartbeat():
    """发送心跳"""
    global service_id, http_client
    
    if not service_id or not http_client:
        return
    
    registry_url = os.getenv("REGISTRY_SERVICE_URL", "http://registry-service:8000")
    
    try:
        response = await http_client.post(
            f"{registry_url}/api/heartbeat/{service_id}"
        )
        response.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to send heartbeat: {str(e)}")


async def heartbeat_loop():
    """心跳循环"""
    while True:
        try:
            await send_heartbeat()
            await asyncio.sleep(10)  # 每10秒发送一次心跳
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {str(e)}")
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global heartbeat_task
    
    logger.info("Knowledge Base Service starting up...")
    logger.info(f"Service will listen on {settings.HOST}:{settings.PORT}")
    
    # 初始化数据库连接
    try:
        if init_database():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        # 不阻止启动，但会影响数据库功能
    
    # 初始化向量存储
    try:
        from .core.vector_store import get_vector_store
        vector_store = get_vector_store()
        logger.info("Vector store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
    
    # 初始化嵌入模型
    try:
        from .core.embedding_manager import get_embedding_manager
        embedding_manager = get_embedding_manager()
        logger.info(f"Embedding manager initialized: dimension={embedding_manager.get_dimension()}")
    except Exception as e:
        logger.error(f"Failed to initialize embedding manager: {str(e)}", exc_info=True)
    
    # 确保存储目录存在
    os.makedirs(settings.DOCUMENT_STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    logger.info(f"Storage directories ready: {settings.DOCUMENT_STORAGE_DIR}, {settings.CHROMA_PERSIST_DIR}")
    
    # 注册到服务发现中心
    try:
        await register_to_registry()
        # 启动心跳任务
        heartbeat_task = asyncio.create_task(heartbeat_loop())
    except Exception as e:
        logger.warning(f"Service registration skipped: {str(e)}")
    
    logger.info("Knowledge Base Service started successfully")
    
    yield
    
    # 清理资源
    logger.info("Knowledge Base Service shutting down...")
    
    # 停止心跳任务
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    
    # 关闭HTTP客户端
    if http_client:
        await http_client.aclose()
    
    try:
        close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database: {str(e)}")
    
    logger.info("Knowledge Base Service shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="Knowledge Base API",
    description="""
    企业AI平台 - 知识库管理服务
    
    ## 功能特性
    
    - 📄 **文档管理**: 支持多种文档格式的上传、解析和管理
    - 🔍 **智能搜索**: 语义搜索和关键词搜索
    - 📊 **向量存储**: 基于Chroma/Weaviate的向量数据库
    - 🕸️ **知识图谱**: 实体和关系管理
    - 🔄 **文档处理**: 自动文档解析、分块和向量化
    
    ## 支持的文档格式
    
    - PDF (.pdf)
    - Word (.doc, .docx)
    - Excel (.xls, .xlsx)
    - 文本 (.txt)
    - Markdown (.md, .markdown)
    
    ## API端点
    
    - `POST /api/documents/upload` - 上传文档
    - `GET /api/documents` - 获取文档列表
    - `GET /api/documents/{id}` - 获取文档详情
    - `DELETE /api/documents/{id}` - 删除文档
    - `POST /api/search/semantic` - 语义搜索
    - `POST /api/search/keyword` - 关键词搜索
    - `GET /api/knowledge-graph` - 获取知识图谱
    - `GET /api/health` - 健康检查
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {
            "name": "Documents",
            "description": "文档管理操作"
        },
        {
            "name": "Search",
            "description": "智能搜索功能"
        },
        {
            "name": "Knowledge Graph",
            "description": "知识图谱管理"
        },
        {
            "name": "Health",
            "description": "健康检查端点"
        },
        {
            "name": "Maintenance",
            "description": "知识库维护功能"
        }
    ]
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    # 记录请求到达
    logger.info(
        f"Request received: {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.3f}s",
            exc_info=True
        )
        # 重新抛出异常，让全局异常处理器处理
        raise


# 注册路由
app.include_router(health.router, prefix="/api", tags=["Health"])

# 注册数据库集成版本的路由
from .routes import documents_db, search_db, knowledge_graph_db, analytics, knowledge_bases, document_progress, chunks
app.include_router(documents_db.router, prefix="/api", tags=["Documents"])
app.include_router(search_db.router, prefix="/api", tags=["Search"])
app.include_router(knowledge_graph_db.router, prefix="/api", tags=["Knowledge Graph"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(knowledge_bases.router, prefix="/api", tags=["Knowledge Bases"])
app.include_router(document_progress.router, prefix="/api", tags=["Document Progress"])
app.include_router(chunks.router, prefix="/api", tags=["Chunks"])

# 保留原有路由（向后兼容）
app.include_router(documents.router, prefix="/api/legacy", tags=["Documents (Legacy)"])
app.include_router(search.router, prefix="/api/legacy", tags=["Search (Legacy)"])
app.include_router(knowledge_graph.router, prefix="/api/legacy", tags=["Knowledge Graph (Legacy)"])

app.include_router(maintenance.router, prefix="/api", tags=["Maintenance"])

# 注册本体构建路由
from .routes import ontology
app.include_router(ontology.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Knowledge Base",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health"
        }
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


"""
向量协调服务主应用
统一向量空间管理、多模态向量融合、向量相似度服务
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .routes import vectors, health
from luminaos_common.common.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Vector Coordinator Service starting up...")
    
    # 初始化统一向量模型管理器
    from .core.embedding_manager import get_unified_embedding_manager
    embedding_manager = get_unified_embedding_manager()
    
    if embedding_manager.is_available():
        logger.info(f"Unified embedding model loaded: {embedding_manager.model_name}")
        logger.info(f"Vector dimension: {embedding_manager.get_dimension()}")
    else:
        logger.warning("Embedding model not available, using mock embeddings")
    
    # 启动批量写入管理器（如果启用）
    from .services.vector_coordinator_service import VectorCoordinatorService
    service = VectorCoordinatorService()
    if service.batch_writer:
        await service.batch_writer.start()
        logger.info("Batch writer started")
    
    logger.info(f"Vector Coordinator Service started on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # 停止批量写入管理器
    if service.batch_writer:
        await service.batch_writer.stop()
        logger.info("Batch writer stopped")
    
    logger.info("Vector Coordinator Service shutting down...")


# 创建FastAPI应用
app = FastAPI(
    title="企业AI平台 - 向量协调服务",
    description="""
    向量协调服务 - 统一向量空间管理
    
    ## 功能特性
    
    - 🔗 **统一向量模型管理**: 确保所有服务使用相同的模型和版本
    - 🔀 **多模态向量融合**: 支持加权平均、拼接、注意力机制等融合策略
    - 🔍 **向量相似度服务**: 提供向量相似度计算和搜索功能
    - 📊 **向量注册管理**: 统一管理来自不同服务的向量
    
    ## API端点
    
    ### 向量管理
    - `POST /api/vectors/register` - 注册向量
    - `GET /api/vectors/info/{entity_uri}` - 获取向量信息
    - `GET /api/vectors/stats` - 获取统计信息
    
    ### 向量融合
    - `POST /api/vectors/fuse` - 融合多个模态的向量
    
    ### 相似度搜索
    - `POST /api/vectors/similar` - 查找相似向量
    
    ### 健康检查
    - `GET /health` - 健康检查
    - `GET /health/ready` - 就绪检查
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(vectors.router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Vector Coordinator Service",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Unified Vector Model Management",
            "Multi-modal Vector Fusion",
            "Vector Similarity Service",
            "Vector Registry"
        ]
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )



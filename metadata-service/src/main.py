"""
元数据服务主应用
提供数据资产、AI模型、业务实体和工作流的元数据管理
"""
import sys
from pathlib import Path

# 添加项目根目录到路径，以便导入shared_libs
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from .core.config import settings
from .core.database import init_database, close_database
from .api import health, data_assets, ai_models, business_entities, workflows, search, lineage, quality, workflow_versions, realtime_metadata, quality_rules, entity_models, entity_mapping, ontology, entity_registry, recommendation, classifications, enterprise_architecture, enterprise_architecture_sync, classification_migration
from .collectors.collection_manager import get_collection_manager, close_collection_manager
from luminaos_common.common.logger import setup_logger
from luminaos_common.common.error_handler import create_error_response

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Metadata Service starting up...")
    
    # 初始化数据库连接
    try:
        if init_database():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # 不阻止启动，但会影响数据库功能
    
    # 服务启动时：注册基础元数据
    try:
        collection_manager = get_collection_manager()
        logger.info("Starting metadata registration on startup...")
        # 在后台异步执行，不阻塞服务启动
        asyncio.create_task(collection_manager.register_on_startup())
    except Exception as e:
        logger.warning(f"Failed to start metadata collection on startup: {str(e)}")
    
    yield
    
    # 清理资源
    logger.info("Metadata Service shutting down...")
    try:
        await close_collection_manager()
    except Exception as e:
        logger.error(f"Failed to close collection manager: {str(e)}")
    
    try:
        close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="企业AI平台 - 元数据服务",
    description="""
    企业AI平台 - 元数据管理服务
    
    ## 功能特性
    
    - 📊 **数据资产元数据**: 管理数据集的元数据信息
    - 🤖 **AI模型元数据**: 管理AI模型的元数据信息
    - 🏢 **业务实体元数据**: 管理业务实体和术语
    - 🔄 **工作流元数据**: 管理工作流的元数据信息
    - 🔗 **数据血缘**: 追踪数据之间的依赖和转换关系
    - 🔍 **元数据搜索**: 全文搜索和标签搜索
    - ✅ **数据质量**: 数据质量指标管理和监控
    
    ## API端点
    
    ### 数据资产
    - `POST /api/data-assets` - 创建数据资产
    - `GET /api/data-assets` - 列出数据资产
    - `GET /api/data-assets/{id}` - 获取数据资产详情
    - `PUT /api/data-assets/{id}` - 更新数据资产
    - `DELETE /api/data-assets/{id}` - 删除数据资产
    
    ### 搜索
    - `GET /api/search` - 全局搜索
    - `GET /api/search/tags` - 按标签搜索
    - `GET /api/search/popular-tags` - 获取热门标签
    
    ### 数据血缘
    - `POST /api/lineage` - 创建血缘关系
    - `GET /api/lineage` - 列出血缘关系
    - `GET /api/lineage/upstream/{type}/{id}` - 获取上游血缘
    - `GET /api/lineage/downstream/{type}/{id}` - 获取下游血缘
    - `GET /api/lineage/full/{type}/{id}` - 获取完整血缘
    - `GET /api/lineage/impact/{asset_id}` - 影响分析（下游影响）
    - `GET /api/lineage/lineage/{asset_id}` - 获取数据血缘详情
    - `GET /api/lineage/root-cause/{asset_id}` - 根因分析（上游溯源）
    
    ### 元数据API
    - `GET /api/metadata/assets` - 列出数据资产（支持分类、业务域、质量分数过滤）
    - `GET /api/metadata/assets/{asset_id}` - 获取资产详情（包含血缘关系）
    - `GET /api/metadata/search` - 搜索元数据（返回结构化结果）
    
    ### 数据质量
    - `PUT /api/quality/assets/{id}/metrics` - 更新质量指标
    - `GET /api/quality/assets/{id}/metrics` - 获取质量指标
    - `GET /api/quality/metrics/{asset_id}` - 获取数据质量指标（标准化格式）
    - `POST /api/quality/checks/{asset_id}` - 执行质量检查
    - `GET /api/quality/dashboard` - 质量监控仪表板
    - `GET /api/quality/summary` - 获取质量摘要
    - `GET /api/quality/issues` - 获取质量问题
    
    ### 健康检查
    - `GET /api/health` - 健康检查
    - `GET /api/health/ready` - 就绪检查
    - `GET /api/health/live` - 存活检查
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {
            "name": "Data Assets",
            "description": "数据资产元数据管理"
        },
        {
            "name": "AI Models",
            "description": "AI模型元数据管理"
        },
        {
            "name": "Business Entities",
            "description": "业务实体元数据管理"
        },
        {
            "name": "Workflows",
            "description": "工作流元数据管理"
        },
        {
            "name": "Search",
            "description": "元数据搜索功能"
        },
        {
            "name": "Lineage",
            "description": "数据血缘管理"
        },
        {
            "name": "Lineage Analysis",
            "description": "数据血缘分析（影响分析、根因分析）"
        },
        {
            "name": "Metadata",
            "description": "元数据API（统一接口）"
        },
        {
            "name": "Quality",
            "description": "数据质量管理"
        },
        {
            "name": "Health",
            "description": "健康检查端点"
        }
    ]
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
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
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(data_assets.router, prefix="/api", tags=["Data Assets"])
app.include_router(ai_models.router, prefix="/api", tags=["AI Models"])
app.include_router(business_entities.router, prefix="/api", tags=["Business Entities"])
app.include_router(workflows.router, prefix="/api", tags=["Workflows"])
app.include_router(workflow_versions.router, prefix="/api", tags=["Workflow Versions"])

# 注册其他API路由
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(lineage.router, prefix="/api", tags=["Lineage"])
app.include_router(quality.router, prefix="/api", tags=["Quality"])
app.include_router(quality_rules.router, prefix="/api", tags=["Quality Rules"])
app.include_router(realtime_metadata.router, prefix="/api/v1", tags=["Metadata"])
app.include_router(classifications.router, prefix="/api/metadata", tags=["Metadata"])
app.include_router(classification_migration.router, prefix="/api", tags=["Classification"])
app.include_router(enterprise_architecture.router, tags=["Enterprise Architecture"])
app.include_router(enterprise_architecture_sync.router, tags=["Enterprise Architecture Sync"])
app.include_router(entity_models.router, tags=["Entity Models"])  # 路由已有prefix="/api/models"
app.include_router(entity_mapping.router, tags=["Entity Mapping"])  # 路由已有prefix="/api/entity-mapping"
app.include_router(entity_registry.router, tags=["Entity Registry"])  # 路由已有prefix="/api/entity-registry"
app.include_router(recommendation.router, tags=["Recommendation"])  # 路由已有prefix="/api/recommendation"

# 注册采集API路由
from .api import collection, lineage_tracking
app.include_router(collection.router, prefix="/api", tags=["Collection"])
app.include_router(lineage_tracking.router, prefix="/api", tags=["Lineage Tracking"])
app.include_router(ontology.router, tags=["Ontology"])  # 路由已有prefix="/api/ontology"
from .api import knowledge_graph, document_entity_linker, knowledge_graph_visualization
app.include_router(knowledge_graph.router, tags=["Knowledge Graph"])  # 路由已有prefix="/api/knowledge-graph"
app.include_router(document_entity_linker.router, tags=["Document Entity Linker"])  # 路由已有prefix="/api/document-entity-linker"
app.include_router(knowledge_graph_visualization.router, tags=["Knowledge Graph Visualization"])  # 路由已有prefix="/api/knowledge-graph/viz"
try:
    from .api import neo4j_api
    app.include_router(neo4j_api.router, tags=["Neo4j"])  # 路由已有prefix="/api/neo4j"
except ImportError:
    logger.warning("neo4j_api module not found, skipping")
from .api import intelligent_quality
app.include_router(intelligent_quality.router, tags=["Intelligent Quality"])  # 路由已有prefix="/api/intelligent-quality"

# 注册请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    """记录请求日志"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "metadata-service",
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
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


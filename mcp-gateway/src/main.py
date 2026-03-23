"""
MCP Gateway - FastAPI主应用
提供MCP工具的统一网关服务
"""
import sys
import os

# 修复shared_libs导入路径 - 必须在所有导入之前
if '/shared_libs' not in sys.path:
    sys.path.insert(0, '/shared_libs')

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from .routes import health, tools, monitoring
from .config import settings
from .core.database import init_database, close_database
from shared_libs.luminaos_common.common.logger import setup_logger
from shared_libs.luminaos_common.common.error_handler import create_error_response

# 设置日志
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("MCP Gateway starting up...")
    
    # 初始化数据库连接
    try:
        if init_database():
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # 不阻止启动，但会影响数据库功能
    
    # 初始化MCP客户端
    try:
        from .tools import tool_registry
        
        # 加载MCP服务器配置并初始化客户端
        mcp_servers = settings.get_mcp_servers()
        if mcp_servers:
            initialized_count = await tool_registry.initialize_mcp_clients(mcp_servers)
            logger.info(f"Initialized {initialized_count}/{len(mcp_servers)} MCP clients")
        else:
            logger.info("No MCP servers configured")
        
        # 启动工具自动刷新任务
        if settings.AUTO_REFRESH_TOOLS:
            await tool_registry.start_auto_refresh(settings.TOOL_REFRESH_INTERVAL)
            logger.info(f"Started auto-refresh task with interval {settings.TOOL_REFRESH_INTERVAL}s")
        
        # 同步默认工具到数据库和元数据服务
        try:
            from .services.tool_service import ToolService
            from database.src.core.session import SessionLocal
            
            db = SessionLocal()
            try:
                tool_service = ToolService(db, tool_registry)
                
                # 获取所有已注册的工具
                all_tools = tool_registry.list_tools()
                logger.info(f"Found {len(all_tools)} tools in registry, syncing to database and metadata service...")
                
                synced_count = 0
                for tool_dict in all_tools:
                    tool_name = tool_dict.get("name")
                    if not tool_name:
                        continue
                    
                    try:
                        # 转换为字典格式
                        tool_def = {
                            "name": tool_name,
                            "description": tool_dict.get("description", ""),
                            "version": tool_dict.get("version", "1.0.0"),
                            "tool_type": tool_dict.get("tool_type", "function"),
                            "parameters": tool_dict.get("parameters", {}),
                            "required_parameters": tool_dict.get("required_parameters", []),
                            "returns": tool_dict.get("returns", {}),
                            "metadata": tool_dict.get("metadata", {})
                        }
                        
                        # 注册工具（会保存到数据库并同步到元数据服务）
                        result = await tool_service.register_tool(
                            tool_def,
                            overwrite=True  # 如果已存在则更新
                        )
                        
                        if result.get("success"):
                            synced_count += 1
                            logger.debug(f"Synced tool: {tool_name}")
                    except Exception as e:
                        logger.warning(f"Failed to sync tool {tool_name}: {str(e)}")
                
                logger.info(f"Successfully synced {synced_count}/{len(all_tools)} tools to database and metadata service")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to sync default tools to database/metadata: {str(e)}")
            # 不阻止启动，但会影响工具元数据功能
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP clients: {str(e)}", exc_info=True)
        # 不阻止启动，但会影响MCP工具功能
    
    logger.info("MCP Gateway startup completed")
    
    yield
    
    # 清理资源
    logger.info("MCP Gateway shutting down...")
    
    # 关闭MCP客户端
    try:
        from .tools import tool_registry
        await tool_registry.close_all_clients()
        logger.info("MCP clients closed")
    except Exception as e:
        logger.error(f"Failed to close MCP clients: {str(e)}")
    
    # 关闭数据库连接
    try:
        close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Failed to close database: {str(e)}")
    
    logger.info("MCP Gateway shutdown completed")


# 创建FastAPI应用
app = FastAPI(
    title="MCP Gateway API",
    description="""
    LuminaOS - MCP工具网关服务
    
    ## 功能特性
    
    - 🔧 **工具注册**: 动态注册MCP工具
    - 📋 **工具发现**: 查询和列出可用工具
    - ⚡ **工具执行**: 执行工具并返回结果
    - 📊 **健康检查**: 服务状态监控
    
    ## API端点
    
    ### MCP协议端点（标准MCP协议）
    - `POST /mcp` - MCP协议主端点（支持JSON-RPC 2.0和SSE格式）
    
    ### RESTful API端点（简化接口）
    - `POST /api/tools/register` - 注册新工具
    - `GET /api/tools` - 获取工具列表
    - `GET /api/tools/{name}` - 获取工具详情
    - `POST /api/tools/{name}/execute` - 执行工具
    - `DELETE /api/tools/{name}` - 注销工具
    - `GET /api/health` - 健康检查
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=[
        {
            "name": "Tools",
            "description": "MCP工具管理操作"
        },
        {
            "name": "Health",
            "description": "健康检查端点"
        }
    ]
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
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
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # 更新监控统计
    try:
        from .routes.monitoring import _update_api_stats
        _update_api_stats(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            response_time=process_time
        )
    except (ImportError, AttributeError) as e:
        # 如果导入失败，只记录日志，不阻止请求
        logger.debug(f"Failed to update API stats: {e}")
    
    return response


# 注册路由
app.include_router(health.router, prefix="/api", tags=["Health"])

# 注册MCP协议端点（标准MCP协议，支持JSON-RPC 2.0和SSE）
from .routes import mcp_protocol
app.include_router(mcp_protocol.router, tags=["MCP Protocol"])

# 注册数据库集成版本的路由
from .routes import tools_db, tool_config, tool_monitoring
app.include_router(tools_db.router, prefix="/api/tools", tags=["Tools"])
app.include_router(tool_config.router, prefix="/api", tags=["工具配置管理"])
app.include_router(tool_monitoring.router, prefix="/api", tags=["工具监控"])

# 保留原有路由（向后兼容）
app.include_router(tools.router, prefix="/api/legacy/tools", tags=["Tools (Legacy)"])

app.include_router(monitoring.router, prefix="/api", tags=["Monitoring"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "MCP Gateway",
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


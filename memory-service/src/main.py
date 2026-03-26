"""
Memory Service - 记忆服务
提供智能体的记忆和上下文管理功能
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
import sys

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_libs"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database" / "src"))

from .routes import memory, sessions, contexts
from .routes.health import router as health_router

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Memory Service",
    description="记忆服务 - 提供智能体的记忆和上下文管理功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.include_router(memory.router, prefix="/api/memory", tags=["记忆管理"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["会话管理"])
app.include_router(contexts.router, prefix="/api/contexts", tags=["上下文管理"])
app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Memory Service starting up...")
    logger.info(f"Redis Host: {os.getenv('REDIS_HOST', 'redis')}")
    logger.info(f"PostgreSQL Host: {os.getenv('POSTGRES_HOST', 'postgres')}")
    logger.info(f"Qdrant Host: {os.getenv('QDRANT_HOST', 'qdrant')}")
    logger.info("Memory Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Memory Service shutting down...")
    # 关闭连接
    from .core.context_manager import context_manager
    await context_manager.close()
    logger.info("Memory Service shutdown complete")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8013))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )





"""
Agent Registry - 智能体注册中心
提供智能体能力注册、发现和匹配等功能
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
import sys

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_libs"))

from .routes import registry, discovery, health

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Agent Registry",
    description="智能体注册中心 - 提供智能体能力注册、发现和匹配等功能",
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
app.include_router(registry.router, prefix="/api/v1/registry", tags=["注册管理"])
app.include_router(discovery.router, prefix="/api/v1/registry", tags=["发现服务"])
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Agent Registry starting up...")
    logger.info(f"Redis Host: {os.getenv('REDIS_HOST', 'redis')}")
    logger.info(f"Redis Port: {os.getenv('REDIS_PORT', '6379')}")
    logger.info("Agent Registry started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Agent Registry shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8012))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )



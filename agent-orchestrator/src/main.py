"""
Agent Orchestrator - 智能体编排服务
提供多智能体协同编排、任务分解和规划等功能
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
import sys

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_libs"))

from .routes import orchestrate, plans, health

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Agent Orchestrator",
    description="智能体编排服务 - 提供多智能体协同编排、任务分解和规划等功能",
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
app.include_router(orchestrate.router, prefix="/api/v1/orchestrate", tags=["编排管理"])
app.include_router(plans.router, prefix="/api/v1/orchestrate/plans", tags=["计划管理"])
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Agent Orchestrator starting up...")
    logger.info(f"Agent Service URL: {os.getenv('AGENT_SERVICE_URL', 'http://agent-service:8010')}")
    logger.info(f"Registry Service URL: {os.getenv('REGISTRY_SERVICE_URL', 'http://registry-service:8000')}")
    logger.info(f"Config Center URL: {os.getenv('CONFIG_CENTER_URL', 'http://config-center:8090')}")
    logger.info("Agent Orchestrator started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Agent Orchestrator shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8011))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )



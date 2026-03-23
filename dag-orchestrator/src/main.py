"""
DAG Orchestrator Service
智能任务分解与编排服务主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .routes import tasks_router, executions_router
from .routes.health import router as health_router

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="DAG Orchestrator Service",
    description="智能任务分解与编排服务",
    version="1.0.0",
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
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("DAG Orchestrator Service starting up...")
    logger.info(f"MCP Gateway URL: {os.getenv('MCP_GATEWAY_URL', 'http://mcp-gateway:8001')}")
    logger.info(f"Workflow Engine URL: {os.getenv('WORKFLOW_ENGINE_URL', 'http://workflow-engine:8002')}")
    logger.info(f"Knowledge Base URL: {os.getenv('KNOWLEDGE_BASE_URL', 'http://knowledge-base:8004')}")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("DAG Orchestrator Service shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8009))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )












































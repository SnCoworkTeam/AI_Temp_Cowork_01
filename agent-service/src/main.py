"""
Agent Service Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import agents, chat, executions, health, agent_registry, prompts, dynamic_workflow
# 延迟导入server_operation，避免启动时错误
try:
    from .routes import server_operation
    _server_operation_available = True
except (ImportError, AttributeError):
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("无法导入server_operation路由，功能将不可用")
    _server_operation_available = False
    server_operation = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Service",
    description="AIOS Agent Service API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(dynamic_workflow.router, prefix="/api/v1")
app.include_router(chat.router)
app.include_router(executions.router)
app.include_router(agent_registry.router)
# 条件注册server_operation路由
if _server_operation_available and server_operation:
    app.include_router(server_operation.router)  # 添加服务器操作智能体路由

@app.get("/")
async def root():
    return {
        "service": "agent-service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

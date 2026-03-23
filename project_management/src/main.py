"""
Project Management Service - 项目管理服务
提供项目的创建、管理、Excel导入等功能
"""

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加共享库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared_libs"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database" / "src"))

from .routes import (
    basic_data,
    critical_path,
    health,
    milestones,
    monthly_reports,
    phases,
    programs,
    project_members,
    project_plans,
    project_templates,
    projects,
    risks,
    tasks,
    todos,
    weekly_reports,
)

# plan_changes 暂时注释，因为PlanChangeLog模型未定义
# from .routes import plan_changes

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Project Management Service",
    description="项目管理服务 - 提供项目的创建、管理、Excel导入等功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(project_members.router, prefix="/api/v1", tags=["项目成员管理"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(milestones.router, prefix="/api/v1/milestones", tags=["里程碑管理"])
app.include_router(weekly_reports.router, prefix="/api/v1/weekly-reports", tags=["周报管理"])
app.include_router(monthly_reports.router, prefix="/api/v1/monthly-reports", tags=["月报管理"])
app.include_router(risks.router, prefix="/api/v1/risks", tags=["风险管理"])
app.include_router(phases.router, prefix="/api/v1/project-phases", tags=["项目阶段"])
app.include_router(basic_data.router, prefix="/api/v1/basic-data", tags=["基础数据管理"])
app.include_router(todos.router, prefix="/api/v1/todos", tags=["待办事项管理"])
app.include_router(programs.router, prefix="/api/v1/programs", tags=["项目群管理"])
app.include_router(project_plans.router, prefix="/api/v1", tags=["项目计划管理"])
app.include_router(project_templates.router, prefix="/api/v1", tags=["项目模板管理"])
app.include_router(critical_path.router, prefix="/api/v1", tags=["关键路径计算"])
# plan_changes 暂时注释，因为PlanChangeLog模型未定义
# app.include_router(plan_changes.router, prefix="/api/v1", tags=["计划变更历史"])
app.include_router(health.router, prefix="/api", tags=["健康检查"])


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Project Management Service starting up...")

    # 初始化数据库会话工厂
    try:
        from database.src.core.session import init_session_factory

        init_session_factory()
        logger.info("Database session factory initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database session factory: {e!s}", exc_info=True)

    logger.info(f"Database URL: {os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}")
    logger.info("Project Management Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("Project Management Service shutting down...")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8016))

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )

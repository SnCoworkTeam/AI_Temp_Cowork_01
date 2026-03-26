"""
部署智能体服务 - FastAPI主应用
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .agent import DeploymentCoordinatorAgent

# 配置日志
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Deployment Agent Service",
    description="部署协调智能体服务 - 自动监控代码变更并协调部署任务",
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

# 全局智能体实例
deployment_agent: Optional[DeploymentCoordinatorAgent] = None


# Pydantic模型
class DeployRequest(BaseModel):
    services: List[str] = []
    target_server: str = "app-server"
    skip_data_sync: bool = False
    skip_migration: bool = False
    include_neo4j: bool = True


class AnalyzeRequest(BaseModel):
    changed_files: List[str]


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global deployment_agent
    
    try:
        # 从环境变量读取配置
        watch_path = os.getenv("WATCH_PATH", "/workspace")
        workdir = os.getenv("WORKDIR", "/app/workdir")
        scripts_dir = os.getenv("SCRIPTS_DIR", "/workspace/scripts/deployment")
        service_map_path = os.getenv("SERVICE_MAP_PATH")
        
        # 创建智能体实例
        deployment_agent = DeploymentCoordinatorAgent(
            watch_path=watch_path,
            workdir=workdir,
            scripts_dir=scripts_dir,
            service_map_path=service_map_path
        )
        
        # 启动文件监控（在后台任务中启动，不阻塞）
        async def start_monitoring_background():
            try:
                await asyncio.sleep(1)  # 延迟1秒启动
                await deployment_agent.start_monitoring()
                logger.info("文件监控已启动")
            except Exception as e:
                logger.error(f"启动文件监控失败: {e}，服务将继续运行但不会自动监控")
        
        asyncio.create_task(start_monitoring_background())
        
        logger.info("部署协调智能体服务已启动")
        logger.info(f"监控路径: {watch_path}")
        logger.info(f"工作目录: {workdir}")
        logger.info(f"脚本目录: {scripts_dir}")
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理"""
    global deployment_agent
    
    if deployment_agent:
        await deployment_agent.stop_monitoring()
        logger.info("部署协调智能体服务已关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Deployment Agent Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    status = deployment_agent.get_status()
    return {
        "status": "healthy",
        "agent": status
    }


@app.get("/api/v1/status")
async def get_status():
    """获取智能体状态"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return deployment_agent.get_status()


@app.post("/api/v1/analyze")
async def analyze_changes(request: AnalyzeRequest):
    """分析代码变更影响"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await deployment_agent.analyze_task(
        task_description="分析代码变更",
        context={"changed_files": request.changed_files}
    )
    
    return result


@app.post("/api/v1/deploy")
async def deploy(request: DeployRequest, background_tasks: BackgroundTasks):
    """手动触发部署"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    # 如果没有指定服务，分析所有变更
    if not request.services:
        # 这里可以添加逻辑来检测所有变更的文件
        request.services = ["all"]
    
    # 执行部署（在后台任务中执行，避免阻塞）
    def execute_deployment():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                deployment_agent.execute(
                    input_data=request.dict(),
                    context={}
                )
            )
            logger.info(f"部署完成: {result}")
        except Exception as e:
            logger.error(f"部署失败: {e}")
        finally:
            loop.close()
    
    background_tasks.add_task(execute_deployment)
    
    return {
        "status": "accepted",
        "message": "部署任务已提交",
        "services": request.services
    }


@app.get("/api/v1/history")
async def get_history(limit: int = 10):
    """获取部署历史"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "history": deployment_agent.get_deployment_history(limit=limit)
    }


@app.post("/api/v1/deploy-full")
async def deploy_full(
    skip_data_sync: bool = False,
    skip_migration: bool = False,
    include_neo4j: bool = True,
    background_tasks: BackgroundTasks = None
):
    """执行完整部署（所有服务 + 数据同步 + Neo4j）"""
    if not deployment_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    request = DeployRequest(
        services=["all"],
        skip_data_sync=skip_data_sync,
        skip_migration=skip_migration,
        include_neo4j=include_neo4j
    )
    
    return await deploy(request, background_tasks or BackgroundTasks())


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )





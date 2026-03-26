"""
编排管理路由
"""
from fastapi import APIRouter, HTTPException
import logging

from ..models.task_models import OrchestrationRequest, OrchestrationResponse
from ..core.orchestrator import agent_orchestrator

router = APIRouter(tags=["编排管理"])
logger = logging.getLogger(__name__)


@router.post("/tasks", response_model=OrchestrationResponse, summary="编排复杂任务")
async def orchestrate_task(request: OrchestrationRequest):
    """
    编排复杂任务（多智能体协同）
    
    - **task**: 任务描述
    - **context**: 上下文信息
    - **strategy**: 协调策略（sequential/parallel/pipeline/adaptive）
    - **max_agents**: 最大智能体数量
    - **timeout**: 超时时间（秒）
    """
    try:
        result = await agent_orchestrator.orchestrate_agents(request)
        return OrchestrationResponse(**result)
    except Exception as e:
        logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


@router.post("/plan", summary="生成执行计划")
async def create_plan(request: OrchestrationRequest):
    """
    仅生成执行计划（不执行）
    
    用于测试和调试任务分解功能
    """
    try:
        plan = await agent_orchestrator._create_plan(request)
        return plan
    except Exception as e:
        logger.error(f"Plan creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Plan creation failed: {str(e)}")


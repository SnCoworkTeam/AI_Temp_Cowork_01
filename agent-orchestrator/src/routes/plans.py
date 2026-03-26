"""
计划管理路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.plan_models import ExecutionPlan
from ..core.orchestrator import agent_orchestrator

router = APIRouter(tags=["计划管理"])
logger = logging.getLogger(__name__)


@router.get("/{plan_id}", response_model=ExecutionPlan, summary="获取计划状态")
async def get_plan(plan_id: str):
    """
    获取计划状态
    
    - **plan_id**: 计划ID
    """
    plan = await agent_orchestrator.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    return plan


@router.get("", response_model=List[ExecutionPlan], summary="获取计划列表")
async def list_plans(limit: int = 100, offset: int = 0):
    """
    获取计划列表
    
    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        plans = await agent_orchestrator.list_plans(limit, offset)
        return plans
    except Exception as e:
        logger.error(f"Failed to list plans: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list plans: {str(e)}")


@router.post("/{plan_id}/execute", summary="执行计划")
async def execute_plan(plan_id: str):
    """
    执行计划
    
    - **plan_id**: 计划ID
    """
    plan = await agent_orchestrator.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    
    try:
        # 获取智能体选择（简化版本）
        agent_selections = await agent_orchestrator._select_agents(plan)
        
        # 执行计划
        from ..models.task_models import CoordinationStrategy
        results = await agent_orchestrator._execute_plan(
            plan,
            agent_selections,
            CoordinationStrategy.SEQUENTIAL
        )
        
        return {
            "plan_id": plan_id,
            "status": plan.status.value,
            "results": results
        }
    except Exception as e:
        logger.error(f"Plan execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Plan execution failed: {str(e)}")


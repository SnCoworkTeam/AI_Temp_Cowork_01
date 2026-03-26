"""
任务API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
import logging

from ..models.dag_models import ExecutionRequest, ExecutionResult, DAGPlan
from ..core.dag_engine import DAGEngine
from ..core.task_decomposer import TaskDecomposer

router = APIRouter(prefix="/tasks", tags=["任务管理"])
logger = logging.getLogger(__name__)

# 全局DAG引擎实例
dag_engine = DAGEngine()


@router.post("/execute", response_model=ExecutionResult, summary="执行复杂任务")
async def execute_complex_task(request: ExecutionRequest) -> ExecutionResult:
    """
    执行复杂任务（主要入口）
    
    该接口会：
    1. 使用LLM智能分解用户输入为DAG计划
    2. 执行DAG计划中的各个任务节点
    3. 聚合结果并返回
    
    - **user_input**: 用户输入的任务描述
    - **context**: 上下文信息（可选）
    - **priority**: 优先级（normal/high/low）
    """
    try:
        result = await dag_engine.execute_complex_task(request)
        return result
    except Exception as e:
        logger.error(f"Task execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/decompose", response_model=Dict[str, Any], summary="仅分解任务")
async def decompose_task_only(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    仅分解任务（返回DAG计划，不执行）
    
    用于测试和调试任务分解功能
    
    请求体格式：
    {
        "user_input": "用户输入的任务描述",
        "context": {}  // 可选
    }
    """
    try:
        user_input = request.get("user_input", "")
        context = request.get("context", {})
        
        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")
        
        decomposer = TaskDecomposer()
        dag_plan = await decomposer.decompose_task(user_input, context)
        
        # 转换为字典格式返回
        return {
            "dag_id": dag_plan.dag_id,
            "task_nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "name": node.name,
                    "description": node.description,
                    "task_type": node.task_type.value if hasattr(node.task_type, 'value') else str(node.task_type),
                    "target_service": node.target_service,
                    "action": node.action,
                    "parameters": node.parameters,
                    "dependencies": node.dependencies,
                }
                for node_id, node in dag_plan.task_nodes.items()
            },
            "entry_nodes": dag_plan.entry_nodes,
            "exit_nodes": dag_plan.exit_nodes,
            "metadata": dag_plan.metadata,
        }
    except Exception as e:
        logger.error(f"Task decomposition failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Task decomposition failed: {str(e)}"
        )


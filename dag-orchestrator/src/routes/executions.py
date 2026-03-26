"""
执行管理API路由
"""
from fastapi import APIRouter, HTTPException, Path
from typing import Optional
import logging

from ..models.dag_models import ExecutionResult
from ..core.dag_engine import DAGEngine

router = APIRouter(prefix="/executions", tags=["执行管理"])
logger = logging.getLogger(__name__)

# 全局DAG引擎实例
dag_engine = DAGEngine()


@router.get(
    "/{execution_id}",
    response_model=ExecutionResult,
    summary="获取执行状态"
)
async def get_execution_status(
    execution_id: str = Path(..., description="执行ID")
) -> ExecutionResult:
    """
    获取执行状态
    
    - **execution_id**: 执行ID
    """
    execution = dag_engine.get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{execution_id}' not found"
        )
    
    return execution












































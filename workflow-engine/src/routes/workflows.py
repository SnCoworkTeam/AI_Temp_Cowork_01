"""
工作流路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from ..models.workflow_models import WorkflowExecutionRequest, WorkflowExecutionResponse
from ..workflows import workflow_manager

router = APIRouter()


# 注意：list_workflows 端点已迁移到 workflow_designer.router
# 这里保留是为了向后兼容，但实际应该使用 /api/v1/workflows (workflow_designer版本)
# @router.get("", summary="获取工作流列表")
# async def list_workflows() -> List[Dict[str, Any]]:
#     """
#     获取所有可用的工作流定义
#     """
#     return await workflow_manager.list_workflows()


@router.post("/execute", summary="执行工作流")
async def execute_workflow(request: WorkflowExecutionRequest) -> WorkflowExecutionResponse:
    """
    执行指定的工作流
    """
    try:
        result = await workflow_manager.execute_workflow(
            workflow_name=request.workflow_name,
            input_data=request.input_data,
            context=request.context or {}
        )
        return WorkflowExecutionResponse(
            success=True,
            execution_id=result.get("execution_id"),
            result=result.get("result"),
            workflow_name=request.workflow_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/{workflow_name}", summary="获取工作流详情")
async def get_workflow_info(workflow_name: str) -> Dict[str, Any]:
    """
    获取指定工作流的详细信息
    """
    workflow_info = workflow_manager.get_workflow_info(workflow_name)
    if not workflow_info:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")
    return workflow_info


@router.get("/executions/{execution_id}", summary="获取执行状态")
async def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    获取工作流执行状态
    """
    status = workflow_manager.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return status










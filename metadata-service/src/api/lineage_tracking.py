"""
血缘追踪API路由
接收来自各个服务的血缘追踪请求
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ..collectors.lineage_collector import (
    LineageCollector,
    NodeExecution,
    ProcessingStep,
    get_lineage_collector
)
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


class ToolExecutionLineageRequest(BaseModel):
    """工具执行血缘请求"""
    tool_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_id: Optional[str] = None
    execution_time: Optional[float] = None


class WorkflowExecutionLineageRequest(BaseModel):
    """工作流执行血缘请求"""
    workflow_id: str
    execution_id: Optional[str] = None
    node_executions: List[Dict[str, Any]]


class KnowledgeProcessingLineageRequest(BaseModel):
    """知识处理血缘请求"""
    document_id: str
    processing_id: Optional[str] = None
    processing_steps: List[Dict[str, Any]]


class ModelInferenceLineageRequest(BaseModel):
    """模型推理血缘请求"""
    model_id: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    inference_id: Optional[str] = None
    inference_time: Optional[float] = None


@router.post(
    "/collection/lineage/tool-execution",
    summary="追踪MCP工具执行血缘",
    tags=["Lineage Tracking"]
)
async def track_tool_execution(
    request: ToolExecutionLineageRequest = Body(...)
):
    """追踪MCP工具执行血缘"""
    try:
        collector = get_lineage_collector()
        result = await collector.track_mcp_tool_execution(
            tool_name=request.tool_name,
            input_data=request.input_data,
            output_data=request.output_data,
            execution_id=request.execution_id,
            execution_time=request.execution_time
        )
        return {
            "success": result,
            "message": f"Tool execution lineage tracked for {request.tool_name}"
        }
    except Exception as e:
        logger.error(f"Failed to track tool execution lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/lineage/workflow-execution",
    summary="追踪工作流执行血缘",
    tags=["Lineage Tracking"]
)
async def track_workflow_execution(
    request: WorkflowExecutionLineageRequest = Body(...)
):
    """追踪工作流执行血缘"""
    try:
        collector = get_lineage_collector()
        
        # 转换节点执行数据
        node_executions = []
        for node_data in request.node_executions:
            node_exec = NodeExecution(
                node_id=node_data["node_id"],
                node_type=node_data.get("node_type", "unknown"),
                input_data=node_data.get("input_data", {}),
                output_data=node_data.get("output_data", {}),
                execution_time=node_data.get("execution_time"),
                success=node_data.get("success", True)
            )
            node_executions.append(node_exec)
        
        result = await collector.track_workflow_execution(
            workflow_id=request.workflow_id,
            node_executions=node_executions,
            execution_id=request.execution_id
        )
        return {
            "success": result,
            "message": f"Workflow execution lineage tracked for {request.workflow_id}"
        }
    except Exception as e:
        logger.error(f"Failed to track workflow execution lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/lineage/knowledge-processing",
    summary="追踪知识处理血缘",
    tags=["Lineage Tracking"]
)
async def track_knowledge_processing(
    request: KnowledgeProcessingLineageRequest = Body(...)
):
    """追踪知识处理血缘"""
    try:
        collector = get_lineage_collector()
        
        # 转换处理步骤数据
        processing_steps = []
        for step_data in request.processing_steps:
            step = ProcessingStep(
                step_name=step_data["step_name"],
                step_type=step_data.get("step_type", "unknown"),
                input_data=step_data.get("input_data", {}),
                output_data=step_data.get("output_data", {}),
                processing_time=step_data.get("processing_time")
            )
            processing_steps.append(step)
        
        result = await collector.track_knowledge_processing(
            document_id=request.document_id,
            processing_steps=processing_steps,
            processing_id=request.processing_id
        )
        return {
            "success": result,
            "message": f"Knowledge processing lineage tracked for document {request.document_id}"
        }
    except Exception as e:
        logger.error(f"Failed to track knowledge processing lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/lineage/model-inference",
    summary="追踪模型推理血缘",
    tags=["Lineage Tracking"]
)
async def track_model_inference(
    request: ModelInferenceLineageRequest = Body(...)
):
    """追踪模型推理血缘"""
    try:
        collector = get_lineage_collector()
        result = await collector.track_model_inference(
            model_id=request.model_id,
            input_data=request.input_data,
            output_data=request.output_data,
            inference_id=request.inference_id,
            inference_time=request.inference_time
        )
        return {
            "success": result,
            "message": f"Model inference lineage tracked for {request.model_id}"
        }
    except Exception as e:
        logger.error(f"Failed to track model inference lineage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


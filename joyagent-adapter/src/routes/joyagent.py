"""
JoyAgent Adapter API Routes

FastAPI routes for JoyAgent integration with the enterprise platform.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional, Dict, Any
import structlog

from ..models import (
    JoyAgentTaskRequest,
    JoyAgentTaskResponse,
    JoyAgentTaskList,
    JoyAgentStatus,
    WorkflowIntegrationRequest,
    KnowledgeEnhancementRequest,
    MCPToolIntegrationRequest,
    HealthCheckResponse,
    ErrorResponse
)
from ..services.joyagent_service import joyagent_service
from ..integrations.platform_integration import platform_integrator

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/tasks",
    response_model=JoyAgentTaskResponse,
    status_code=201,
    summary="创建JoyAgent任务",
    description="创建新的JoyAgent任务，支持多种任务类型",
    responses={
        201: {"description": "任务创建成功", "model": JoyAgentTaskResponse},
        400: {"description": "请求参数错误", "model": ErrorResponse},
        503: {"description": "JoyAgent服务不可用", "model": ErrorResponse}
    }
)
async def create_joyagent_task(
    task_request: JoyAgentTaskRequest
) -> JoyAgentTaskResponse:
    """
    创建JoyAgent任务

    支持的任务类型:
    - **query**: 自然语言查询
    - **report_generation**: 报告生成
    - **code_generation**: 代码生成
    - **ppt_generation**: PPT生成
    - **data_analysis**: 数据分析
    - **document_processing**: 文档处理
    - **workflow_execution**: 工作流执行
    """
    try:
        task_response = await joyagent_service.create_task(task_request)
        logger.info(f"Created JoyAgent task: {task_response.task_id}")
        return task_response

    except Exception as e:
        logger.error(f"Failed to create JoyAgent task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get(
    "/tasks/{task_id}",
    response_model=JoyAgentTaskResponse,
    summary="获取任务状态",
    description="获取指定任务的执行状态和结果",
    responses={
        200: {"description": "任务状态", "model": JoyAgentTaskResponse},
        404: {"description": "任务不存在", "model": ErrorResponse}
    }
)
async def get_task_status(
    task_id: str = Path(..., description="任务ID")
) -> JoyAgentTaskResponse:
    """
    获取任务状态和结果

    - **task_id**: 任务标识符
    """
    try:
        return await joyagent_service.get_task_status(task_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/tasks",
    response_model=JoyAgentTaskList,
    summary="获取任务列表",
    description="获取所有任务的列表，支持分页",
    responses={
        200: {"description": "任务列表", "model": JoyAgentTaskList}
    }
)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小")
) -> JoyAgentTaskList:
    """
    获取任务列表

    - **page**: 页码（从1开始）
    - **page_size**: 每页大小（1-100）
    """
    try:
        result = await joyagent_service.list_tasks(page=page, page_size=page_size)
        return JoyAgentTaskList(**result)

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="取消任务",
    description="取消正在执行的任务",
    responses={
        204: {"description": "任务已取消"},
        404: {"description": "任务不存在", "model": ErrorResponse},
        400: {"description": "任务已完成，无法取消", "model": ErrorResponse}
    }
)
async def cancel_task(
    task_id: str = Path(..., description="任务ID")
):
    """
    取消任务

    - **task_id**: 任务标识符
    """
    try:
        await joyagent_service.cancel_task(task_id)
        logger.info(f"Cancelled JoyAgent task: {task_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.get(
    "/status",
    response_model=JoyAgentStatus,
    summary="获取服务状态",
    description="获取JoyAgent服务状态和能力",
    responses={
        200: {"description": "服务状态", "model": JoyAgentStatus}
    }
)
async def get_service_status() -> JoyAgentStatus:
    """
    获取JoyAgent服务状态

    包括:
    - 服务健康状态
    - 活跃任务数量
    - 可用能力列表
    - 版本信息
    """
    try:
        return await joyagent_service.get_service_status()

    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.post(
    "/integrations/workflow",
    response_model=JoyAgentTaskResponse,
    summary="工作流集成",
    description="将JoyAgent任务集成到工作流步骤中",
    responses={
        201: {"description": "工作流任务创建成功", "model": JoyAgentTaskResponse},
        400: {"description": "请求参数错误", "model": ErrorResponse}
    }
)
async def create_workflow_integration_task(
    request: WorkflowIntegrationRequest
) -> JoyAgentTaskResponse:
    """
    工作流集成

    将JoyAgent任务作为工作流的一个步骤执行，支持:
    - 工作流上下文传递
    - 结果回调
    - 状态同步
    """
    try:
        # Add workflow context to JoyAgent task
        enhanced_task = await platform_integrator.enhance_task_with_workflow_context(
            request.joyagent_task,
            request.integration_context
        )

        task_response = await joyagent_service.create_task(enhanced_task)

        # Register workflow callback if provided
        if request.callback_url:
            await platform_integrator.register_workflow_callback(
                task_response.task_id,
                request.callback_url,
                request.workflow_id,
                request.step_name
            )

        logger.info(f"Created workflow integration task: {task_response.task_id} for workflow: {request.workflow_id}")
        return task_response

    except Exception as e:
        logger.error(f"Failed to create workflow integration task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workflow integration task: {str(e)}"
        )


@router.post(
    "/integrations/knowledge",
    response_model=JoyAgentTaskResponse,
    summary="知识增强集成",
    description="使用JoyAgent增强知识库查询和分析",
    responses={
        201: {"description": "知识增强任务创建成功", "model": JoyAgentTaskResponse},
        400: {"description": "请求参数错误", "model": ErrorResponse}
    }
)
async def create_knowledge_enhancement_task(
    request: KnowledgeEnhancementRequest
) -> JoyAgentTaskResponse:
    """
    知识增强集成

    使用JoyAgent的分析能力增强知识库:
    - 智能文档摘要
    - 知识点提取
    - 关联分析
    - 趋势洞察
    """
    try:
        # Convert to JoyAgent task
        enhanced_task = await platform_integrator.create_knowledge_enhancement_task(request)
        task_response = await joyagent_service.create_task(enhanced_task)

        logger.info(f"Created knowledge enhancement task: {task_response.task_id}")
        return task_response

    except Exception as e:
        logger.error(f"Failed to create knowledge enhancement task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create knowledge enhancement task: {str(e)}"
        )


@router.post(
    "/integrations/mcp",
    response_model=JoyAgentTaskResponse,
    summary="MCP工具集成",
    description="集成MCP工具与JoyAgent协同工作",
    responses={
        201: {"description": "MCP集成任务创建成功", "model": JoyAgentTaskResponse},
        400: {"description": "请求参数错误", "model": ErrorResponse}
    }
)
async def create_mcp_integration_task(
    request: MCPToolIntegrationRequest
) -> JoyAgentTaskResponse:
    """
    MCP工具集成

    将MCP工具与JoyAgent结合:
    - 工具调用协调
    - 结果分析增强
    - 多工具组合任务
    """
    try:
        # Convert to JoyAgent task with MCP tool context
        enhanced_task = await platform_integrator.create_mcp_integration_task(request)
        task_response = await joyagent_service.create_task(enhanced_task)

        logger.info(f"Created MCP integration task: {task_response.task_id} for tool: {request.tool_name}")
        return task_response

    except Exception as e:
        logger.error(f"Failed to create MCP integration task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create MCP integration task: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="检查JoyAgent适配器服务健康状态"
)
async def health_check() -> HealthCheckResponse:
    """
    健康检查端点

    检查:
    - JoyAgent服务连接
    - Redis连接
    - 平台服务状态
    """
    try:
        from datetime import datetime
        from ..config import settings

        # Check JoyAgent service
        await joyagent_service._health_check()

        # Check platform integrations
        platform_status = await platform_integrator.check_platform_health()

        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0",
            dependencies={
                "joyagent_backend": "healthy",
                "redis": "healthy",
                "platform_services": "healthy" if platform_status else "degraded"
            },
            metrics={
                "active_tasks": len(joyagent_service.active_tasks),
                "service_port": settings.service_port,
                "uptime_seconds": 0  # TODO: Calculate actual uptime
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        from datetime import datetime

        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0",
            dependencies={
                "joyagent_backend": "unhealthy",
                "redis": "unknown",
                "platform_services": "unknown"
            }
        )
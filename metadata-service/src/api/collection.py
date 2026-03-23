"""
元数据采集API路由
提供手动触发采集和查看采集状态的端点
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..collectors.collection_manager import get_collection_manager
from ..core.database import get_db
from luminaos_common.common.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post(
    "/collection/startup",
    summary="服务启动时注册基础元数据",
    tags=["Collection"]
)
async def register_on_startup(
    background_tasks: BackgroundTasks
):
    """服务启动时：注册基础元数据"""
    try:
        collection_manager = get_collection_manager()
        # 在后台执行，不阻塞请求
        background_tasks.add_task(collection_manager.register_on_startup)
        return {
            "success": True,
            "message": "Metadata registration started in background"
        }
    except Exception as e:
        logger.error(f"Failed to start metadata registration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/data-change",
    summary="数据变更时更新元数据",
    tags=["Collection"]
)
async def update_on_data_change(
    entity_type: str,
    entity_id: str,
    change_type: str = "update"
):
    """数据变更时：更新元数据版本"""
    try:
        collection_manager = get_collection_manager()
        success = await collection_manager.update_on_data_change(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type
        )
        return {
            "success": success,
            "message": f"Metadata updated for {entity_type}:{entity_id}"
        }
    except Exception as e:
        logger.error(f"Failed to update metadata on data change: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/tool-usage",
    summary="工具执行时收集使用统计",
    tags=["Collection"]
)
async def collect_tool_usage(
    tool_name: str,
    execution_time: float,
    success: bool
):
    """工具执行时：收集使用统计"""
    try:
        collection_manager = get_collection_manager()
        result = await collection_manager.collect_tool_usage_statistics(
            tool_name=tool_name,
            execution_time=execution_time,
            success=success
        )
        return {
            "success": result,
            "message": f"Tool usage statistics collected for {tool_name}"
        }
    except Exception as e:
        logger.error(f"Failed to collect tool usage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/workflow-execution",
    summary="工作流运行时收集执行指标",
    tags=["Collection"]
)
async def collect_workflow_execution(
    workflow_id: str,
    execution_time: float,
    success: bool,
    input_size: Optional[int] = None,
    output_size: Optional[int] = None
):
    """工作流运行时：收集执行指标"""
    try:
        collection_manager = get_collection_manager()
        result = await collection_manager.collect_workflow_execution_metrics(
            workflow_id=workflow_id,
            execution_time=execution_time,
            success=success,
            input_size=input_size,
            output_size=output_size
        )
        return {
            "success": result,
            "message": f"Workflow execution metrics collected for {workflow_id}"
        }
    except Exception as e:
        logger.error(f"Failed to collect workflow execution metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/user-access",
    summary="用户交互时收集访问模式",
    tags=["Collection"]
)
async def collect_user_access(
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    action: str = "access",
    metadata: Optional[Dict[str, Any]] = None
):
    """用户交互时：收集访问模式"""
    try:
        collection_manager = get_collection_manager()
        result = await collection_manager.collect_user_access_pattern(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            metadata=metadata
        )
        return {
            "success": result,
            "message": f"User access pattern collected for {entity_type}:{entity_id}"
        }
    except Exception as e:
        logger.error(f"Failed to collect user access pattern: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/collection/sync-all",
    summary="同步所有元数据",
    tags=["Collection"]
)
async def sync_all_metadata(
    background_tasks: BackgroundTasks
):
    """手动触发：同步所有元数据"""
    try:
        collection_manager = get_collection_manager()
        # 在后台执行
        background_tasks.add_task(collection_manager.register_on_startup)
        return {
            "success": True,
            "message": "Full metadata sync started in background"
        }
    except Exception as e:
        logger.error(f"Failed to start full sync: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


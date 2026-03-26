"""
工具监控和审计API路由
提供性能指标、告警、执行历史等功能
"""
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from typing import Dict, Any, Optional
from datetime import datetime

from ..services.tool_service import ToolService
from ..core.monitoring import ToolMonitor
from ..dependencies.database import get_db
from shared_libs.luminaos_common.common.logger import setup_logger
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tools", tags=["工具监控"])
logger = setup_logger(__name__)


def get_tool_service(db: Session = Depends(get_db)) -> ToolService:
    """获取工具服务"""
    from ..tools.tool_registry import ToolRegistry
    from ..tools import tool_registry  # 使用全局单例实例
    return ToolService(db, tool_registry=tool_registry)


def get_tool_monitor(db: Session = Depends(get_db)) -> ToolMonitor:
    """获取工具监控器"""
    return ToolMonitor(db)


@router.get(
    "/{tool_name}/metrics",
    summary="获取工具性能指标",
    description="获取工具的详细性能指标和统计信息",
    responses={
        200: {"description": "性能指标"},
        404: {"description": "工具不存在"}
    }
)
async def get_tool_metrics(
    tool_name: str = Path(..., description="工具名称"),
    start_date: Optional[str] = Query(None, description="开始日期（ISO格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（ISO格式）"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工具性能指标"""
    try:
        monitor = get_tool_monitor(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        metrics = monitor.get_tool_metrics(
            tool_id=str(tool.id),
            start_date=start_dt,
            end_date=end_dt
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool metrics: {str(e)}"
        )


@router.get(
    "/{tool_name}/alerts",
    summary="获取工具告警",
    description="检查工具的告警状态",
    responses={
        200: {"description": "告警列表"},
        404: {"description": "工具不存在"}
    }
)
async def get_tool_alerts(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工具告警"""
    try:
        monitor = get_tool_monitor(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        alerts = monitor.check_alerts(str(tool.id))
        
        return {
            "tool_id": str(tool.id),
            "tool_name": tool_name,
            "alerts": alerts,
            "total": len(alerts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool alerts: {str(e)}"
        )


@router.get(
    "/{tool_name}/executions",
    summary="获取工具执行历史",
    description="获取工具的执行历史记录",
    responses={
        200: {"description": "执行历史"}
    }
)
async def get_tool_executions(
    tool_name: str = Path(..., description="工具名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页大小"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取工具执行历史"""
    try:
        service = get_tool_service(db)
        
        from ..repositories.tool_repository import ToolRepository
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        history = await service.get_execution_history(
            tool_id=str(tool.id),
            page=page,
            page_size=page_size
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool executions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool executions: {str(e)}"
        )


@router.get(
    "/{tool_name}/rate-limit",
    summary="获取频率限制信息",
    description="获取工具的频率限制配置和使用情况",
    responses={
        200: {"description": "频率限制信息"},
        404: {"description": "工具不存在"}
    }
)
async def get_rate_limit_info(
    tool_name: str = Path(..., description="工具名称"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取频率限制信息"""
    try:
        from ..repositories.tool_repository import ToolRepository
        from ..core.rate_limiter import RateLimiter
        
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_by_name(tool_name)
        
        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        rate_limiter = RateLimiter(db)
        rate_limit_info = rate_limiter.get_rate_limit_info(str(tool.id))
        
        return {
            "tool_id": str(tool.id),
            "tool_name": tool_name,
            **rate_limit_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rate limit info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting rate limit info: {str(e)}"
        )


@router.get(
    "/monitoring/system",
    summary="获取系统监控指标",
    description="获取MCP网关的系统级监控指标",
    responses={
        200: {"description": "系统监控指标"}
    }
)
async def get_system_metrics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取系统监控指标"""
    try:
        monitor = get_tool_monitor(db)
        metrics = monitor.get_system_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system metrics: {str(e)}"
        )










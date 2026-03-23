"""
Workflow Engine 监控路由
提供工作流引擎监控和统计数据
"""
from fastapi import APIRouter, Request
from datetime import datetime
from typing import Dict, Any, List, Optional
import time
import psutil

from shared_libs.luminaos_common.schemas.monitoring_schemas import (
    ServiceMonitoringData,
    ServiceHealth,
    ServiceStatus,
    APIStatistics,
    WorkflowExecutionStats,
    SystemResourceUsage,
    Metric,
    MetricType,
    MetricPoint,
    Alert,
    AlertLevel
)
from ..workflows import workflow_manager
from ..config import settings

router = APIRouter()

# 内存中的统计数据
_api_stats: Dict[str, Dict[str, Any]] = {}
_workflow_execution_stats: Dict[str, Dict[str, Any]] = {}
_start_time = time.time()


def _get_api_key(method: str, path: str) -> str:
    """生成API键"""
    return f"{method}:{path}"


def _update_api_stats(method: str, path: str, status_code: int, response_time: float):
    """更新API统计"""
    key = _get_api_key(method, path)
    
    if key not in _api_stats:
        _api_stats[key] = {
            "endpoint": path,
            "method": method,
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "response_times": []
        }
    
    stats = _api_stats[key]
    stats["total_requests"] += 1
    
    if 200 <= status_code < 400:
        stats["success_count"] += 1
    else:
        stats["error_count"] += 1
    
    stats["response_times"].append(response_time)
    
    if len(stats["response_times"]) > 1000:
        stats["response_times"] = stats["response_times"][-1000:]


def _update_workflow_execution_stats(
    workflow_id: str,
    workflow_name: str,
    success: bool,
    execution_time: float
):
    """更新工作流执行统计"""
    if workflow_id not in _workflow_execution_stats:
        _workflow_execution_stats[workflow_id] = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "total_executions": 0,
            "success_count": 0,
            "failed_count": 0,
            "running_count": 0,
            "execution_times": [],
            "total_execution_time": 0.0
        }
    
    stats = _workflow_execution_stats[workflow_id]
    stats["total_executions"] += 1
    
    if success:
        stats["success_count"] += 1
    else:
        stats["failed_count"] += 1
    
    stats["execution_times"].append(execution_time)
    stats["total_execution_time"] += execution_time
    
    if len(stats["execution_times"]) > 1000:
        stats["execution_times"] = stats["execution_times"][-1000:]


def _calculate_percentiles(values: List[float], percentile: float) -> float:
    """计算百分位数"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


@router.get(
    "/monitoring",
    response_model=ServiceMonitoringData,
    summary="获取服务监控数据",
    description="返回Workflow Engine的监控数据，包括健康状态、工作流执行统计、API统计等",
    tags=["Monitoring"]
)
async def get_monitoring_data() -> ServiceMonitoringData:
    """
    获取服务监控数据
    """
    # 计算运行时间
    uptime = time.time() - _start_time
    
    # 获取工作流统计
    try:
        workflows = await workflow_manager.list_workflows(page=1, page_size=1000)
        total_workflows = len(workflows)
    except Exception:
        total_workflows = 0
    
    # 健康状态
    health = ServiceHealth(
        service_name="workflow-engine",
        status=ServiceStatus.HEALTHY,
        version="1.0.0",
        uptime=uptime,
        last_check=datetime.now(),
        checks={
            "total_workflows": total_workflows,
            "workflow_manager_initialized": True
        }
    )
    
    # API统计
    api_statistics = []
    for key, stats in _api_stats.items():
        response_times = stats.get("response_times", [])
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            p95_time = _calculate_percentiles(response_times, 95)
            p99_time = _calculate_percentiles(response_times, 99)
        else:
            avg_time = min_time = max_time = p95_time = p99_time = 0.0
        
        api_statistics.append(APIStatistics(
            endpoint=stats["endpoint"],
            method=stats["method"],
            total_requests=stats["total_requests"],
            success_count=stats["success_count"],
            error_count=stats["error_count"],
            avg_response_time=avg_time * 1000,
            min_response_time=min_time * 1000,
            max_response_time=max_time * 1000,
            p95_response_time=p95_time * 1000,
            p99_response_time=p99_time * 1000
        ))
    
    # 工作流执行统计
    workflow_stats = []
    for workflow_id, stats in _workflow_execution_stats.items():
        execution_times = stats.get("execution_times", [])
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        workflow_stats.append(WorkflowExecutionStats(
            workflow_id=stats["workflow_id"],
            workflow_name=stats["workflow_name"],
            total_executions=stats["total_executions"],
            success_count=stats["success_count"],
            failed_count=stats["failed_count"],
            running_count=stats["running_count"],
            avg_execution_time=avg_execution_time,
            total_execution_time=stats["total_execution_time"]
        ))
    
    # 系统资源使用
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        resource_usage = SystemResourceUsage(
            cpu_percent=cpu_percent,
            memory_used=memory.used,
            memory_total=memory.total,
            memory_percent=memory.percent,
            disk_used=disk.used,
            disk_total=disk.total,
            disk_percent=(disk.used / disk.total * 100) if disk.total > 0 else 0,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv
        )
    except Exception:
        resource_usage = SystemResourceUsage()
    
    # 指标
    metrics = [
        Metric(
            name="workflow_count",
            metric_type=MetricType.GAUGE,
            description="工作流总数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(total_workflows),
                    labels={"service": "workflow-engine"}
                )
            ]
        ),
        Metric(
            name="total_workflow_executions",
            metric_type=MetricType.COUNTER,
            description="总工作流执行次数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(sum(s["total_executions"] for s in _workflow_execution_stats.values())),
                    labels={"service": "workflow-engine"}
                )
            ]
        )
    ]
    
    # 告警
    alerts = []
    if resource_usage.cpu_percent > 80:
        alerts.append(Alert(
            id=f"cpu_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="CPU使用率过高",
            message=f"CPU使用率达到 {resource_usage.cpu_percent:.1f}%",
            service="workflow-engine",
            created_at=datetime.now(),
            metadata={"cpu_percent": resource_usage.cpu_percent}
        ))
    
    if resource_usage.memory_percent > 80:
        alerts.append(Alert(
            id=f"memory_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="内存使用率过高",
            message=f"内存使用率达到 {resource_usage.memory_percent:.1f}%",
            service="workflow-engine",
            created_at=datetime.now(),
            metadata={"memory_percent": resource_usage.memory_percent}
        ))
    
    # 注意：这里我们需要将 workflow_stats 转换为 API 可接受的格式
    # 由于 ServiceMonitoringData 没有 workflow_execution_stats 字段，我们将其放在 metadata 中
    return ServiceMonitoringData(
        service_name="workflow-engine",
        health=health,
        api_statistics=api_statistics,
        metrics=metrics,
        resource_usage=resource_usage,
        alerts=alerts,
        last_updated=datetime.now()
    )


@router.get(
    "/monitoring/workflow-stats",
    summary="获取工作流执行统计",
    description="返回工作流执行统计信息",
    tags=["Monitoring"]
)
async def get_workflow_execution_stats() -> Dict[str, Any]:
    """获取工作流执行统计"""
    workflow_stats = []
    for workflow_id, stats in _workflow_execution_stats.items():
        execution_times = stats.get("execution_times", [])
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        workflow_stats.append({
            "workflow_id": stats["workflow_id"],
            "workflow_name": stats["workflow_name"],
            "total_executions": stats["total_executions"],
            "success_count": stats["success_count"],
            "failed_count": stats["failed_count"],
            "running_count": stats["running_count"],
            "avg_execution_time": avg_execution_time,
            "total_execution_time": stats["total_execution_time"]
        })
    
    return {
        "workflow_execution_stats": workflow_stats,
        "timestamp": datetime.now().isoformat()
    }


# 中间件函数
async def monitoring_middleware(request: Request, call_next):
    """监控中间件，记录请求统计"""
    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time
    
    _update_api_stats(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        response_time=response_time
    )
    
    return response








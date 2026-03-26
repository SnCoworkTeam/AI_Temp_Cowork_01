"""
MCP Gateway 监控路由
提供服务监控和统计数据
"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import psutil
import sys
import os

# 修复shared_libs导入路径
if '/shared_libs' not in sys.path:
    sys.path.insert(0, '/shared_libs')

from shared_libs.luminaos_common.schemas.monitoring_schemas import (
    ServiceMonitoringData,
    ServiceHealth,
    ServiceStatus,
    APIStatistics,
    SystemResourceUsage,
    Metric,
    MetricType,
    MetricPoint,
    Alert,
    AlertLevel
)
from ..tools import tool_registry
from ..config import settings

router = APIRouter()

# 内存中的统计数据（生产环境应使用Redis或其他持久化存储）
_api_stats: Dict[str, Dict[str, Any]] = {}
_request_times: Dict[str, List[float]] = {}
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
    
    # 只保留最近1000个响应时间
    if len(stats["response_times"]) > 1000:
        stats["response_times"] = stats["response_times"][-1000:]


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
    description="返回MCP Gateway的监控数据，包括健康状态、API统计、资源使用等",
    tags=["Monitoring"]
)
async def get_monitoring_data() -> ServiceMonitoringData:
    """
    获取服务监控数据
    """
    # 计算运行时间
    uptime = time.time() - _start_time
    
    # 健康状态
    health = ServiceHealth(
        service_name="mcp-gateway",
        status=ServiceStatus.HEALTHY,
        version="1.0.0",
        uptime=uptime,
        last_check=datetime.now(),
        checks={
            "tools_registry": tool_registry.get_tool_count() > 0,
            "total_tools": tool_registry.get_tool_count(),
            "active_tools": tool_registry.get_active_tool_count()
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
            avg_response_time=avg_time * 1000,  # 转换为毫秒
            min_response_time=min_time * 1000,
            max_response_time=max_time * 1000,
            p95_response_time=p95_time * 1000,
            p99_response_time=p99_time * 1000
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
    except Exception as e:
        # 如果无法获取系统资源，返回默认值
        resource_usage = SystemResourceUsage()
    
    # 指标
    metrics = [
        Metric(
            name="tool_count",
            metric_type=MetricType.GAUGE,
            description="已注册工具数量",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(tool_registry.get_tool_count()),
                    labels={"service": "mcp-gateway"}
                )
            ]
        ),
        Metric(
            name="active_tool_count",
            metric_type=MetricType.GAUGE,
            description="活跃工具数量",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(tool_registry.get_active_tool_count()),
                    labels={"service": "mcp-gateway"}
                )
            ]
        ),
        Metric(
            name="total_api_requests",
            metric_type=MetricType.COUNTER,
            description="总API请求数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(sum(s["total_requests"] for s in _api_stats.values())),
                    labels={"service": "mcp-gateway"}
                )
            ]
        )
    ]
    
    # 告警（示例）
    alerts = []
    if resource_usage.cpu_percent > 80:
        alerts.append(Alert(
            id=f"cpu_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="CPU使用率过高",
            message=f"CPU使用率达到 {resource_usage.cpu_percent:.1f}%",
            service="mcp-gateway",
            created_at=datetime.now(),
            metadata={"cpu_percent": resource_usage.cpu_percent}
        ))
    
    if resource_usage.memory_percent > 80:
        alerts.append(Alert(
            id=f"memory_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="内存使用率过高",
            message=f"内存使用率达到 {resource_usage.memory_percent:.1f}%",
            service="mcp-gateway",
            created_at=datetime.now(),
            metadata={"memory_percent": resource_usage.memory_percent}
        ))
    
    return ServiceMonitoringData(
        service_name="mcp-gateway",
        health=health,
        api_statistics=api_statistics,
        metrics=metrics,
        resource_usage=resource_usage,
        alerts=alerts,
        last_updated=datetime.now()
    )


@router.get(
    "/monitoring/stats",
    summary="获取API统计",
    description="返回API调用统计信息",
    tags=["Monitoring"]
)
async def get_api_stats() -> Dict[str, Any]:
    """获取API统计"""
    return {
        "api_statistics": [
            {
                "endpoint": stats["endpoint"],
                "method": stats["method"],
                "total_requests": stats["total_requests"],
                "success_count": stats["success_count"],
                "error_count": stats["error_count"]
            }
            for stats in _api_stats.values()
        ],
        "timestamp": datetime.now().isoformat()
    }


# 中间件函数（需要在主应用中注册）
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



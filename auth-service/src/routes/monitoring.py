"""
Auth Service 监控路由
提供认证服务监控和统计数据
"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import psutil

from shared_libs.luminaos_common.schemas.monitoring_schemas import (
    ServiceMonitoringData,
    ServiceHealth,
    ServiceStatus,
    APIStatistics,
    UserActivityStats,
    SystemResourceUsage,
    Metric,
    MetricType,
    MetricPoint,
    Alert,
    AlertLevel
)
from ..sso.cache_manager import cache_manager
from ..config import settings

router = APIRouter()

# 内存中的统计数据
_api_stats: Dict[str, Dict[str, Any]] = {}
_user_activity: Dict[str, Dict[str, Any]] = {}
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


def _update_user_activity(user_id: str, username: str, action: str):
    """更新用户活跃度"""
    if user_id not in _user_activity:
        _user_activity[user_id] = {
            "user_id": user_id,
            "username": username,
            "active_sessions": 0,
            "total_requests": 0,
            "last_activity": datetime.now(),
            "login_count": 0,
            "actions": {}
        }
    
    stats = _user_activity[user_id]
    stats["total_requests"] += 1
    stats["last_activity"] = datetime.now()
    
    if action == "login":
        stats["login_count"] += 1
        stats["active_sessions"] = max(1, stats["active_sessions"])
    elif action == "logout":
        stats["active_sessions"] = max(0, stats["active_sessions"] - 1)
    elif action == "session_created":
        stats["active_sessions"] += 1
    
    if action not in stats["actions"]:
        stats["actions"][action] = 0
    stats["actions"][action] += 1


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
    description="返回Auth Service的监控数据，包括健康状态、用户活跃度、API统计等",
    tags=["Monitoring"]
)
async def get_monitoring_data() -> ServiceMonitoringData:
    """
    获取服务监控数据
    """
    # 计算运行时间
    uptime = time.time() - _start_time
    
    # 检查Redis连接状态
    redis_connected = False
    try:
        if cache_manager._redis:
            await cache_manager._redis.ping()
            redis_connected = True
    except Exception:
        pass
    
    # 获取用户统计
    try:
        # 这里应该从实际的数据源获取，现在使用缓存中的数据
        total_users = len(_user_activity)
        active_users = sum(1 for u in _user_activity.values() if u["active_sessions"] > 0)
    except Exception:
        total_users = 0
        active_users = 0
    
    # 健康状态
    health = ServiceHealth(
        service_name="auth-service",
        status=ServiceStatus.HEALTHY if redis_connected else ServiceStatus.DEGRADED,
        version="1.0.0",
        uptime=uptime,
        last_check=datetime.now(),
        checks={
            "redis_connected": redis_connected,
            "total_users": total_users,
            "active_users": active_users
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
            name="total_users",
            metric_type=MetricType.GAUGE,
            description="总用户数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(total_users),
                    labels={"service": "auth-service"}
                )
            ]
        ),
        Metric(
            name="active_users",
            metric_type=MetricType.GAUGE,
            description="活跃用户数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(active_users),
                    labels={"service": "auth-service"}
                )
            ]
        ),
        Metric(
            name="active_sessions",
            metric_type=MetricType.GAUGE,
            description="活跃会话数",
            unit="count",
            points=[
                MetricPoint(
                    timestamp=datetime.now(),
                    value=float(sum(u["active_sessions"] for u in _user_activity.values())),
                    labels={"service": "auth-service"}
                )
            ]
        )
    ]
    
    # 告警
    alerts = []
    if not redis_connected:
        alerts.append(Alert(
            id=f"redis_disconnected_{int(time.time())}",
            level=AlertLevel.ERROR,
            title="Redis连接断开",
            message="无法连接到Redis缓存服务",
            service="auth-service",
            created_at=datetime.now(),
            metadata={"redis_connected": False}
        ))
    
    if resource_usage.cpu_percent > 80:
        alerts.append(Alert(
            id=f"cpu_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="CPU使用率过高",
            message=f"CPU使用率达到 {resource_usage.cpu_percent:.1f}%",
            service="auth-service",
            created_at=datetime.now(),
            metadata={"cpu_percent": resource_usage.cpu_percent}
        ))
    
    if resource_usage.memory_percent > 80:
        alerts.append(Alert(
            id=f"memory_high_{int(time.time())}",
            level=AlertLevel.WARNING,
            title="内存使用率过高",
            message=f"内存使用率达到 {resource_usage.memory_percent:.1f}%",
            service="auth-service",
            created_at=datetime.now(),
            metadata={"memory_percent": resource_usage.memory_percent}
        ))
    
    return ServiceMonitoringData(
        service_name="auth-service",
        health=health,
        api_statistics=api_statistics,
        metrics=metrics,
        resource_usage=resource_usage,
        alerts=alerts,
        last_updated=datetime.now()
    )


@router.get(
    "/monitoring/user-activity",
    summary="获取用户活跃度统计",
    description="返回用户活跃度统计信息",
    tags=["Monitoring"]
)
async def get_user_activity_stats() -> Dict[str, Any]:
    """获取用户活跃度统计"""
    user_stats = []
    for user_id, stats in _user_activity.items():
        user_stats.append({
            "user_id": stats["user_id"],
            "username": stats["username"],
            "active_sessions": stats["active_sessions"],
            "total_requests": stats["total_requests"],
            "last_activity": stats["last_activity"].isoformat(),
            "login_count": stats["login_count"]
        })
    
    return {
        "user_activity_stats": user_stats,
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








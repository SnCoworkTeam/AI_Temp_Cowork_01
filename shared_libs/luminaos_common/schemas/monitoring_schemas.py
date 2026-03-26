"""
监控数据模型
提供系统监控相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ServiceStatus(str, Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertLevel(str, Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServiceHealth(BaseModel):
    """服务健康状态"""
    service_name: str = Field(..., description="服务名称")
    status: ServiceStatus = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间（秒）")
    last_check: datetime = Field(..., description="最后检查时间")
    checks: Dict[str, Any] = Field(default_factory=dict, description="健康检查详情")


class MetricPoint(BaseModel):
    """指标数据点"""
    timestamp: datetime = Field(..., description="时间戳")
    value: float = Field(..., description="指标值")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")


class Metric(BaseModel):
    """指标模型"""
    name: str = Field(..., description="指标名称")
    metric_type: MetricType = Field(..., description="指标类型")
    description: str = Field(..., description="指标描述")
    unit: Optional[str] = Field(None, description="单位")
    points: List[MetricPoint] = Field(default_factory=list, description="数据点列表")


class APIStatistics(BaseModel):
    """API调用统计"""
    endpoint: str = Field(..., description="API端点")
    method: str = Field(..., description="HTTP方法")
    total_requests: int = Field(default=0, description="总请求数")
    success_count: int = Field(default=0, description="成功请求数")
    error_count: int = Field(default=0, description="错误请求数")
    avg_response_time: float = Field(default=0.0, description="平均响应时间（毫秒）")
    min_response_time: float = Field(default=0.0, description="最小响应时间（毫秒）")
    max_response_time: float = Field(default=0.0, description="最大响应时间（毫秒）")
    p95_response_time: float = Field(default=0.0, description="P95响应时间（毫秒）")
    p99_response_time: float = Field(default=0.0, description="P99响应时间（毫秒）")


class WorkflowExecutionStats(BaseModel):
    """工作流执行统计"""
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    workflow_name: Optional[str] = Field(None, description="工作流名称")
    total_executions: int = Field(default=0, description="总执行次数")
    success_count: int = Field(default=0, description="成功次数")
    failed_count: int = Field(default=0, description="失败次数")
    running_count: int = Field(default=0, description="运行中数量")
    avg_execution_time: float = Field(default=0.0, description="平均执行时间（秒）")
    total_execution_time: float = Field(default=0.0, description="总执行时间（秒）")


class UserActivityStats(BaseModel):
    """用户活跃度统计"""
    user_id: Optional[str] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    active_sessions: int = Field(default=0, description="活跃会话数")
    total_requests: int = Field(default=0, description="总请求数")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
    login_count: int = Field(default=0, description="登录次数")


class SystemResourceUsage(BaseModel):
    """系统资源使用情况"""
    cpu_percent: float = Field(default=0.0, description="CPU使用率（%）")
    memory_used: int = Field(default=0, description="已使用内存（字节）")
    memory_total: int = Field(default=0, description="总内存（字节）")
    memory_percent: float = Field(default=0.0, description="内存使用率（%）")
    disk_used: int = Field(default=0, description="已使用磁盘（字节）")
    disk_total: int = Field(default=0, description="总磁盘（字节）")
    disk_percent: float = Field(default=0.0, description="磁盘使用率（%）")
    network_bytes_sent: int = Field(default=0, description="网络发送字节数")
    network_bytes_recv: int = Field(default=0, description="网络接收字节数")


class Alert(BaseModel):
    """告警模型"""
    id: str = Field(..., description="告警ID")
    level: AlertLevel = Field(..., description="告警级别")
    title: str = Field(..., description="告警标题")
    message: str = Field(..., description="告警消息")
    service: str = Field(..., description="服务名称")
    created_at: datetime = Field(..., description="创建时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    resolved: bool = Field(default=False, description="是否已解决")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: datetime = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别")
    service: str = Field(..., description="服务名称")
    logger: str = Field(..., description="日志记录器")
    message: str = Field(..., description="日志消息")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    traceback: Optional[str] = Field(None, description="堆栈跟踪")


class ServiceMonitoringData(BaseModel):
    """服务监控数据"""
    service_name: str = Field(..., description="服务名称")
    health: ServiceHealth = Field(..., description="健康状态")
    api_statistics: List[APIStatistics] = Field(default_factory=list, description="API统计")
    metrics: List[Metric] = Field(default_factory=list, description="指标列表")
    resource_usage: Optional[SystemResourceUsage] = Field(None, description="资源使用情况")
    alerts: List[Alert] = Field(default_factory=list, description="告警列表")
    last_updated: datetime = Field(..., description="最后更新时间")


class MonitoringOverview(BaseModel):
    """监控总览"""
    services: List[ServiceMonitoringData] = Field(default_factory=list, description="服务列表")
    total_alerts: int = Field(default=0, description="总告警数")
    critical_alerts: int = Field(default=0, description="严重告警数")
    system_resource: Optional[SystemResourceUsage] = Field(None, description="系统资源")
    overall_status: ServiceStatus = Field(..., description="整体状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class MonitoringResponse(BaseModel):
    """监控响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[MonitoringOverview] = Field(None, description="监控数据")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class LogQueryParams(BaseModel):
    """日志查询参数"""
    service: Optional[str] = Field(None, description="服务名称")
    level: Optional[str] = Field(None, description="日志级别")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")


class LogQueryResponse(BaseModel):
    """日志查询响应"""
    success: bool = Field(..., description="是否成功")
    logs: List[LogEntry] = Field(default_factory=list, description="日志列表")
    total: int = Field(default=0, description="总数量")
    limit: int = Field(..., description="限制数量")
    offset: int = Field(..., description="偏移量")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")



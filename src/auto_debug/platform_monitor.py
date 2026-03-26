"""
与现有平台监控系统深度集成

功能：
1. 监控数据收集
2. 智能告警处理
3. 性能基线管理
4. 用户体验监控
"""
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """告警类别"""
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    ERROR = "error"
    RESOURCE = "resource"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Alert:
    """告警"""
    alert_id: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    service: str
    metric: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved: bool = False
    related_alerts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceBaseline:
    """性能基线"""
    metric_name: str
    service: str
    baseline_value: float
    p50: float
    p95: float
    p99: float
    std_dev: float
    sample_count: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserExperienceMetric:
    """用户体验指标"""
    service: str
    operation: str
    success_rate: float
    avg_response_time: float
    p95_response_time: float
    error_rate: float
    user_satisfaction: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class PlatformMonitor:
    """平台监控管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 监控系统配置
        self.prometheus_url = self.config.get("prometheus_url", "http://localhost:9090")
        self.grafana_url = self.config.get("grafana_url", "http://localhost:3000")
        self.loki_url = self.config.get("loki_url", "http://localhost:3100")
        self.sentry_dsn = self.config.get("sentry_dsn")
        
        # 服务配置
        self.service_urls = {
            "mcp-gateway": self.config.get("mcp_gateway_url", "http://localhost:8001"),
            "workflow-engine": self.config.get("workflow_engine_url", "http://localhost:8002"),
            "auth-service": self.config.get("auth_service_url", "http://localhost:8003"),
            "knowledge-base": self.config.get("knowledge_base_url", "http://localhost:8004"),
            "web-ui": self.config.get("web_ui_url", "http://localhost:3000"),
        }
        
        # 告警管理
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: List[Dict[str, Any]] = []
        
        # 性能基线
        self.performance_baselines: Dict[str, PerformanceBaseline] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # 用户体验指标
        self.user_experience_metrics: List[UserExperienceMetric] = []
        
        # 告警路由配置
        self.alert_routing: Dict[AlertCategory, List[str]] = {
            AlertCategory.PERFORMANCE: ["performance-team"],
            AlertCategory.AVAILABILITY: ["ops-team", "on-call"],
            AlertCategory.ERROR: ["dev-team", "on-call"],
            AlertCategory.RESOURCE: ["ops-team"],
            AlertCategory.SECURITY: ["security-team", "on-call"],
            AlertCategory.USER_EXPERIENCE: ["product-team"],
        }
        
        # 初始化告警规则
        self._initialize_alert_rules()
    
    # ==================== 监控数据收集 ====================
    
    async def collect_prometheus_metrics(
        self,
        query: str,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """从Prometheus获取平台指标"""
        try:
            from shared_libs.common.http_client import HTTPClient
            
            params = {"query": query}
            
            if time_range:
                start, end = time_range
                params["start"] = start.timestamp()
                params["end"] = end.timestamp()
            
            async with HTTPClient(self.prometheus_url) as client:
                response = await client.get("/api/v1/query", params=params)
                
                return {
                    "success": True,
                    "data": response.get("data", {}),
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to collect Prometheus metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def collect_grafana_dashboard_data(
        self,
        dashboard_uid: str,
        panel_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """从Grafana获取监控仪表板数据"""
        try:
            from shared_libs.common.http_client import HTTPClient
            
            headers = {}
            if self.config.get("grafana_api_key"):
                headers["Authorization"] = f"Bearer {self.config['grafana_api_key']}"
            
            async with HTTPClient(self.grafana_url, headers=headers) as client:
                if panel_id:
                    # 获取特定面板数据
                    response = await client.get(
                        f"/api/dashboards/uid/{dashboard_uid}/panels/{panel_id}/data"
                    )
                else:
                    # 获取整个仪表板
                    response = await client.get(f"/api/dashboards/uid/{dashboard_uid}")
                
                return {
                    "success": True,
                    "data": response,
                    "dashboard_uid": dashboard_uid,
                    "panel_id": panel_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to collect Grafana data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "dashboard_uid": dashboard_uid
            }
    
    async def collect_loki_logs(
        self,
        query: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """从Loki获取服务日志"""
        try:
            from shared_libs.common.http_client import HTTPClient
            
            params = {
                "query": query,
                "limit": limit
            }
            
            if start_time:
                params["start"] = int(start_time.timestamp() * 1e9)  # 纳秒
            if end_time:
                params["end"] = int(end_time.timestamp() * 1e9)
            
            async with HTTPClient(self.loki_url) as client:
                response = await client.get("/loki/api/v1/query_range", params=params)
                
                logs = []
                for stream in response.get("data", {}).get("result", []):
                    for entry in stream.get("values", []):
                        logs.append({
                            "timestamp": datetime.fromtimestamp(entry[0] / 1e9),
                            "message": entry[1],
                            "labels": stream.get("stream", {})
                        })
                
                return {
                    "success": True,
                    "logs": logs,
                    "count": len(logs),
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to collect Loki logs: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def collect_sentry_errors(
        self,
        project_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """从Sentry获取错误跟踪"""
        if not self.sentry_dsn:
            return {
                "success": False,
                "error": "Sentry DSN not configured"
            }
        
        try:
            from shared_libs.common.http_client import HTTPClient
            
            headers = {
                "Authorization": f"Bearer {self.config.get('sentry_api_token', '')}"
            }
            
            url = "https://sentry.io/api/0/projects"
            if project_id:
                url = f"{url}/{project_id}/events/"
            
            params = {}
            if start_time:
                params["start"] = start_time.isoformat()
            if end_time:
                params["end"] = end_time.isoformat()
            
            async with HTTPClient(base_url="https://sentry.io", headers=headers) as client:
                response = await client.get(url, params=params)
                
                return {
                    "success": True,
                    "errors": response,
                    "project_id": project_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to collect Sentry errors: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }
    
    async def collect_service_metrics(
        self,
        service_name: str
    ) -> Dict[str, Any]:
        """从服务直接收集指标"""
        service_url = self.service_urls.get(service_name)
        if not service_url:
            return {"error": "Service not configured"}
        
        try:
            from shared_libs.common.http_client import HTTPClient
            
            async with HTTPClient(service_url) as client:
                monitoring_data = await client.get("/api/monitoring")
                
                return {
                    "success": True,
                    "service": service_name,
                    "data": monitoring_data,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Failed to collect service metrics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "service": service_name
            }
    
    # ==================== 智能告警处理 ====================
    
    def _initialize_alert_rules(self):
        """初始化平台特有告警规则"""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "category": AlertCategory.ERROR,
                "condition": lambda m: m.get("error_rate", 0) > 5.0,
                "severity": AlertSeverity.ERROR,
                "message_template": "Service {service} has high error rate: {error_rate}%"
            },
            {
                "name": "slow_response_time",
                "category": AlertCategory.PERFORMANCE,
                "condition": lambda m: m.get("avg_response_time", 0) > 1000,  # ms
                "severity": AlertSeverity.WARNING,
                "message_template": "Service {service} has slow response time: {avg_response_time}ms"
            },
            {
                "name": "high_cpu_usage",
                "category": AlertCategory.RESOURCE,
                "condition": lambda m: m.get("cpu_usage", 0) > 80,
                "severity": AlertSeverity.WARNING,
                "message_template": "Service {service} has high CPU usage: {cpu_usage}%"
            },
            {
                "name": "high_memory_usage",
                "category": AlertCategory.RESOURCE,
                "condition": lambda m: m.get("memory_percent", 0) > 85,
                "severity": AlertSeverity.WARNING,
                "message_template": "Service {service} has high memory usage: {memory_percent}%"
            },
            {
                "name": "service_unhealthy",
                "category": AlertCategory.AVAILABILITY,
                "condition": lambda m: m.get("status") != "healthy",
                "severity": AlertSeverity.CRITICAL,
                "message_template": "Service {service} is unhealthy: {status}"
            },
            {
                "name": "low_user_satisfaction",
                "category": AlertCategory.USER_EXPERIENCE,
                "condition": lambda m: m.get("user_satisfaction", 100) < 70,
                "severity": AlertSeverity.WARNING,
                "message_template": "Service {service} has low user satisfaction: {user_satisfaction}%"
            },
        ]
    
    async def evaluate_alerts(
        self,
        metrics: Dict[str, Any]
    ) -> List[Alert]:
        """评估告警规则并生成告警"""
        alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    alert = Alert(
                        alert_id=f"alert_{uuid.uuid4().hex[:12]}",
                        severity=rule["severity"],
                        category=rule["category"],
                        title=rule["name"].replace("_", " ").title(),
                        message=rule["message_template"].format(**metrics),
                        service=metrics.get("service", "unknown"),
                        metric=metrics.get("metric_name"),
                        value=metrics.get("value"),
                        threshold=metrics.get("threshold"),
                        metadata={"rule": rule["name"]}
                    )
                    
                    alerts.append(alert)
                    self.active_alerts[alert.alert_id] = alert
            
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {str(e)}")
        
        return alerts
    
    async def analyze_alert_correlation(
        self,
        alerts: List[Alert]
    ) -> Dict[str, Any]:
        """分析告警相关性"""
        if len(alerts) < 2:
            return {"correlated": False, "groups": []}
        
        # 按服务分组
        service_groups = defaultdict(list)
        for alert in alerts:
            service_groups[alert.service].append(alert.alert_id)
        
        # 按时间窗口分组（5分钟内）
        time_groups = defaultdict(list)
        for alert in alerts:
            time_window = alert.created_at.replace(second=0, microsecond=0)
            time_groups[time_window].append(alert.alert_id)
        
        # 按类别分组
        category_groups = defaultdict(list)
        for alert in alerts:
            category_groups[alert.category].append(alert.alert_id)
        
        # 识别相关告警
        correlated_groups = []
        
        # 同一服务的多个告警
        for service, alert_ids in service_groups.items():
            if len(alert_ids) > 1:
                correlated_groups.append({
                    "type": "service_correlation",
                    "service": service,
                    "alert_ids": alert_ids,
                    "count": len(alert_ids)
                })
        
        # 同一时间窗口的多个告警
        for time_window, alert_ids in time_groups.items():
            if len(alert_ids) > 1:
                correlated_groups.append({
                    "type": "temporal_correlation",
                    "time_window": time_window.isoformat(),
                    "alert_ids": alert_ids,
                    "count": len(alert_ids)
                })
        
        # 更新告警的相关性信息
        for group in correlated_groups:
            for alert_id in group["alert_ids"]:
                if alert_id in self.active_alerts:
                    related = [aid for aid in group["alert_ids"] if aid != alert_id]
                    self.active_alerts[alert_id].related_alerts.extend(related)
        
        return {
            "correlated": len(correlated_groups) > 0,
            "groups": correlated_groups,
            "total_alerts": len(alerts)
        }
    
    async def classify_and_route_alert(
        self,
        alert: Alert
    ) -> Dict[str, Any]:
        """自动分类和路由告警"""
        # 确定路由目标
        routing_targets = self.alert_routing.get(alert.category, [])
        
        # 根据严重程度调整路由
        if alert.severity == AlertSeverity.CRITICAL:
            routing_targets.append("on-call")
        
        # 生成路由信息
        routing_info = {
            "alert_id": alert.alert_id,
            "category": alert.category.value,
            "severity": alert.severity.value,
            "targets": routing_targets,
            "routed_at": datetime.now().isoformat()
        }
        
        return routing_info
    
    async def generate_alert_response_suggestions(
        self,
        alert: Alert
    ) -> List[Dict[str, Any]]:
        """生成告警响应建议"""
        suggestions = []
        
        # 基于告警类别生成建议
        if alert.category == AlertCategory.PERFORMANCE:
            suggestions.append({
                "action": "check_service_performance",
                "description": "检查服务性能指标",
                "priority": "high"
            })
            suggestions.append({
                "action": "review_recent_deployments",
                "description": "检查最近的部署是否影响性能",
                "priority": "medium"
            })
        
        elif alert.category == AlertCategory.ERROR:
            suggestions.append({
                "action": "check_error_logs",
                "description": "查看错误日志获取详细信息",
                "priority": "high"
            })
            suggestions.append({
                "action": "review_error_patterns",
                "description": "分析错误模式确定根因",
                "priority": "high"
            })
        
        elif alert.category == AlertCategory.RESOURCE:
            suggestions.append({
                "action": "scale_service",
                "description": "考虑扩展服务实例",
                "priority": "medium"
            })
            suggestions.append({
                "action": "optimize_resource_usage",
                "description": "优化资源使用",
                "priority": "low"
            })
        
        elif alert.category == AlertCategory.AVAILABILITY:
            suggestions.append({
                "action": "check_service_health",
                "description": "检查服务健康状态",
                "priority": "critical"
            })
            suggestions.append({
                "action": "check_dependencies",
                "description": "检查服务依赖是否正常",
                "priority": "high"
            })
        
        elif alert.category == AlertCategory.USER_EXPERIENCE:
            suggestions.append({
                "action": "check_user_metrics",
                "description": "检查用户指标详情",
                "priority": "medium"
            })
            suggestions.append({
                "action": "review_user_feedback",
                "description": "查看用户反馈",
                "priority": "medium"
            })
        
        # 基于严重程度添加通用建议
        if alert.severity == AlertSeverity.CRITICAL:
            suggestions.append({
                "action": "escalate_to_oncall",
                "description": "立即升级到on-call",
                "priority": "critical"
            })
        
        return suggestions
    
    # ==================== 性能基线管理 ====================
    
    async def establish_performance_baseline(
        self,
        metric_name: str,
        service: str,
        duration_days: int = 7
    ) -> PerformanceBaseline:
        """建立平台性能基线"""
        # 收集历史数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=duration_days)
        
        # 从Prometheus获取历史指标
        query = f'{metric_name}{{service="{service}"}}'
        metrics_data = await self.collect_prometheus_metrics(
            query,
            time_range=(start_time, end_time)
        )
        
        # 提取指标值
        values = []
        for result in metrics_data.get("data", {}).get("result", []):
            for value_pair in result.get("values", []):
                values.append(float(value_pair[1]))
        
        if not values:
            # 如果没有历史数据，使用当前值
            current_metrics = await self.collect_service_metrics(service)
            current_value = current_metrics.get("data", {}).get(metric_name, 0)
            values = [current_value]
        
        # 计算统计值
        values_sorted = sorted(values)
        n = len(values_sorted)
        
        baseline_value = sum(values) / n if n > 0 else 0
        p50 = values_sorted[n // 2] if n > 0 else 0
        p95 = values_sorted[int(n * 0.95)] if n > 0 else 0
        p99 = values_sorted[int(n * 0.99)] if n > 0 else 0
        
        # 计算标准差
        variance = sum((x - baseline_value) ** 2 for x in values) / n if n > 0 else 0
        std_dev = variance ** 0.5
        
        baseline = PerformanceBaseline(
            metric_name=metric_name,
            service=service,
            baseline_value=baseline_value,
            p50=p50,
            p95=p95,
            p99=p99,
            std_dev=std_dev,
            sample_count=n
        )
        
        baseline_key = f"{service}:{metric_name}"
        self.performance_baselines[baseline_key] = baseline
        
        return baseline
    
    async def detect_performance_anomalies(
        self,
        metric_name: str,
        service: str,
        current_value: float
    ) -> Dict[str, Any]:
        """检测性能异常模式"""
        baseline_key = f"{service}:{metric_name}"
        baseline = self.performance_baselines.get(baseline_key)
        
        if not baseline:
            # 如果没有基线，先建立基线
            baseline = await self.establish_performance_baseline(metric_name, service)
        
        # 计算偏差
        deviation = current_value - baseline.baseline_value
        deviation_percent = (deviation / baseline.baseline_value * 100) if baseline.baseline_value > 0 else 0
        
        # 使用3-sigma规则检测异常
        is_anomaly = abs(deviation) > 3 * baseline.std_dev
        
        # 检测是否超过P95
        exceeds_p95 = current_value > baseline.p95
        
        # 检测是否超过P99
        exceeds_p99 = current_value > baseline.p99
        
        anomaly_result = {
            "metric": metric_name,
            "service": service,
            "current_value": current_value,
            "baseline_value": baseline.baseline_value,
            "deviation": deviation,
            "deviation_percent": deviation_percent,
            "is_anomaly": is_anomaly,
            "exceeds_p95": exceeds_p95,
            "exceeds_p99": exceeds_p99,
            "baseline": asdict(baseline),
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录到历史
        self.metric_history[baseline_key].append(current_value)
        
        return anomaly_result
    
    async def predict_performance_trends(
        self,
        metric_name: str,
        service: str,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """性能趋势预测"""
        baseline_key = f"{service}:{metric_name}"
        history = list(self.metric_history.get(baseline_key, []))
        
        if len(history) < 10:
            return {
                "success": False,
                "error": "Insufficient historical data for prediction"
            }
        
        # 简单的线性回归预测
        n = len(history)
        x = list(range(n))
        y = history
        
        # 计算回归系数
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator > 0 else 0
        intercept = y_mean - slope * x_mean
        
        # 预测未来值
        forecast = []
        for i in range(1, forecast_days + 1):
            predicted_value = slope * (n + i) + intercept
            forecast.append({
                "day": i,
                "predicted_value": predicted_value,
                "timestamp": (datetime.now() + timedelta(days=i)).isoformat()
            })
        
        return {
            "success": True,
            "metric": metric_name,
            "service": service,
            "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
            "slope": slope,
            "forecast": forecast,
            "current_value": history[-1] if history else None
        }
    
    async def suggest_capacity_planning(
        self,
        service: str,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """容量规划建议"""
        # 获取关键指标的趋势
        metrics = ["cpu_usage", "memory_usage", "request_rate"]
        
        trends = {}
        for metric in metrics:
            trend_result = await self.predict_performance_trends(metric, service, forecast_days)
            if trend_result.get("success"):
                trends[metric] = trend_result
        
        # 生成容量规划建议
        recommendations = []
        
        # 检查CPU趋势
        if "cpu_usage" in trends:
            cpu_trend = trends["cpu_usage"]
            if cpu_trend.get("trend") == "increasing":
                current_cpu = cpu_trend.get("current_value", 0)
                if current_cpu > 70:
                    recommendations.append({
                        "metric": "cpu_usage",
                        "action": "scale_up",
                        "reason": f"CPU usage is {current_cpu:.1f}% and trending upward",
                        "priority": "high"
                    })
        
        # 检查内存趋势
        if "memory_usage" in trends:
            memory_trend = trends["memory_usage"]
            if memory_trend.get("trend") == "increasing":
                current_memory = memory_trend.get("current_value", 0)
                if current_memory > 80:
                    recommendations.append({
                        "metric": "memory_usage",
                        "action": "increase_memory",
                        "reason": f"Memory usage is {current_memory:.1f}% and trending upward",
                        "priority": "high"
                    })
        
        # 检查请求率趋势
        if "request_rate" in trends:
            request_trend = trends["request_rate"]
            if request_trend.get("trend") == "increasing":
                recommendations.append({
                    "metric": "request_rate",
                    "action": "scale_horizontal",
                    "reason": "Request rate is increasing, consider horizontal scaling",
                    "priority": "medium"
                })
        
        return {
            "service": service,
            "forecast_period_days": forecast_days,
            "trends": trends,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== 用户体验监控 ====================
    
    async def track_user_operation_success(
        self,
        service: str,
        operation: str,
        success: bool,
        response_time: float
    ):
        """跟踪用户操作成功率"""
        # 记录操作
        operation_key = f"{service}:{operation}"
        
        if not hasattr(self, "_operation_stats"):
            self._operation_stats = defaultdict(lambda: {
                "total": 0,
                "success": 0,
                "failed": 0,
                "response_times": deque(maxlen=100)
            })
        
        stats = self._operation_stats[operation_key]
        stats["total"] += 1
        
        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
        
        stats["response_times"].append(response_time)
        
        # 计算成功率
        success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        # 计算平均响应时间
        if stats["response_times"]:
            avg_response_time = sum(stats["response_times"]) / len(stats["response_times"])
            p95_response_time = sorted(stats["response_times"])[int(len(stats["response_times"]) * 0.95)] if stats["response_times"] else 0
        else:
            avg_response_time = 0
            p95_response_time = 0
        
        # 计算错误率
        error_rate = (stats["failed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        # 创建用户体验指标
        ux_metric = UserExperienceMetric(
            service=service,
            operation=operation,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            error_rate=error_rate
        )
        
        self.user_experience_metrics.append(ux_metric)
        
        # 保持最近1000条记录
        if len(self.user_experience_metrics) > 1000:
            self.user_experience_metrics = self.user_experience_metrics[-1000:]
        
        return ux_metric
    
    async def get_user_experience_summary(
        self,
        service: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取用户体验摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        metrics = self.user_experience_metrics
        if service:
            metrics = [m for m in metrics if m.service == service]
        
        metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        if not metrics:
            return {
                "service": service or "all",
                "period_hours": hours,
                "no_data": True
            }
        
        # 计算总体指标
        total_operations = len(metrics)
        avg_success_rate = sum(m.success_rate for m in metrics) / total_operations
        avg_response_time = sum(m.avg_response_time for m in metrics) / total_operations
        avg_error_rate = sum(m.error_rate for m in metrics) / total_operations
        
        # 按操作分组
        operation_stats = defaultdict(lambda: {
            "count": 0,
            "success_rate": 0,
            "avg_response_time": 0
        })
        
        for metric in metrics:
            op_key = f"{metric.service}:{metric.operation}"
            op_stats = operation_stats[op_key]
            op_stats["count"] += 1
            op_stats["success_rate"] += metric.success_rate
            op_stats["avg_response_time"] += metric.avg_response_time
        
        # 计算平均值
        for op_key, op_stats in operation_stats.items():
            count = op_stats["count"]
            op_stats["success_rate"] /= count
            op_stats["avg_response_time"] /= count
        
        return {
            "service": service or "all",
            "period_hours": hours,
            "total_operations": total_operations,
            "overall_success_rate": avg_success_rate,
            "overall_avg_response_time": avg_response_time,
            "overall_error_rate": avg_error_rate,
            "operation_stats": dict(operation_stats),
            "timestamp": datetime.now().isoformat()
        }
    
    async def monitor_response_times(
        self,
        service: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """监控响应时间"""
        # 从服务监控数据获取响应时间
        metrics_data = await self.collect_service_metrics(service)
        
        if not metrics_data.get("success"):
            return {
                "success": False,
                "error": "Failed to collect metrics"
            }
        
        api_stats = metrics_data.get("data", {}).get("api_statistics", [])
        
        endpoint_stats = None
        for stat in api_stats:
            if stat.get("endpoint") == endpoint:
                endpoint_stats = stat
                break
        
        if not endpoint_stats:
            return {
                "success": False,
                "error": "Endpoint not found in statistics"
            }
        
        return {
            "success": True,
            "service": service,
            "endpoint": endpoint,
            "avg_response_time": endpoint_stats.get("avg_response_time", 0),
            "p95_response_time": endpoint_stats.get("p95_response_time", 0),
            "p99_response_time": endpoint_stats.get("p99_response_time", 0),
            "min_response_time": endpoint_stats.get("min_response_time", 0),
            "max_response_time": endpoint_stats.get("max_response_time", 0),
            "total_requests": endpoint_stats.get("total_requests", 0),
            "timestamp": datetime.now().isoformat()
        }
    
    async def calculate_error_rate(
        self,
        service: str,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """计算错误率统计"""
        start_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        # 从Loki获取错误日志
        error_query = f'{{service="{service}"}} |= "error" |= "exception"'
        logs_data = await self.collect_loki_logs(
            error_query,
            start_time=start_time
        )
        
        # 获取总请求数
        metrics_data = await self.collect_service_metrics(service)
        total_requests = 0
        if metrics_data.get("success"):
            api_stats = metrics_data.get("data", {}).get("api_statistics", [])
            total_requests = sum(stat.get("total_requests", 0) for stat in api_stats)
        
        # 计算错误数
        error_count = logs_data.get("count", 0)
        
        # 计算错误率
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "service": service,
            "time_window_minutes": time_window_minutes,
            "total_requests": total_requests,
            "error_count": error_count,
            "error_rate": error_rate,
            "timestamp": datetime.now().isoformat()
        }
    
    async def calculate_user_satisfaction(
        self,
        service: str
    ) -> Dict[str, Any]:
        """计算用户满意度指标"""
        # 获取用户体验摘要
        ux_summary = await self.get_user_experience_summary(service, hours=24)
        
        if ux_summary.get("no_data"):
            return {
                "success": False,
                "error": "No user experience data available"
            }
        
        success_rate = ux_summary.get("overall_success_rate", 0)
        avg_response_time = ux_summary.get("overall_avg_response_time", 0)
        
        # 基于成功率和响应时间计算满意度
        # 简化计算：成功率权重70%，响应时间权重30%
        response_time_score = max(0, 100 - (avg_response_time / 10))  # 响应时间越短分数越高
        satisfaction_score = success_rate * 0.7 + response_time_score * 0.3
        
        # 确定满意度等级
        if satisfaction_score >= 90:
            satisfaction_level = "excellent"
        elif satisfaction_score >= 80:
            satisfaction_level = "good"
        elif satisfaction_score >= 70:
            satisfaction_level = "fair"
        else:
            satisfaction_level = "poor"
        
        return {
            "success": True,
            "service": service,
            "satisfaction_score": satisfaction_score,
            "satisfaction_level": satisfaction_level,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "timestamp": datetime.now().isoformat()
        }


# 全局监控器实例
_monitor_instance: Optional[PlatformMonitor] = None


def get_platform_monitor(
    config: Optional[Dict[str, Any]] = None
) -> PlatformMonitor:
    """获取平台监控器实例（单例模式）"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PlatformMonitor(config)
    return _monitor_instance


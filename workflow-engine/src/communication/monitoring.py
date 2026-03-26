"""
智能体通信监控和调试工具
提供完整的通信监控、性能分析、错误诊断和调试功能
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import statistics
import threading
import weakref

from shared_libs.luminaos_common.schemas.agent_communication import (
    AgentMessage, MessageType, CommunicationMetrics, CommunicationDiagnostics,
    HealthCheckMessage, MetricsReportMessage, LogEntryMessage, DebugTraceMessage
)

logger = logging.getLogger(__name__)


class MonitoringLevel(str, Enum):
    """监控级别"""
    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"
    VERBOSE = "verbose"
    DEBUG = "debug"


class AlertSeverity(str, Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TraceEventType(str, Enum):
    """跟踪事件类型"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_ROUTED = "message_routed"
    MESSAGE_PROCESSED = "message_processed"
    MESSAGE_FAILED = "message_failed"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    EXECUTION_START = "execution_start"
    EXECUTION_COMPLETE = "execution_complete"
    STATE_CHANGED = "state_changed"


@dataclass
class TraceEvent:
    """跟踪事件"""
    event_id: str
    event_type: TraceEventType
    timestamp: datetime
    source_node: str
    target_node: Optional[str] = None
    message_id: Optional[str] = None
    message_type: Optional[MessageType] = None
    duration: Optional[float] = None
    status: str = "success"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """性能指标"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    node_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    source_node: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommunicationMonitor:
    """通信监控器"""

    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.BASIC):
        self.monitoring_level = monitoring_level
        self.trace_events: deque = deque(maxlen=10000)
        self.performance_metrics: deque = deque(maxlen=5000)
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.message_counters: Dict[str, int] = defaultdict(int)
        self.error_counters: Dict[str, int] = defaultdict(int)
        self.latency_measurements: Dict[str, List[float]] = defaultdict(list)
        self.throughput_measurements: Dict[str, List[float]] = defaultdict(list)
        self.subscribers: List[Callable] = []
        self._running = False
        self._monitoring_tasks: Set[asyncio.Task] = set()

    async def start(self):
        """启动监控器"""
        self._running = True
        logger.info("通信监控器启动")

        # 启动监控任务
        if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.VERBOSE, MonitoringLevel.DEBUG]:
            task = asyncio.create_task(self._metrics_collector())
            self._monitoring_tasks.add(task)

            task = asyncio.create_task(self._connection_monitor())
            self._monitoring_tasks.add(task)

        if self.monitoring_level == MonitoringLevel.DEBUG:
            task = asyncio.create_task(self._debug_tracer())
            self._monitoring_tasks.add(task)

    async def stop(self):
        """停止监控器"""
        self._running = False

        # 取消监控任务
        for task in self._monitoring_tasks:
            task.cancel()

        await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)
        logger.info("通信监控器停止")

    def record_message_event(
        self,
        event_type: TraceEventType,
        message: AgentMessage,
        duration: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """记录消息事件"""
        if self.monitoring_level == MonitoringLevel.NONE:
            return

        event = TraceEvent(
            event_id=f"{message.header.message_id}_{event_type.value}",
            event_type=event_type,
            timestamp=datetime.now(),
            source_node=message.header.source,
            target_node=message.header.destination,
            message_id=message.header.message_id,
            message_type=message.header.message_type,
            duration=duration,
            status="success" if error_message is None else "failed",
            error_message=error_message
        )

        self.trace_events.append(event)

        # 更新计数器
        self.message_counters[f"{event_type.value}_{message.header.message_type.value}"] += 1

        if error_message:
            self.error_counters[f"error_{message.header.message_type.value}"] += 1

        # 记录延迟
        if duration is not None:
            self.latency_measurements[message.header.message_type.value].append(duration)

        # 通知订阅者
        self._notify_subscribers(event)

    def record_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        node_id: Optional[str] = None,
        tags: Dict[str, str] = None
    ):
        """记录性能指标"""
        if self.monitoring_level in [MonitoringLevel.NONE, MonitoringLevel.BASIC]:
            return

        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            node_id=node_id,
            tags=tags or {}
        )

        self.performance_metrics.append(metric)

    def record_connection_event(self, node_id: str, event_type: str, metadata: Dict[str, Any] = None):
        """记录连接事件"""
        if event_type == "connected":
            self.active_connections[node_id] = {
                "connected_at": datetime.now(),
                "last_activity": datetime.now(),
                "metadata": metadata or {}
            }
        elif event_type == "disconnected":
            if node_id in self.active_connections:
                del self.active_connections[node_id]

        # 记录跟踪事件
        if event_type == "connected":
            trace_type = TraceEventType.CONNECTION_ESTABLISHED
        else:
            trace_type = TraceEventType.CONNECTION_LOST

        event = TraceEvent(
            event_id=f"{node_id}_{event_type}_{int(time.time())}",
            event_type=trace_type,
            timestamp=datetime.now(),
            source_node=node_id,
            metadata=metadata or {}
        )

        self.trace_events.append(event)

    def update_connection_activity(self, node_id: str):
        """更新连接活动"""
        if node_id in self.active_connections:
            self.active_connections[node_id]["last_activity"] = datetime.now()

    def subscribe(self, callback: Callable[[TraceEvent], None]):
        """订阅监控事件"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def _notify_subscribers(self, event: TraceEvent):
        """通知订阅者"""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"通知订阅者失败: {e}")

    async def _metrics_collector(self):
        """指标收集器"""
        while self._running:
            try:
                await asyncio.sleep(10)  # 每10秒收集一次

                # 计算吞吐量指标
                current_time = datetime.now()
                time_window = timedelta(minutes=1)

                recent_events = [
                    event for event in self.trace_events
                    if current_time - event.timestamp <= time_window
                ]

                # 按消息类型分组计算吞吐量
                message_type_counts = defaultdict(int)
                for event in recent_events:
                    if event.message_type:
                        message_type_counts[event.message_type.value] += 1

                for message_type, count in message_type_counts.items():
                    throughput = count / 60.0  # 每秒消息数
                    self.record_performance_metric(
                        f"throughput_{message_type}",
                        throughput,
                        "messages/sec"
                    )

                # 计算延迟指标
                for message_type, latencies in self.latency_measurements.items():
                    if latencies:
                        avg_latency = statistics.mean(latencies)
                        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)

                        self.record_performance_metric(f"latency_avg_{message_type}", avg_latency, "ms")
                        self.record_performance_metric(f"latency_p95_{message_type}", p95_latency, "ms")

                        # 清理旧数据
                        if len(latencies) > 1000:
                            self.latency_measurements[message_type] = latencies[-500:]

            except Exception as e:
                logger.error(f"指标收集失败: {e}")
                await asyncio.sleep(5)

    async def _connection_monitor(self):
        """连接监控器"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次

                current_time = datetime.now()
                inactive_threshold = timedelta(minutes=5)

                # 检查不活跃连接
                inactive_connections = []
                for node_id, conn_info in self.active_connections.items():
                    if current_time - conn_info["last_activity"] > inactive_threshold:
                        inactive_connections.append(node_id)

                for node_id in inactive_connections:
                    logger.warning(f"检测到不活跃连接: {node_id}")
                    # 可以选择断开连接或发送心跳

            except Exception as e:
                logger.error(f"连接监控失败: {e}")
                await asyncio.sleep(10)

    async def _debug_tracer(self):
        """调试跟踪器"""
        while self._running:
            try:
                await asyncio.sleep(1)  # 每秒运行一次

                # 详细的调试信息收集
                if self.monitoring_level == MonitoringLevel.DEBUG:
                    # 收集系统状态快照
                    snapshot = {
                        "timestamp": datetime.now().isoformat(),
                        "active_connections": len(self.active_connections),
                        "trace_events_count": len(self.trace_events),
                        "performance_metrics_count": len(self.performance_metrics),
                        "memory_usage": self._get_memory_usage()
                    }

                    debug_event = TraceEvent(
                        event_id=f"debug_snapshot_{int(time.time())}",
                        event_type=TraceEventType.STATE_CHANGED,
                        timestamp=datetime.now(),
                        source_node="monitor",
                        metadata=snapshot
                    )

                    self.trace_events.append(debug_event)

            except Exception as e:
                logger.error(f"调试跟踪失败: {e}")
                await asyncio.sleep(5)

    def _get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_percent": process.memory_percent(),
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}

    def get_communication_statistics(self, time_window: int = 3600) -> Dict[str, Any]:
        """获取通信统计"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=time_window)

        recent_events = [
            event for event in self.trace_events
            if event.timestamp >= cutoff_time
        ]

        # 统计消息类型分布
        message_type_stats = defaultdict(int)
        error_stats = defaultdict(int)
        node_stats = defaultdict(int)

        for event in recent_events:
            if event.message_type:
                message_type_stats[event.message_type.value] += 1

            if event.status == "failed":
                error_stats[event.event_type.value] += 1

            node_stats[event.source_node] += 1

        # 计算延迟统计
        latency_stats = {}
        for message_type, latencies in self.latency_measurements.items():
            recent_latencies = [l for l in latencies if l is not None]
            if recent_latencies:
                latency_stats[message_type] = {
                    "avg": statistics.mean(recent_latencies),
                    "min": min(recent_latencies),
                    "max": max(recent_latencies),
                    "count": len(recent_latencies)
                }

        return {
            "time_window_seconds": time_window,
            "total_events": len(recent_events),
            "active_connections": len(self.active_connections),
            "message_type_distribution": dict(message_type_stats),
            "error_distribution": dict(error_stats),
            "node_activity": dict(node_stats),
            "latency_statistics": latency_stats,
            "error_rate": sum(error_stats.values()) / len(recent_events) if recent_events else 0
        }

    def export_trace_data(self, format_type: str = "json") -> str:
        """导出跟踪数据"""
        if format_type == "json":
            data = {
                "export_time": datetime.now().isoformat(),
                "monitoring_level": self.monitoring_level.value,
                "events": [
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "source_node": event.source_node,
                        "target_node": event.target_node,
                        "message_id": event.message_id,
                        "message_type": event.message_type.value if event.message_type else None,
                        "duration": event.duration,
                        "status": event.status,
                        "error_message": event.error_message,
                        "metadata": event.metadata
                    }
                    for event in self.trace_events
                ]
            }
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []
        self._alert_checker_running = False

    def add_alert_rule(
        self,
        rule_name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_period: int = 300  # 5分钟冷却期
    ):
        """添加告警规则"""
        self.alert_rules[rule_name] = {
            "condition": condition,
            "severity": severity,
            "message_template": message_template,
            "cooldown_period": cooldown_period,
            "last_triggered": None
        }

    async def start_alert_checking(self, monitor: CommunicationMonitor, check_interval: int = 30):
        """开始告警检查"""
        self._alert_checker_running = True

        while self._alert_checker_running:
            try:
                # 获取监控数据
                stats = monitor.get_communication_statistics(time_window=300)  # 5分钟窗口

                # 检查所有告警规则
                for rule_name, rule_config in self.alert_rules.items():
                    try:
                        # 检查冷却期
                        if (rule_config["last_triggered"] and
                            datetime.now() - rule_config["last_triggered"] < timedelta(seconds=rule_config["cooldown_period"])):
                            continue

                        # 评估条件
                        if rule_config["condition"](stats):
                            await self._trigger_alert(rule_name, rule_config, stats)

                    except Exception as e:
                        logger.error(f"告警规则检查失败 {rule_name}: {e}")

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"告警检查失败: {e}")
                await asyncio.sleep(check_interval)

    async def _trigger_alert(self, rule_name: str, rule_config: Dict[str, Any], stats: Dict[str, Any]):
        """触发告警"""
        alert_id = f"{rule_name}_{int(time.time())}"

        alert = Alert(
            alert_id=alert_id,
            alert_type=rule_name,
            severity=rule_config["severity"],
            message=rule_config["message_template"].format(**stats),
            source_node="alert_manager",
            timestamp=datetime.now(),
            metadata={"trigger_stats": stats}
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        rule_config["last_triggered"] = datetime.now()

        # 发送通知
        await self._send_notifications(alert)

        logger.warning(f"告警触发: {rule_name} - {alert.message}")

    async def _send_notifications(self, alert: Alert):
        """发送告警通知"""
        for handler in self.notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"发送告警通知失败: {e}")

    def add_notification_handler(self, handler: Callable):
        """添加通知处理器"""
        self.notification_handlers.append(handler)

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            logger.info(f"告警已解决: {alert_id}")

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.now() - alert.timestamp <= timedelta(hours=24)
        ]

        severity_counts = defaultdict(int)
        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1

        return {
            "active_alerts_count": len(self.active_alerts),
            "total_alerts_24h": len(recent_alerts),
            "severity_distribution_24h": dict(severity_counts),
            "alert_rules_count": len(self.alert_rules)
        }


class DebugSessionManager:
    """调试会话管理器"""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.breakpoints: Dict[str, Set[str]] = defaultdict(set)
        self.watch_variables: Dict[str, List[str]] = defaultdict(list)

    def create_debug_session(self, session_id: str, workflow_id: str, user_id: str) -> bool:
        """创建调试会话"""
        if session_id in self.active_sessions:
            return False

        self.active_sessions[session_id] = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "breakpoints": set(),
            "watch_variables": [],
            "current_state": {},
            "step_mode": False,
            "paused_at": None
        }

        logger.info(f"创建调试会话: {session_id}")
        return True

    def add_breakpoint(self, session_id: str, node_id: str, condition: str = None):
        """添加断点"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["breakpoints"].add(node_id)
            self.breakpoints[session_id].add(node_id)
            logger.info(f"添加断点: {session_id} -> {node_id}")

    def remove_breakpoint(self, session_id: str, node_id: str):
        """移除断点"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["breakpoints"].discard(node_id)
            self.breakpoints[session_id].discard(node_id)
            logger.info(f"移除断点: {session_id} -> {node_id}")

    def check_breakpoint(self, session_id: str, node_id: str, execution_context: Dict[str, Any]) -> bool:
        """检查是否命中断点"""
        if session_id not in self.active_sessions:
            return False

        if node_id in self.breakpoints[session_id]:
            # 更新调试状态
            self.active_sessions[session_id]["paused_at"] = node_id
            self.active_sessions[session_id]["current_state"] = execution_context

            logger.info(f"命中断点: {session_id} -> {node_id}")
            return True

        return False

    def add_watch_variable(self, session_id: str, variable_path: str):
        """添加监视变量"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["watch_variables"].append(variable_path)
            logger.info(f"添加监视变量: {session_id} -> {variable_path}")

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        return self.active_sessions.get(session_id)

    def close_session(self, session_id: str):
        """关闭调试会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            if session_id in self.breakpoints:
                del self.breakpoints[session_id]
            logger.info(f"关闭调试会话: {session_id}")


# ==================== 预定义告警规则 ====================

def setup_default_alert_rules(alert_manager: AlertManager):
    """设置默认告警规则"""

    # 高错误率告警
    alert_manager.add_alert_rule(
        "high_error_rate",
        lambda stats: stats.get("error_rate", 0) > 0.1,  # 错误率超过10%
        AlertSeverity.ERROR,
        "检测到高错误率: {error_rate:.2%}"
    )

    # 无活跃连接告警
    alert_manager.add_alert_rule(
        "no_active_connections",
        lambda stats: stats.get("active_connections", 0) == 0,
        AlertSeverity.WARNING,
        "没有活跃连接"
    )

    # 高延迟告警
    def check_high_latency(stats):
        latency_stats = stats.get("latency_statistics", {})
        for message_type, latency_info in latency_stats.items():
            if latency_info.get("avg", 0) > 5000:  # 平均延迟超过5秒
                return True
        return False

    alert_manager.add_alert_rule(
        "high_latency",
        check_high_latency,
        AlertSeverity.WARNING,
        "检测到高延迟"
    )


# ==================== 使用示例 ====================

async def example_monitoring():
    """监控使用示例"""

    # 创建监控器
    monitor = CommunicationMonitor(MonitoringLevel.DETAILED)
    await monitor.start()

    # 创建告警管理器
    alert_manager = AlertManager()
    setup_default_alert_rules(alert_manager)

    # 添加通知处理器
    async def log_alert(alert: Alert):
        print(f"告警通知: [{alert.severity.value}] {alert.message}")

    alert_manager.add_notification_handler(log_alert)

    # 模拟消息事件
    from shared_libs.luminaos_common.schemas.agent_communication import AgentMessage, MessageHeader

    message = AgentMessage(
        header=MessageHeader(
            message_type=MessageType.EXECUTION_START,
            source="test_node_1",
            destination="test_node_2"
        ),
        payload={}
    )

    # 记录事件
    monitor.record_message_event(TraceEventType.MESSAGE_SENT, message)
    monitor.record_message_event(TraceEventType.MESSAGE_RECEIVED, message, duration=150.0)

    # 启动告警检查
    asyncio.create_task(alert_manager.start_alert_checking(monitor, check_interval=10))

    # 等待一段时间收集数据
    await asyncio.sleep(5)

    # 获取统计信息
    stats = monitor.get_communication_statistics()
    print(f"通信统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    # 导出跟踪数据
    trace_data = monitor.export_trace_data()
    print(f"跟踪数据已导出，大小: {len(trace_data)} 字符")

    await monitor.stop()

if __name__ == "__main__":
    asyncio.run(example_monitoring())
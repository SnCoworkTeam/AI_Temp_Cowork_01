"""
治理仪表板
多角色视图（高管、业务负责人、IT/架构师）
治理指标统计和合规审计报告
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

try:
    from .audit_logger import AuditLogger, AuditEventType, AuditEventSeverity
except ImportError:
    from audit_logger import AuditLogger, AuditEventType, AuditEventSeverity

logger = logging.getLogger(__name__)


class DashboardRole(Enum):
    """仪表板角色"""
    EXECUTIVE = "executive"  # 高管
    BUSINESS_OWNER = "business_owner"  # 业务负责人
    IT_ARCHITECT = "it_architect"  # IT/架构师
    AUDITOR = "auditor"  # 审计员


@dataclass
class GovernanceMetric:
    """治理指标"""
    name: str
    value: float
    unit: str = ""
    trend: Optional[str] = None  # "up" | "down" | "stable"
    threshold: Optional[float] = None
    status: str = "normal"  # "normal" | "warning" | "critical"
    description: str = ""


@dataclass
class DashboardView:
    """仪表板视图"""
    role: DashboardRole
    metrics: List[GovernanceMetric]
    charts: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    last_updated: datetime


class GovernanceDashboard:
    """治理仪表板"""
    
    def __init__(self, audit_logger: AuditLogger):
        """
        初始化治理仪表板
        
        Args:
            audit_logger: 审计日志记录器
        """
        self.audit_logger = audit_logger
    
    def get_executive_view(self, days: int = 30) -> DashboardView:
        """
        获取高管视图
        
        Args:
            days: 统计天数
            
        Returns:
            DashboardView: 高管视图
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 获取审计事件
        events = self.audit_logger.query_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # 计算指标
        metrics = []
        
        # 1. 意图识别成功率
        intent_events = [e for e in events if e.event_type == AuditEventType.INTENT_RECOGNITION]
        intent_success_count = sum(1 for e in intent_events if e.result == "success")
        intent_success_rate = (intent_success_count / len(intent_events) * 100) if intent_events else 0
        metrics.append(GovernanceMetric(
            name="意图识别成功率",
            value=intent_success_rate,
            unit="%",
            threshold=80.0,
            status="normal" if intent_success_rate >= 80 else "warning",
            description="意图识别成功的比例"
        ))
        
        # 2. 资源操作成功率
        operation_events = [e for e in events if e.event_type == AuditEventType.RESOURCE_OPERATION]
        operation_success_count = sum(1 for e in operation_events if e.result == "success")
        operation_success_rate = (operation_success_count / len(operation_events) * 100) if operation_events else 0
        metrics.append(GovernanceMetric(
            name="资源操作成功率",
            value=operation_success_rate,
            unit="%",
            threshold=95.0,
            status="normal" if operation_success_rate >= 95 else "warning",
            description="资源操作成功的比例"
        ))
        
        # 3. 策略拒绝率
        policy_events = [e for e in events if e.event_type == AuditEventType.POLICY_EVALUATION]
        policy_denied_count = sum(1 for e in policy_events if e.result == "denied")
        policy_denied_rate = (policy_denied_count / len(policy_events) * 100) if policy_events else 0
        metrics.append(GovernanceMetric(
            name="策略拒绝率",
            value=policy_denied_rate,
            unit="%",
            threshold=10.0,
            status="normal" if policy_denied_rate <= 10 else "warning",
            description="被策略拒绝的操作比例"
        ))
        
        # 4. 总操作数
        total_operations = len(operation_events)
        metrics.append(GovernanceMetric(
            name="总操作数",
            value=total_operations,
            unit="次",
            description=f"过去{days}天的总操作数"
        ))
        
        # 5. 活跃用户数
        unique_users = len(set(e.user for e in events))
        metrics.append(GovernanceMetric(
            name="活跃用户数",
            value=unique_users,
            unit="人",
            description=f"过去{days}天的活跃用户数"
        ))
        
        # 图表数据
        charts = [
            {
                "type": "line",
                "title": "意图识别成功率趋势",
                "data": self._get_intent_success_trend(events, days)
            },
            {
                "type": "bar",
                "title": "资源操作类型分布",
                "data": self._get_operation_type_distribution(operation_events)
            }
        ]
        
        # 告警
        alerts = self._get_alerts(metrics, events)
        
        return DashboardView(
            role=DashboardRole.EXECUTIVE,
            metrics=metrics,
            charts=charts,
            alerts=alerts,
            last_updated=datetime.now()
        )
    
    def get_business_owner_view(self, days: int = 7) -> DashboardView:
        """
        获取业务负责人视图
        
        Args:
            days: 统计天数
            
        Returns:
            DashboardView: 业务负责人视图
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        events = self.audit_logger.query_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        metrics = []
        
        # 1. 工作流执行成功率
        workflow_events = [e for e in events if e.event_type == AuditEventType.WORKFLOW_EXECUTION]
        workflow_success_count = sum(1 for e in workflow_events if e.result == "success")
        workflow_success_rate = (workflow_success_count / len(workflow_events) * 100) if workflow_events else 0
        metrics.append(GovernanceMetric(
            name="工作流执行成功率",
            value=workflow_success_rate,
            unit="%",
            threshold=90.0,
            status="normal" if workflow_success_rate >= 90 else "warning",
            description="工作流执行成功的比例"
        ))
        
        # 2. 平均工作流执行时间
        workflow_times = [e.metadata.get("execution_time", 0) for e in workflow_events if "execution_time" in e.metadata]
        avg_execution_time = sum(workflow_times) / len(workflow_times) if workflow_times else 0
        metrics.append(GovernanceMetric(
            name="平均工作流执行时间",
            value=avg_execution_time,
            unit="秒",
            threshold=30.0,
            status="normal" if avg_execution_time <= 30 else "warning",
            description="工作流平均执行时间"
        ))
        
        # 3. 审批请求数
        approval_events = [e for e in events if e.event_type == AuditEventType.APPROVAL_REQUEST]
        metrics.append(GovernanceMetric(
            name="审批请求数",
            value=len(approval_events),
            unit="次",
            description=f"过去{days}天的审批请求数"
        ))
        
        charts = [
            {
                "type": "pie",
                "title": "工作流执行状态分布",
                "data": self._get_workflow_status_distribution(workflow_events)
            }
        ]
        
        alerts = self._get_alerts(metrics, events)
        
        return DashboardView(
            role=DashboardRole.BUSINESS_OWNER,
            metrics=metrics,
            charts=charts,
            alerts=alerts,
            last_updated=datetime.now()
        )
    
    def get_it_architect_view(self, days: int = 7) -> DashboardView:
        """
        获取IT/架构师视图
        
        Args:
            days: 统计天数
            
        Returns:
            DashboardView: IT/架构师视图
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        events = self.audit_logger.query_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        metrics = []
        
        # 1. 策略评估覆盖率
        policy_events = [e for e in events if e.event_type == AuditEventType.POLICY_EVALUATION]
        operation_events = [e for e in events if e.event_type == AuditEventType.RESOURCE_OPERATION]
        policy_coverage = (len(policy_events) / len(operation_events) * 100) if operation_events else 0
        metrics.append(GovernanceMetric(
            name="策略评估覆盖率",
            value=policy_coverage,
            unit="%",
            threshold=100.0,
            status="normal" if policy_coverage >= 100 else "warning",
            description="经过策略评估的操作比例"
        ))
        
        # 2. 错误事件数
        error_events = [e for e in events if e.event_type == AuditEventType.ERROR or e.severity == AuditEventSeverity.ERROR]
        metrics.append(GovernanceMetric(
            name="错误事件数",
            value=len(error_events),
            unit="次",
            threshold=10.0,
            status="normal" if len(error_events) <= 10 else "critical",
            description=f"过去{days}天的错误事件数"
        ))
        
        # 3. 资源使用分布
        resource_types = {}
        for event in operation_events:
            rt = event.resource_type or "unknown"
            resource_types[rt] = resource_types.get(rt, 0) + 1
        
        charts = [
            {
                "type": "bar",
                "title": "资源类型使用分布",
                "data": resource_types
            },
            {
                "type": "line",
                "title": "错误事件趋势",
                "data": self._get_error_trend(error_events, days)
            }
        ]
        
        alerts = self._get_alerts(metrics, events)
        
        return DashboardView(
            role=DashboardRole.IT_ARCHITECT,
            metrics=metrics,
            charts=charts,
            alerts=alerts,
            last_updated=datetime.now()
        )
    
    def get_auditor_view(self, days: int = 30) -> DashboardView:
        """
        获取审计员视图
        
        Args:
            days: 统计天数
            
        Returns:
            DashboardView: 审计员视图
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 生成审计报告
        audit_report = self.audit_logger.generate_audit_report(
            start_time=start_time,
            end_time=end_time
        )
        
        metrics = []
        
        # 从审计报告中提取指标
        summary = audit_report.get("summary", {})
        metrics.append(GovernanceMetric(
            name="总审计事件数",
            value=summary.get("total_events", 0),
            unit="次",
            description=f"过去{days}天的总审计事件数"
        ))
        
        # 严重事件数
        critical_count = summary.get("severity_counts", {}).get("critical", 0)
        metrics.append(GovernanceMetric(
            name="严重事件数",
            value=critical_count,
            unit="次",
            threshold=0.0,
            status="normal" if critical_count == 0 else "critical",
            description="严重级别的审计事件数"
        ))
        
        charts = [
            {
                "type": "bar",
                "title": "事件类型分布",
                "data": summary.get("event_type_counts", {})
            },
            {
                "type": "pie",
                "title": "严重程度分布",
                "data": summary.get("severity_counts", {})
            }
        ]
        
        alerts = []
        if critical_count > 0:
            alerts.append({
                "level": "critical",
                "message": f"发现 {critical_count} 个严重事件，需要立即审查",
                "timestamp": datetime.now().isoformat()
            })
        
        return DashboardView(
            role=DashboardRole.AUDITOR,
            metrics=metrics,
            charts=charts,
            alerts=alerts,
            last_updated=datetime.now()
        )
    
    def _get_intent_success_trend(self, events: List, days: int) -> Dict[str, Any]:
        """获取意图识别成功率趋势"""
        # 简化实现：按天统计
        daily_stats = {}
        for event in events:
            if event.event_type == AuditEventType.INTENT_RECOGNITION:
                date_key = event.timestamp.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"total": 0, "success": 0}
                daily_stats[date_key]["total"] += 1
                if event.result == "success":
                    daily_stats[date_key]["success"] += 1
        
        # 计算成功率
        trend_data = {}
        for date_key, stats in daily_stats.items():
            success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            trend_data[date_key] = success_rate
        
        return trend_data
    
    def _get_operation_type_distribution(self, events: List) -> Dict[str, int]:
        """获取操作类型分布"""
        distribution = {}
        for event in events:
            op = event.operation or "unknown"
            distribution[op] = distribution.get(op, 0) + 1
        return distribution
    
    def _get_workflow_status_distribution(self, events: List) -> Dict[str, int]:
        """获取工作流状态分布"""
        distribution = {"success": 0, "failed": 0}
        for event in events:
            if event.result == "success":
                distribution["success"] += 1
            elif event.result == "failed":
                distribution["failed"] += 1
        return distribution
    
    def _get_error_trend(self, events: List, days: int) -> Dict[str, Any]:
        """获取错误事件趋势"""
        daily_errors = {}
        for event in events:
            date_key = event.timestamp.date().isoformat()
            daily_errors[date_key] = daily_errors.get(date_key, 0) + 1
        return daily_errors
    
    def _get_alerts(self, metrics: List[GovernanceMetric], events: List) -> List[Dict[str, Any]]:
        """获取告警列表"""
        alerts = []
        
        # 检查指标告警
        for metric in metrics:
            if metric.status == "critical":
                alerts.append({
                    "level": "critical",
                    "message": f"{metric.name} 达到临界值: {metric.value}{metric.unit}",
                    "metric": metric.name,
                    "timestamp": datetime.now().isoformat()
                })
            elif metric.status == "warning":
                alerts.append({
                    "level": "warning",
                    "message": f"{metric.name} 超过阈值: {metric.value}{metric.unit}",
                    "metric": metric.name,
                    "timestamp": datetime.now().isoformat()
                })
        
        # 检查严重事件
        critical_events = [e for e in events if e.severity == AuditEventSeverity.CRITICAL]
        if critical_events:
            alerts.append({
                "level": "critical",
                "message": f"发现 {len(critical_events)} 个严重事件",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts


"""
审计日志系统
记录所有资源操作、意图识别和执行过程
支持审计查询和报告
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """审计事件类型"""
    INTENT_RECOGNITION = "intent_recognition"  # 意图识别
    RESOURCE_OPERATION = "resource_operation"  # 资源操作
    POLICY_EVALUATION = "policy_evaluation"  # 策略评估
    WORKFLOW_EXECUTION = "workflow_execution"  # 工作流执行
    APPROVAL_REQUEST = "approval_request"  # 审批请求
    APPROVAL_RESPONSE = "approval_response"  # 审批响应
    ERROR = "error"  # 错误事件


class AuditEventSeverity(Enum):
    """审计事件严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user: str
    role: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    operation: Optional[str] = None
    intent: Optional[str] = None
    result: Optional[str] = None
    severity: AuditEventSeverity = AuditEventSeverity.INFO
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, storage_backend=None):
        """
        初始化审计日志记录器
        
        Args:
            storage_backend: 存储后端（如果为None，使用内存存储）
        """
        self.storage_backend = storage_backend
        self._events: List[AuditEvent] = []  # 内存存储（用于测试）
        self._event_counter = 0
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        self._event_counter += 1
        return f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._event_counter:06d}"
    
    def log_event(
        self,
        event_type: AuditEventType,
        user: str,
        role: str,
        severity: AuditEventSeverity = AuditEventSeverity.INFO,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        operation: Optional[str] = None,
        intent: Optional[str] = None,
        result: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录审计事件
        
        Returns:
            str: 事件ID
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            timestamp=datetime.now(),
            user=user,
            role=role,
            resource_id=resource_id,
            resource_type=resource_type,
            operation=operation,
            intent=intent,
            result=result,
            severity=severity,
            metadata=metadata or {}
        )
        
        # 存储事件
        if self.storage_backend:
            try:
                self.storage_backend.store_event(event)
            except Exception as e:
                logger.error(f"存储审计事件失败: {e}")
                # 降级到内存存储
                self._events.append(event)
        else:
            self._events.append(event)
        
        # 记录日志
        log_message = f"[审计] {event_type.value} | 用户: {user} | 角色: {role}"
        if resource_id:
            log_message += f" | 资源: {resource_id}"
        if operation:
            log_message += f" | 操作: {operation}"
        if intent:
            log_message += f" | 意图: {intent}"
        if result:
            log_message += f" | 结果: {result}"
        
        if severity == AuditEventSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == AuditEventSeverity.ERROR:
            logger.error(log_message)
        elif severity == AuditEventSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        return event.event_id
    
    def log_intent_recognition(
        self,
        user: str,
        role: str,
        intent: str,
        recognized_intent: Dict[str, Any],
        success: bool
    ) -> str:
        """记录意图识别事件"""
        return self.log_event(
            event_type=AuditEventType.INTENT_RECOGNITION,
            user=user,
            role=role,
            intent=intent,
            result="success" if success else "failed",
            metadata={
                "recognized_intent": recognized_intent,
                "success": success
            }
        )
    
    def log_resource_operation(
        self,
        user: str,
        role: str,
        resource_id: str,
        resource_type: str,
        operation: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """记录资源操作事件"""
        return self.log_event(
            event_type=AuditEventType.RESOURCE_OPERATION,
            user=user,
            role=role,
            resource_id=resource_id,
            resource_type=resource_type,
            operation=operation,
            result="success" if success else "failed",
            severity=AuditEventSeverity.ERROR if not success else AuditEventSeverity.INFO,
            metadata=metadata or {}
        )
    
    def log_policy_evaluation(
        self,
        user: str,
        role: str,
        resource_id: str,
        operation: str,
        evaluation_result: Dict[str, Any],
        allowed: bool
    ) -> str:
        """记录策略评估事件"""
        return self.log_event(
            event_type=AuditEventType.POLICY_EVALUATION,
            user=user,
            role=role,
            resource_id=resource_id,
            operation=operation,
            result="allowed" if allowed else "denied",
            metadata={
                "evaluation_result": evaluation_result,
                "allowed": allowed
            }
        )
    
    def log_workflow_execution(
        self,
        user: str,
        role: str,
        workflow_id: str,
        workflow_name: str,
        success: bool,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """记录工作流执行事件"""
        return self.log_event(
            event_type=AuditEventType.WORKFLOW_EXECUTION,
            user=user,
            role=role,
            resource_id=workflow_id,
            resource_type="workflow",
            operation="execute",
            result="success" if success else "failed",
            severity=AuditEventSeverity.ERROR if not success else AuditEventSeverity.INFO,
            metadata={
                "workflow_name": workflow_name,
                "execution_time": execution_time,
                "success": success,
                **(metadata or {})
            }
        )
    
    def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user: Optional[str] = None,
        role: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        resource_id: Optional[str] = None,
        severity: Optional[AuditEventSeverity] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        查询审计事件
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            user: 用户过滤
            role: 角色过滤
            event_type: 事件类型过滤
            resource_id: 资源ID过滤
            severity: 严重程度过滤
            limit: 返回数量限制
            
        Returns:
            List[AuditEvent]: 审计事件列表
        """
        if self.storage_backend:
            try:
                return self.storage_backend.query_events(
                    start_time=start_time,
                    end_time=end_time,
                    user=user,
                    role=role,
                    event_type=event_type,
                    resource_id=resource_id,
                    severity=severity,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"查询审计事件失败: {e}")
                return []
        
        # 内存查询
        results = self._events.copy()
        
        # 应用过滤
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        if user:
            results = [e for e in results if e.user == user]
        if role:
            results = [e for e in results if e.role == role]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        if severity:
            results = [e for e in results if e.severity == severity]
        
        # 按时间倒序排序
        results.sort(key=lambda e: e.timestamp, reverse=True)
        
        return results[:limit]
    
    def generate_audit_report(
        self,
        start_time: datetime,
        end_time: datetime,
        group_by: str = "user"  # "user" | "role" | "resource_type" | "event_type"
    ) -> Dict[str, Any]:
        """
        生成审计报告
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            group_by: 分组方式
            
        Returns:
            Dict: 审计报告
        """
        events = self.query_events(start_time=start_time, end_time=end_time, limit=10000)
        
        # 统计
        total_events = len(events)
        event_type_counts = {}
        severity_counts = {}
        user_counts = {}
        role_counts = {}
        
        for event in events:
            # 事件类型统计
            event_type_key = event.event_type.value
            event_type_counts[event_type_key] = event_type_counts.get(event_type_key, 0) + 1
            
            # 严重程度统计
            severity_key = event.severity.value
            severity_counts[severity_key] = severity_counts.get(severity_key, 0) + 1
            
            # 用户统计
            user_counts[event.user] = user_counts.get(event.user, 0) + 1
            
            # 角色统计
            role_counts[event.role] = role_counts.get(event.role, 0) + 1
        
        # 按分组方式统计
        grouped_stats = {}
        for event in events:
            if group_by == "user":
                key = event.user
            elif group_by == "role":
                key = event.role
            elif group_by == "resource_type":
                key = event.resource_type or "unknown"
            elif group_by == "event_type":
                key = event.event_type.value
            else:
                key = "all"
            
            if key not in grouped_stats:
                grouped_stats[key] = {
                    "count": 0,
                    "success_count": 0,
                    "failed_count": 0
                }
            
            grouped_stats[key]["count"] += 1
            if event.result == "success":
                grouped_stats[key]["success_count"] += 1
            elif event.result == "failed":
                grouped_stats[key]["failed_count"] += 1
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "event_type_counts": event_type_counts,
                "severity_counts": severity_counts,
                "user_counts": user_counts,
                "role_counts": role_counts
            },
            "grouped_stats": grouped_stats,
            "generated_at": datetime.now().isoformat()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_events = len(self._events) if not self.storage_backend else 0
        
        if self.storage_backend:
            try:
                return self.storage_backend.get_statistics()
            except Exception as e:
                logger.error(f"获取统计信息失败: {e}")
        
        return {
            "total_events": total_events,
            "storage_backend": "memory" if not self.storage_backend else "external"
        }


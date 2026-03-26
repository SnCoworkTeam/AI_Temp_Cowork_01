"""
行为数据收集器
记录所有意图调用、工作流执行、资源使用情况
用于自演进AIOS的数据基础
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class BehaviorEventType(Enum):
    """行为事件类型"""
    INTENT_CALL = "intent_call"  # 意图调用
    WORKFLOW_EXECUTION = "workflow_execution"  # 工作流执行
    RESOURCE_USAGE = "resource_usage"  # 资源使用
    AGENT_EXECUTION = "agent_execution"  # Agent执行
    CAPABILITY_INVOCATION = "capability_invocation"  # 能力调用


@dataclass
class IntentCallData:
    """意图调用数据"""
    intent_id: str
    user_input: str
    recognized_intent: str
    confidence: float
    execution_time: float
    success: bool
    suggested_activities: List[str]
    resource_operations: List[str]
    timestamp: datetime
    user_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionData:
    """工作流执行数据"""
    workflow_id: str
    workflow_name: str
    execution_id: str
    steps: List[Dict[str, Any]]  # 步骤详情
    total_time: float
    success: bool
    timestamp: datetime
    failure_point: Optional[str] = None
    agent_usage: List[str] = field(default_factory=list)  # 使用的Agent列表
    resource_usage: List[str] = field(default_factory=list)  # 使用的资源列表
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsageData:
    """资源使用数据"""
    resource_id: str
    resource_type: str
    operation: str
    usage_count: int
    success_count: int
    failure_count: int
    avg_execution_time: float
    last_used: datetime
    first_used: datetime
    users: List[str] = field(default_factory=list)  # 使用该资源的用户列表


class BehaviorCollector:
    """行为数据收集器"""
    
    def __init__(self, storage_backend=None):
        """
        初始化行为数据收集器
        
        Args:
            storage_backend: 存储后端（如果为None，使用内存存储）
        """
        self.storage_backend = storage_backend
        self._intent_calls: List[IntentCallData] = []
        self._workflow_executions: List[WorkflowExecutionData] = []
        self._resource_usage: Dict[str, ResourceUsageData] = {}  # {resource_id: ResourceUsageData}
        self._event_counter = 0
    
    def _generate_event_id(self) -> str:
        """生成事件ID"""
        self._event_counter += 1
        return f"behavior_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._event_counter:06d}"
    
    def collect_intent_call(
        self,
        user_input: str,
        recognized_intent: str,
        confidence: float,
        execution_time: float,
        success: bool,
        suggested_activities: List[str],
        resource_operations: List[str],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        收集意图调用数据
        
        Returns:
            str: 事件ID
        """
        intent_id = self._generate_event_id()
        
        intent_data = IntentCallData(
            intent_id=intent_id,
            user_input=user_input,
            recognized_intent=recognized_intent,
            confidence=confidence,
            execution_time=execution_time,
            success=success,
            suggested_activities=suggested_activities,
            resource_operations=resource_operations,
            timestamp=datetime.now(),
            user_id=user_id,
            context=context or {}
        )
        
        # 存储
        if self.storage_backend:
            try:
                self.storage_backend.store_intent_call(intent_data)
            except Exception as e:
                logger.error(f"存储意图调用数据失败: {e}")
                self._intent_calls.append(intent_data)
        else:
            self._intent_calls.append(intent_data)
        
        logger.debug(f"收集意图调用数据: {intent_id}")
        return intent_id
    
    def collect_workflow_execution(
        self,
        workflow_id: str,
        workflow_name: str,
        execution_id: str,
        steps: List[Dict[str, Any]],
        total_time: float,
        success: bool,
        failure_point: Optional[str] = None,
        agent_usage: Optional[List[str]] = None,
        resource_usage: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        收集工作流执行数据
        
        Returns:
            str: 事件ID
        """
        execution_data = WorkflowExecutionData(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            execution_id=execution_id,
            steps=steps,
            total_time=total_time,
            success=success,
            failure_point=failure_point,
            agent_usage=agent_usage or [],
            resource_usage=resource_usage or [],
            timestamp=datetime.now(),
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # 存储
        if self.storage_backend:
            try:
                self.storage_backend.store_workflow_execution(execution_data)
            except Exception as e:
                logger.error(f"存储工作流执行数据失败: {e}")
                self._workflow_executions.append(execution_data)
        else:
            self._workflow_executions.append(execution_data)
        
        # 更新资源使用统计
        if resource_usage:
            for resource_id in resource_usage:
                self._update_resource_usage(resource_id, "workflow_execution", success, total_time, user_id)
        
        logger.debug(f"收集工作流执行数据: {workflow_id} - {execution_id}")
        return execution_id
    
    def collect_resource_usage(
        self,
        resource_id: str,
        resource_type: str,
        operation: str,
        execution_time: float,
        success: bool,
        user_id: Optional[str] = None
    ):
        """收集资源使用数据"""
        self._update_resource_usage(resource_id, resource_type, operation, success, execution_time, user_id)
    
    def _update_resource_usage(
        self,
        resource_id: str,
        resource_type: str,
        operation: str,
        success: bool,
        execution_time: float,
        user_id: Optional[str] = None
    ):
        """更新资源使用统计"""
        if resource_id not in self._resource_usage:
            self._resource_usage[resource_id] = ResourceUsageData(
                resource_id=resource_id,
                resource_type=resource_type,
                operation=operation,
                usage_count=0,
                success_count=0,
                failure_count=0,
                avg_execution_time=0.0,
                last_used=datetime.now(),
                first_used=datetime.now()
            )
        
        usage = self._resource_usage[resource_id]
        usage.usage_count += 1
        if success:
            usage.success_count += 1
        else:
            usage.failure_count += 1
        
        # 更新平均执行时间（简化实现：移动平均）
        usage.avg_execution_time = (
            (usage.avg_execution_time * (usage.usage_count - 1) + execution_time) / usage.usage_count
        )
        
        usage.last_used = datetime.now()
        
        if user_id and user_id not in usage.users:
            usage.users.append(user_id)
    
    def get_intent_call_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        intent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取意图调用统计"""
        calls = self._intent_calls.copy()
        
        # 应用过滤
        if start_time:
            calls = [c for c in calls if c.timestamp >= start_time]
        if end_time:
            calls = [c for c in calls if c.timestamp <= end_time]
        if intent_type:
            calls = [c for c in calls if c.recognized_intent == intent_type]
        
        if not calls:
            return {
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_execution_time": 0.0
            }
        
        total_calls = len(calls)
        success_count = sum(1 for c in calls if c.success)
        avg_confidence = sum(c.confidence for c in calls) / total_calls
        avg_execution_time = sum(c.execution_time for c in calls) / total_calls
        
        return {
            "total_calls": total_calls,
            "success_rate": (success_count / total_calls * 100) if total_calls > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "avg_execution_time": avg_execution_time,
            "intent_types": {
                intent: sum(1 for c in calls if c.recognized_intent == intent)
                for intent in set(c.recognized_intent for c in calls)
            }
        }
    
    def get_workflow_performance(
        self,
        workflow_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取工作流性能数据"""
        executions = [e for e in self._workflow_executions if e.workflow_id == workflow_id]
        
        # 应用时间过滤
        if start_time:
            executions = [e for e in executions if e.timestamp >= start_time]
        if end_time:
            executions = [e for e in executions if e.timestamp <= end_time]
        
        if not executions:
            return {
                "workflow_id": workflow_id,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "failure_points": []
            }
        
        total_executions = len(executions)
        success_count = sum(1 for e in executions if e.success)
        avg_execution_time = sum(e.total_time for e in executions) / total_executions
        
        # 分析失败点
        failure_points = {}
        for e in executions:
            if not e.success and e.failure_point:
                failure_points[e.failure_point] = failure_points.get(e.failure_point, 0) + 1
        
        # 分析Agent使用情况
        agent_usage = {}
        for e in executions:
            for agent_id in e.agent_usage:
                if agent_id not in agent_usage:
                    agent_usage[agent_id] = {"count": 0, "success_count": 0}
                agent_usage[agent_id]["count"] += 1
                if e.success:
                    agent_usage[agent_id]["success_count"] += 1
        
        return {
            "workflow_id": workflow_id,
            "total_executions": total_executions,
            "success_rate": (success_count / total_executions * 100) if total_executions > 0 else 0.0,
            "avg_execution_time": avg_execution_time,
            "failure_points": failure_points,
            "agent_usage": agent_usage,
            "steps_analysis": self._analyze_workflow_steps(executions)
        }
    
    def _analyze_workflow_steps(self, executions: List[WorkflowExecutionData]) -> Dict[str, Any]:
        """分析工作流步骤"""
        step_stats = {}
        
        for execution in executions:
            for step in execution.steps:
                step_id = step.get("step_id", "unknown")
                if step_id not in step_stats:
                    step_stats[step_id] = {
                        "count": 0,
                        "total_time": 0.0,
                        "success_count": 0,
                        "failure_count": 0
                    }
                
                stats = step_stats[step_id]
                stats["count"] += 1
                stats["total_time"] += step.get("execution_time", 0.0)
                if step.get("success", False):
                    stats["success_count"] += 1
                else:
                    stats["failure_count"] += 1
        
        # 计算平均值
        for step_id, stats in step_stats.items():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["success_rate"] = (stats["success_count"] / stats["count"] * 100) if stats["count"] > 0 else 0.0
        
        return step_stats
    
    def get_resource_usage_statistics(
        self,
        resource_type: Optional[str] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """获取资源使用统计（按使用频率排序）"""
        resources = list(self._resource_usage.values())
        
        # 按资源类型过滤
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        
        # 按使用次数排序
        resources.sort(key=lambda r: r.usage_count, reverse=True)
        
        # 转换为字典
        result = []
        for resource in resources[:top_n]:
            result.append({
                "resource_id": resource.resource_id,
                "resource_type": resource.resource_type,
                "operation": resource.operation,
                "usage_count": resource.usage_count,
                "success_rate": (resource.success_count / resource.usage_count * 100) if resource.usage_count > 0 else 0.0,
                "avg_execution_time": resource.avg_execution_time,
                "last_used": resource.last_used.isoformat(),
                "unique_users": len(resource.users)
            })
        
        return result
    
    def get_unused_resources(
        self,
        days: int = 30,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取未使用的资源（超过指定天数未使用）"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=days)
        
        unused = []
        for resource_id, resource in self._resource_usage.items():
            if resource_type and resource.resource_type != resource_type:
                continue
            
            if resource.last_used < cutoff_time:
                unused.append({
                    "resource_id": resource_id,
                    "resource_type": resource.resource_type,
                    "last_used": resource.last_used.isoformat(),
                    "days_unused": (datetime.now() - resource.last_used).days
                })
        
        return sorted(unused, key=lambda x: x["days_unused"], reverse=True)
    
    def export_data(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json"  # "json" | "csv"
    ) -> str:
        """导出行为数据"""
        data = {
            "intent_calls": [
                asdict(call) for call in self._intent_calls
                if (not start_time or call.timestamp >= start_time)
                and (not end_time or call.timestamp <= end_time)
            ],
            "workflow_executions": [
                asdict(execution) for execution in self._workflow_executions
                if (not start_time or execution.timestamp >= start_time)
                and (not end_time or execution.timestamp <= end_time)
            ],
            "resource_usage": [
                asdict(usage) for usage in self._resource_usage.values()
            ]
        }
        
        # 转换datetime为字符串
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        data = convert_datetime(data)
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            # CSV格式（简化实现）
            return json.dumps(data, ensure_ascii=False)

"""
智能体通信协议设计
定义智能体与工作流引擎、智能体之间的通信机制和数据传递协议
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union, Literal
from datetime import datetime
from enum import Enum
import uuid

# ==================== 通信协议基础类型 ====================

class MessageType(str, Enum):
    """消息类型枚举"""
    # 控制消息
    EXECUTION_START = "execution_start"           # 开始执行
    EXECUTION_COMPLETE = "execution_complete"     # 执行完成
    EXECUTION_FAILED = "execution_failed"         # 执行失败
    EXECUTION_TIMEOUT = "execution_timeout"       # 执行超时
    EXECUTION_CANCEL = "execution_cancel"         # 取消执行

    # 数据传递消息
    DATA_TRANSFER = "data_transfer"               # 数据传递
    CONTEXT_UPDATE = "context_update"             # 上下文更新
    STATE_SYNC = "state_sync"                     # 状态同步

    # 协调消息
    COORDINATION_REQUEST = "coordination_request" # 协调请求
    COORDINATION_RESPONSE = "coordination_response" # 协调响应
    DEPENDENCY_NOTIFY = "dependency_notify"       # 依赖通知

    # 监控消息
    HEALTH_CHECK = "health_check"                 # 健康检查
    METRICS_REPORT = "metrics_report"             # 指标报告
    LOG_ENTRY = "log_entry"                       # 日志条目

    # 调试消息
    DEBUG_TRACE = "debug_trace"                   # 调试跟踪
    BREAKPOINT = "breakpoint"                     # 断点消息


class MessagePriority(str, Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageDeliveryMode(str, Enum):
    """消息传递模式"""
    DIRECT = "direct"           # 直接传递
    ASYNC = "async"             # 异步传递
    BROADCAST = "broadcast"     # 广播传递
    MULTICAST = "multicast"     # 组播传递


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"   # 串行执行
    PARALLEL = "parallel"       # 并行执行
    PIPELINE = "pipeline"       # 流水线执行
    CONDITIONAL = "conditional" # 条件执行


# ==================== 核心通信消息模型 ====================

class MessageHeader(BaseModel):
    """消息头"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息ID")
    correlation_id: Optional[str] = Field(None, description="关联消息ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    message_type: MessageType = Field(..., description="消息类型")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="消息优先级")
    delivery_mode: MessageDeliveryMode = Field(default=MessageDeliveryMode.DIRECT, description="传递模式")
    ttl: Optional[int] = Field(None, description="消息生存时间(秒)")
    retry_count: int = Field(default=0, description="重试次数")
    source: str = Field(..., description="消息源")
    destination: Optional[str] = Field(None, description="消息目标")
    workflow_id: Optional[str] = Field(None, description="工作流ID")
    execution_id: Optional[str] = Field(None, description="执行ID")
    trace_id: Optional[str] = Field(None, description="链路跟踪ID")


class MessagePayload(BaseModel):
    """消息负载基类"""
    data: Dict[str, Any] = Field(default_factory=dict, description="消息数据")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class AgentMessage(BaseModel):
    """智能体通信消息"""
    header: MessageHeader = Field(..., description="消息头")
    payload: MessagePayload = Field(..., description="消息负载")


# ==================== 执行控制消息 ====================

class ExecutionStartMessage(MessagePayload):
    """执行开始消息"""
    agent_id: str = Field(..., description="智能体ID")
    node_id: str = Field(..., description="节点ID")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    execution_config: Dict[str, Any] = Field(default_factory=dict, description="执行配置")
    dependencies: List[str] = Field(default_factory=list, description="依赖节点列表")


class ExecutionCompleteMessage(MessagePayload):
    """执行完成消息"""
    agent_id: str = Field(..., description="智能体ID")
    node_id: str = Field(..., description="节点ID")
    output_data: Dict[str, Any] = Field(..., description="输出数据")
    execution_time: float = Field(..., description="执行时间(秒)")
    tokens_used: int = Field(default=0, description="消耗的token数")
    success: bool = Field(..., description="是否成功")


class ExecutionFailedMessage(MessagePayload):
    """执行失败消息"""
    agent_id: str = Field(..., description="智能体ID")
    node_id: str = Field(..., description="节点ID")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误信息")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="错误详情")
    is_retryable: bool = Field(default=False, description="是否可重试")


# ==================== 数据传递消息 ====================

class DataTransferMessage(MessagePayload):
    """数据传递消息"""
    from_node: str = Field(..., description="源节点ID")
    to_node: str = Field(..., description="目标节点ID")
    data_type: str = Field(..., description="数据类型")
    data_content: Dict[str, Any] = Field(..., description="数据内容")
    data_schema: Optional[Dict[str, Any]] = Field(None, description="数据Schema")
    compression: Optional[str] = Field(None, description="压缩方式")
    encryption: Optional[str] = Field(None, description="加密方式")


class ContextUpdateMessage(MessagePayload):
    """上下文更新消息"""
    context_id: str = Field(..., description="上下文ID")
    update_type: Literal["partial", "full", "merge"] = Field(..., description="更新类型")
    context_data: Dict[str, Any] = Field(..., description="上下文数据")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量更新")
    shared_memory: Dict[str, Any] = Field(default_factory=dict, description="共享内存更新")


class StateSyncMessage(MessagePayload):
    """状态同步消息"""
    node_id: str = Field(..., description="节点ID")
    state_type: Literal["execution", "data", "context"] = Field(..., description="状态类型")
    current_state: Dict[str, Any] = Field(..., description="当前状态")
    state_version: int = Field(..., description="状态版本")
    sync_timestamp: datetime = Field(default_factory=datetime.now, description="同步时间")


# ==================== 协调控制消息 ====================

class CoordinationRequest(MessagePayload):
    """协调请求消息"""
    request_type: Literal["dependency_check", "resource_allocation", "execution_order"] = Field(..., description="请求类型")
    requesting_node: str = Field(..., description="请求节点ID")
    target_nodes: List[str] = Field(..., description="目标节点列表")
    coordination_data: Dict[str, Any] = Field(default_factory=dict, description="协调数据")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")


class CoordinationResponse(MessagePayload):
    """协调响应消息"""
    request_id: str = Field(..., description="请求ID")
    responding_node: str = Field(..., description="响应节点ID")
    response_type: Literal["accept", "reject", "defer"] = Field(..., description="响应类型")
    response_data: Dict[str, Any] = Field(default_factory=dict, description="响应数据")
    reason: Optional[str] = Field(None, description="响应原因")


class DependencyNotifyMessage(MessagePayload):
    """依赖通知消息"""
    dependent_node: str = Field(..., description="依赖节点ID")
    dependency_node: str = Field(..., description="被依赖节点ID")
    dependency_type: Literal["data", "execution", "state"] = Field(..., description="依赖类型")
    status: Literal["satisfied", "pending", "failed"] = Field(..., description="依赖状态")
    dependency_data: Optional[Dict[str, Any]] = Field(None, description="依赖数据")


# ==================== 监控和调试消息 ====================

class HealthCheckMessage(MessagePayload):
    """健康检查消息"""
    component_id: str = Field(..., description="组件ID")
    component_type: Literal["agent", "node", "workflow", "engine"] = Field(..., description="组件类型")
    health_status: Literal["healthy", "warning", "critical", "unknown"] = Field(..., description="健康状态")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="健康指标")
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")


class MetricsReportMessage(MessagePayload):
    """指标报告消息"""
    component_id: str = Field(..., description="组件ID")
    metrics_type: Literal["performance", "resource", "business"] = Field(..., description="指标类型")
    time_window: Dict[str, datetime] = Field(..., description="时间窗口")
    metrics_data: Dict[str, Union[int, float, str]] = Field(..., description="指标数据")
    aggregation_level: Literal["instant", "minute", "hour", "day"] = Field(..., description="聚合级别")


class LogEntryMessage(MessagePayload):
    """日志条目消息"""
    component_id: str = Field(..., description="组件ID")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    category: Optional[str] = Field(None, description="日志分类")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="额外数据")


class DebugTraceMessage(MessagePayload):
    """调试跟踪消息"""
    trace_point: str = Field(..., description="跟踪点")
    node_id: str = Field(..., description="节点ID")
    execution_context: Dict[str, Any] = Field(..., description="执行上下文")
    variables_snapshot: Dict[str, Any] = Field(default_factory=dict, description="变量快照")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")


# ==================== 通信路由配置 ====================

class RoutingRule(BaseModel):
    """路由规则"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="规则ID")
    name: str = Field(..., description="规则名称")
    priority: int = Field(default=100, description="规则优先级")
    enabled: bool = Field(default=True, description="是否启用")

    # 匹配条件
    message_type: Optional[MessageType] = Field(None, description="消息类型匹配")
    source_pattern: Optional[str] = Field(None, description="源匹配模式")
    destination_pattern: Optional[str] = Field(None, description="目标匹配模式")
    workflow_id: Optional[str] = Field(None, description="工作流ID匹配")

    # 路由动作
    target_nodes: List[str] = Field(default_factory=list, description="目标节点列表")
    delivery_mode: MessageDeliveryMode = Field(default=MessageDeliveryMode.DIRECT, description="传递模式")
    transform_rules: List[Dict[str, Any]] = Field(default_factory=list, description="转换规则")

    # 可选配置
    timeout: Optional[int] = Field(None, description="超时时间")
    retry_count: int = Field(default=0, description="重试次数")
    dead_letter_queue: Optional[str] = Field(None, description="死信队列")


class MessageQueue(BaseModel):
    """消息队列配置"""
    queue_id: str = Field(..., description="队列ID")
    queue_name: str = Field(..., description="队列名称")
    queue_type: Literal["fifo", "priority", "topic", "direct"] = Field(..., description="队列类型")
    max_size: int = Field(default=10000, description="最大队列长度")
    ttl: Optional[int] = Field(None, description="消息TTL")
    dead_letter_queue: Optional[str] = Field(None, description="死信队列")
    persistence: bool = Field(default=False, description="是否持久化")


# ==================== 执行协调模型 ====================

class ExecutionPlan(BaseModel):
    """执行计划"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="计划ID")
    workflow_id: str = Field(..., description="工作流ID")
    execution_mode: ExecutionMode = Field(..., description="执行模式")
    node_dependencies: Dict[str, List[str]] = Field(..., description="节点依赖关系")
    execution_order: List[str] = Field(..., description="执行顺序")
    parallel_groups: List[List[str]] = Field(default_factory=list, description="并行执行组")
    estimated_duration: Optional[float] = Field(None, description="预估执行时间")


class CoordinationState(BaseModel):
    """协调状态"""
    execution_id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    current_stage: str = Field(..., description="当前阶段")
    completed_nodes: List[str] = Field(default_factory=list, description="已完成节点")
    running_nodes: List[str] = Field(default_factory=list, description="运行中节点")
    pending_nodes: List[str] = Field(default_factory=list, description="等待中节点")
    failed_nodes: List[str] = Field(default_factory=list, description="失败节点")
    blocked_dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="阻塞的依赖")
    global_context: Dict[str, Any] = Field(default_factory=dict, description="全局上下文")


class SynchronizationPoint(BaseModel):
    """同步点"""
    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="同步点ID")
    sync_type: Literal["barrier", "checkpoint", "milestone"] = Field(..., description="同步类型")
    waiting_nodes: List[str] = Field(default_factory=list, description="等待节点")
    required_nodes: List[str] = Field(..., description="必需节点")
    sync_data: Dict[str, Any] = Field(default_factory=dict, description="同步数据")
    timeout: Optional[int] = Field(None, description="同步超时")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


# ==================== 通信性能监控 ====================

class CommunicationMetrics(BaseModel):
    """通信性能指标"""
    time_window: Dict[str, datetime] = Field(..., description="时间窗口")
    message_count: int = Field(default=0, description="消息总数")
    message_size_total: int = Field(default=0, description="消息总大小(字节)")
    message_size_avg: float = Field(default=0.0, description="平均消息大小")
    delivery_success_rate: float = Field(default=0.0, description="传递成功率")
    delivery_latency_avg: float = Field(default=0.0, description="平均传递延迟(ms)")
    delivery_latency_p95: float = Field(default=0.0, description="95%分位延迟")
    retry_count: int = Field(default=0, description="重试次数")
    error_count: int = Field(default=0, description="错误次数")
    queue_depth_max: int = Field(default=0, description="最大队列深度")
    throughput_per_second: float = Field(default=0.0, description="每秒吞吐量")


# ==================== 消息路由器接口 ====================

class MessageRouter(BaseModel):
    """消息路由器接口"""
    router_id: str = Field(..., description="路由器ID")
    routing_rules: List[RoutingRule] = Field(default_factory=list, description="路由规则")
    message_queues: Dict[str, MessageQueue] = Field(default_factory=dict, description="消息队列")
    active_routes: Dict[str, List[str]] = Field(default_factory=dict, description="活跃路由")
    performance_metrics: Optional[CommunicationMetrics] = Field(None, description="性能指标")


# ==================== 通信协议配置 ====================

class CommunicationProtocolConfig(BaseModel):
    """通信协议配置"""
    protocol_version: str = Field(default="1.0", description="协议版本")
    default_timeout: int = Field(default=30, description="默认超时时间(秒)")
    max_retry_count: int = Field(default=3, description="最大重试次数")
    message_compression: bool = Field(default=False, description="消息压缩")
    message_encryption: bool = Field(default=False, description="消息加密")
    batch_processing: bool = Field(default=True, description="批量处理")
    batch_size: int = Field(default=100, description="批处理大小")
    heartbeat_interval: int = Field(default=30, description="心跳间隔(秒)")
    connection_pool_size: int = Field(default=10, description="连接池大小")
    circuit_breaker: bool = Field(default=True, description="熔断器启用")
    rate_limiting: bool = Field(default=True, description="限流启用")
    monitoring_enabled: bool = Field(default=True, description="监控启用")


# ==================== 调试和诊断工具 ====================

class CommunicationDiagnostics(BaseModel):
    """通信诊断信息"""
    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="执行ID")
    message_flow: List[Dict[str, Any]] = Field(default_factory=list, description="消息流")
    routing_decisions: List[Dict[str, Any]] = Field(default_factory=list, description="路由决策")
    performance_bottlenecks: List[Dict[str, Any]] = Field(default_factory=list, description="性能瓶颈")
    error_analysis: List[Dict[str, Any]] = Field(default_factory=list, description="错误分析")
    recommendations: List[str] = Field(default_factory=list, description="优化建议")


# ==================== 使用示例 ====================

COMMUNICATION_EXAMPLES = {
    "execution_start": AgentMessage(
        header=MessageHeader(
            message_type=MessageType.EXECUTION_START,
            source="workflow_engine",
            destination="agent_node_123",
            workflow_id="workflow_456",
            execution_id="exec_789"
        ),
        payload=ExecutionStartMessage(
            agent_id="agent_123",
            node_id="node_456",
            input_data={"query": "用户问题", "context": {}},
            execution_config={"timeout": 60, "streaming": True}
        )
    ),

    "data_transfer": AgentMessage(
        header=MessageHeader(
            message_type=MessageType.DATA_TRANSFER,
            source="node_123",
            destination="node_456"
        ),
        payload=DataTransferMessage(
            from_node="node_123",
            to_node="node_456",
            data_type="text/json",
            data_content={"result": "处理结果", "metadata": {}},
            data_schema={"type": "object", "properties": {}}
        )
    )
}
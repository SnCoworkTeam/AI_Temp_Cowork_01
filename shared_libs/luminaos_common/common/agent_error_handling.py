"""
智能体节点架构错误处理规范
定义完整的错误处理体系，包括错误类型、代码、响应格式和处理策略
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# ==================== 错误分类和代码 ====================

class AgentErrorCategory(str, Enum):
    """智能体错误分类"""
    VALIDATION = "validation"           # 验证错误
    AUTHENTICATION = "authentication"   # 认证错误
    AUTHORIZATION = "authorization"     # 授权错误
    NOT_FOUND = "not_found"            # 资源不存在
    CONFIGURATION = "configuration"     # 配置错误
    EXECUTION = "execution"            # 执行错误
    AI_MODEL = "ai_model"              # AI模型错误
    TIMEOUT = "timeout"                # 超时错误
    RATE_LIMIT = "rate_limit"          # 限流错误
    DEPENDENCY = "dependency"          # 依赖服务错误
    INTERNAL = "internal"              # 内部系统错误
    WORKFLOW = "workflow"              # 工作流错误
    CONTEXT = "context"                # 上下文错误


class AgentErrorCode(str, Enum):
    """智能体错误代码"""
    # 验证错误 (1000-1099)
    INVALID_INPUT = "AGENT_1001"
    INVALID_CONFIGURATION = "AGENT_1002"
    INVALID_PROMPT = "AGENT_1003"
    INVALID_PARAMETERS = "AGENT_1004"
    SCHEMA_VALIDATION_FAILED = "AGENT_1005"
    REQUIRED_FIELD_MISSING = "AGENT_1006"
    INVALID_ENUM_VALUE = "AGENT_1007"
    INVALID_JSON_FORMAT = "AGENT_1008"
    INVALID_NODE_CONFIGURATION = "AGENT_1009"

    # 认证错误 (1100-1199)
    AUTHENTICATION_FAILED = "AGENT_1101"
    INVALID_TOKEN = "AGENT_1102"
    TOKEN_EXPIRED = "AGENT_1103"
    CREDENTIALS_MISSING = "AGENT_1104"

    # 授权错误 (1200-1299)
    INSUFFICIENT_PERMISSIONS = "AGENT_1201"
    AGENT_ACCESS_DENIED = "AGENT_1202"
    OPERATION_NOT_ALLOWED = "AGENT_1203"
    RESOURCE_FORBIDDEN = "AGENT_1204"

    # 资源不存在 (1300-1399)
    AGENT_NOT_FOUND = "AGENT_1301"
    NODE_NOT_FOUND = "AGENT_1302"
    WORKFLOW_NOT_FOUND = "AGENT_1303"
    EXECUTION_NOT_FOUND = "AGENT_1304"
    CONTEXT_NOT_FOUND = "AGENT_1305"
    MODEL_NOT_FOUND = "AGENT_1306"

    # 配置错误 (1400-1499)
    AGENT_NOT_CONFIGURED = "AGENT_1401"
    MODEL_NOT_CONFIGURED = "AGENT_1402"
    TOOLS_NOT_CONFIGURED = "AGENT_1403"
    INVALID_MODEL_PARAMETERS = "AGENT_1404"
    MISSING_SYSTEM_PROMPT = "AGENT_1405"
    CAPABILITY_NOT_CONFIGURED = "AGENT_1406"

    # 执行错误 (1500-1599)
    EXECUTION_FAILED = "AGENT_1501"
    AGENT_EXECUTION_TIMEOUT = "AGENT_1502"
    MAX_RETRIES_EXCEEDED = "AGENT_1503"
    EXECUTION_CANCELLED = "AGENT_1504"
    EXECUTION_REJECTED = "AGENT_1505"
    NODE_EXECUTION_FAILED = "AGENT_1506"
    CONTEXT_EXECUTION_FAILED = "AGENT_1507"

    # AI模型错误 (1600-1699)
    AI_MODEL_ERROR = "AGENT_1601"
    AI_MODEL_UNAVAILABLE = "AGENT_1602"
    AI_RESPONSE_INVALID = "AGENT_1603"
    AI_TOKEN_LIMIT_EXCEEDED = "AGENT_1604"
    AI_CONTENT_FILTERED = "AGENT_1605"
    AI_MODEL_OVERLOADED = "AGENT_1606"
    AI_API_KEY_INVALID = "AGENT_1607"
    AI_QUOTA_EXCEEDED = "AGENT_1608"

    # 超时错误 (1700-1799)
    EXECUTION_TIMEOUT = "AGENT_1701"
    RESPONSE_TIMEOUT = "AGENT_1702"
    CONNECTION_TIMEOUT = "AGENT_1703"
    AI_MODEL_TIMEOUT = "AGENT_1704"

    # 限流错误 (1800-1899)
    RATE_LIMIT_EXCEEDED = "AGENT_1801"
    EXECUTION_RATE_LIMITED = "AGENT_1802"
    API_RATE_LIMITED = "AGENT_1803"
    USER_RATE_LIMITED = "AGENT_1804"

    # 依赖服务错误 (1900-1999)
    DATABASE_ERROR = "AGENT_1901"
    WORKFLOW_ENGINE_ERROR = "AGENT_1902"
    KNOWLEDGE_BASE_ERROR = "AGENT_1903"
    EXTERNAL_SERVICE_ERROR = "AGENT_1904"
    NETWORK_ERROR = "AGENT_1905"

    # 内部系统错误 (2000-2099)
    INTERNAL_ERROR = "AGENT_2001"
    MEMORY_ERROR = "AGENT_2002"
    SERIALIZATION_ERROR = "AGENT_2003"
    INITIALIZATION_ERROR = "AGENT_2004"
    RESOURCE_EXHAUSTED = "AGENT_2005"

    # 工作流错误 (2100-2199)
    WORKFLOW_VALIDATION_FAILED = "AGENT_2101"
    WORKFLOW_EXECUTION_FAILED = "AGENT_2102"
    NODE_CONNECTION_ERROR = "AGENT_2103"
    WORKFLOW_STATE_ERROR = "AGENT_2104"
    WORKFLOW_VERSION_MISMATCH = "AGENT_2105"

    # 上下文错误 (2200-2299)
    CONTEXT_INVALID = "AGENT_2201"
    CONTEXT_EXPIRED = "AGENT_2202"
    CONTEXT_SIZE_EXCEEDED = "AGENT_2203"
    CONVERSATION_STATE_ERROR = "AGENT_2204"
    MEMORY_CONTEXT_ERROR = "AGENT_2205"


# ==================== 错误响应模型 ====================

class AgentErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(None, description="出错字段")
    message: str = Field(..., description="错误信息")
    code: Optional[str] = Field(None, description="字段错误代码")
    value: Optional[Any] = Field(None, description="引起错误的值")


class AgentErrorResponse(BaseModel):
    """智能体错误响应格式"""
    success: bool = Field(False, description="操作是否成功")
    error_code: AgentErrorCode = Field(..., description="错误代码")
    error_category: AgentErrorCategory = Field(..., description="错误分类")
    message: str = Field(..., description="错误消息")
    details: List[AgentErrorDetail] = Field(default_factory=list, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")
    request_id: Optional[str] = Field(None, description="请求ID")
    agent_id: Optional[str] = Field(None, description="相关智能体ID")
    execution_id: Optional[str] = Field(None, description="相关执行ID")
    trace_id: Optional[str] = Field(None, description="链路追踪ID")
    suggestions: List[str] = Field(default_factory=list, description="修复建议")


class AgentExecutionError(BaseModel):
    """智能体执行错误"""
    execution_id: str = Field(..., description="执行ID")
    agent_id: str = Field(..., description="智能体ID")
    node_id: Optional[str] = Field(None, description="节点ID")
    error_code: AgentErrorCode = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    retry_count: int = Field(default=0, description="重试次数")
    is_retryable: bool = Field(default=False, description="是否可重试")


# ==================== 错误处理策略 ====================

class ErrorHandlingStrategy(str, Enum):
    """错误处理策略"""
    FAIL_FAST = "fail_fast"           # 立即失败
    RETRY = "retry"                   # 重试
    FALLBACK = "fallback"             # 降级处理
    IGNORE = "ignore"                 # 忽略错误
    CIRCUIT_BREAKER = "circuit_breaker" # 熔断器
    GRACEFUL_DEGRADATION = "graceful_degradation" # 优雅降级


class RetryPolicy(BaseModel):
    """重试策略"""
    enabled: bool = Field(default=False, description="是否启用重试")
    max_attempts: int = Field(default=3, ge=1, le=10, description="最大重试次数")
    initial_delay: float = Field(default=1.0, ge=0.1, description="初始延迟(秒)")
    max_delay: float = Field(default=60.0, ge=1.0, description="最大延迟(秒)")
    backoff_multiplier: float = Field(default=2.0, ge=1.0, description="退避倍数")
    jitter: bool = Field(default=True, description="是否添加随机抖动")
    retryable_errors: List[AgentErrorCode] = Field(default_factory=list, description="可重试的错误代码")


class FallbackPolicy(BaseModel):
    """降级策略"""
    enabled: bool = Field(default=False, description="是否启用降级")
    fallback_agent_id: Optional[str] = Field(None, description="降级智能体ID")
    fallback_response: Optional[str] = Field(None, description="降级响应内容")
    timeout_threshold: float = Field(default=30.0, description="超时阈值(秒)")
    error_threshold: int = Field(default=5, description="错误次数阈值")
    trigger_errors: List[AgentErrorCode] = Field(default_factory=list, description="触发降级的错误")


# ==================== 错误监控和告警 ====================

class AgentErrorMetrics(BaseModel):
    """智能体错误指标"""
    agent_id: str = Field(..., description="智能体ID")
    time_window: str = Field(..., description="时间窗口")
    total_executions: int = Field(..., description="总执行次数")
    error_count: int = Field(..., description="错误次数")
    error_rate: float = Field(..., description="错误率")
    error_distribution: Dict[str, int] = Field(..., description="错误分布")
    avg_recovery_time: float = Field(..., description="平均恢复时间(秒)")
    most_frequent_errors: List[Dict[str, Any]] = Field(..., description="最常见错误")


class AlertRule(BaseModel):
    """告警规则"""
    name: str = Field(..., description="规则名称")
    condition: str = Field(..., description="告警条件")
    threshold: float = Field(..., description="阈值")
    time_window: int = Field(..., description="时间窗口(分钟)")
    severity: str = Field(..., description="严重程度", pattern="^(low|medium|high|critical)$")
    enabled: bool = Field(default=True, description="是否启用")
    recipients: List[str] = Field(..., description="通知接收者")


# ==================== 错误处理器实现 ====================

ERROR_CODE_MAPPING = {
    # 错误代码到HTTP状态码的映射
    AgentErrorCode.INVALID_INPUT: 400,
    AgentErrorCode.INVALID_CONFIGURATION: 400,
    AgentErrorCode.AUTHENTICATION_FAILED: 401,
    AgentErrorCode.INSUFFICIENT_PERMISSIONS: 403,
    AgentErrorCode.AGENT_NOT_FOUND: 404,
    AgentErrorCode.EXECUTION_TIMEOUT: 408,
    AgentErrorCode.EXECUTION_FAILED: 422,
    AgentErrorCode.RATE_LIMIT_EXCEEDED: 429,
    AgentErrorCode.AI_MODEL_ERROR: 502,
    AgentErrorCode.DATABASE_ERROR: 503,
    AgentErrorCode.INTERNAL_ERROR: 500,
}

ERROR_RETRY_POLICIES = {
    # 不同错误类型的默认重试策略
    AgentErrorCode.AI_MODEL_TIMEOUT: RetryPolicy(
        enabled=True,
        max_attempts=3,
        initial_delay=2.0,
        backoff_multiplier=2.0
    ),
    AgentErrorCode.DATABASE_ERROR: RetryPolicy(
        enabled=True,
        max_attempts=5,
        initial_delay=1.0,
        backoff_multiplier=1.5
    ),
    AgentErrorCode.NETWORK_ERROR: RetryPolicy(
        enabled=True,
        max_attempts=3,
        initial_delay=1.0,
        backoff_multiplier=2.0
    ),
    AgentErrorCode.AI_MODEL_OVERLOADED: RetryPolicy(
        enabled=True,
        max_attempts=2,
        initial_delay=5.0,
        backoff_multiplier=3.0
    ),
}

ERROR_FALLBACK_POLICIES = {
    # 不同错误类型的降级策略
    AgentErrorCode.AI_MODEL_UNAVAILABLE: FallbackPolicy(
        enabled=True,
        fallback_response="智能体暂时不可用，请稍后再试",
        timeout_threshold=30.0
    ),
    AgentErrorCode.EXECUTION_TIMEOUT: FallbackPolicy(
        enabled=True,
        fallback_response="处理超时，已自动终止",
        timeout_threshold=60.0
    ),
}

# ==================== 错误处理辅助函数 ====================

def get_error_category(error_code: AgentErrorCode) -> AgentErrorCategory:
    """根据错误代码获取错误分类"""
    code_value = int(error_code.value.split('_')[1])

    if 1000 <= code_value < 1100:
        return AgentErrorCategory.VALIDATION
    elif 1100 <= code_value < 1200:
        return AgentErrorCategory.AUTHENTICATION
    elif 1200 <= code_value < 1300:
        return AgentErrorCategory.AUTHORIZATION
    elif 1300 <= code_value < 1400:
        return AgentErrorCategory.NOT_FOUND
    elif 1400 <= code_value < 1500:
        return AgentErrorCategory.CONFIGURATION
    elif 1500 <= code_value < 1600:
        return AgentErrorCategory.EXECUTION
    elif 1600 <= code_value < 1700:
        return AgentErrorCategory.AI_MODEL
    elif 1700 <= code_value < 1800:
        return AgentErrorCategory.TIMEOUT
    elif 1800 <= code_value < 1900:
        return AgentErrorCategory.RATE_LIMIT
    elif 1900 <= code_value < 2000:
        return AgentErrorCategory.DEPENDENCY
    elif 2000 <= code_value < 2100:
        return AgentErrorCategory.INTERNAL
    elif 2100 <= code_value < 2200:
        return AgentErrorCategory.WORKFLOW
    elif 2200 <= code_value < 2300:
        return AgentErrorCategory.CONTEXT
    else:
        return AgentErrorCategory.INTERNAL


def get_http_status_code(error_code: AgentErrorCode) -> int:
    """根据错误代码获取HTTP状态码"""
    return ERROR_CODE_MAPPING.get(error_code, 500)


def is_retryable_error(error_code: AgentErrorCode) -> bool:
    """判断错误是否可重试"""
    retryable_errors = {
        AgentErrorCode.AI_MODEL_TIMEOUT,
        AgentErrorCode.DATABASE_ERROR,
        AgentErrorCode.NETWORK_ERROR,
        AgentErrorCode.AI_MODEL_OVERLOADED,
        AgentErrorCode.EXECUTION_TIMEOUT,
        AgentErrorCode.EXTERNAL_SERVICE_ERROR,
        AgentErrorCode.RESPONSE_TIMEOUT,
        AgentErrorCode.CONNECTION_TIMEOUT,
    }
    return error_code in retryable_errors


def get_error_suggestions(error_code: AgentErrorCode) -> List[str]:
    """获取错误修复建议"""
    suggestions_map = {
        AgentErrorCode.INVALID_INPUT: [
            "检查输入数据格式",
            "验证必填字段是否完整",
            "确认数据类型正确"
        ],
        AgentErrorCode.AGENT_NOT_FOUND: [
            "检查智能体ID是否正确",
            "确认智能体是否已创建",
            "验证智能体状态是否正常"
        ],
        AgentErrorCode.AI_MODEL_ERROR: [
            "检查AI模型配置",
            "验证API密钥是否有效",
            "确认模型服务是否可用"
        ],
        AgentErrorCode.EXECUTION_TIMEOUT: [
            "增加超时时间配置",
            "优化智能体提示词",
            "检查网络连接状态"
        ],
        AgentErrorCode.RATE_LIMIT_EXCEEDED: [
            "降低请求频率",
            "实现请求队列机制",
            "升级API配额"
        ],
    }
    return suggestions_map.get(error_code, ["联系技术支持获取帮助"])


# ==================== 使用示例 ====================

AGENT_ERROR_EXAMPLES = {
    "validation_error": AgentErrorResponse(
        error_code=AgentErrorCode.INVALID_INPUT,
        error_category=AgentErrorCategory.VALIDATION,
        message="输入数据验证失败",
        details=[
            AgentErrorDetail(
                field="content",
                message="内容不能为空",
                code="REQUIRED_FIELD"
            )
        ],
        suggestions=["请检查输入的content字段", "确保提供有效的输入内容"]
    ),

    "execution_error": AgentErrorResponse(
        error_code=AgentErrorCode.EXECUTION_FAILED,
        error_category=AgentErrorCategory.EXECUTION,
        message="智能体执行失败",
        agent_id="agent_123",
        execution_id="exec_456",
        details=[
            AgentErrorDetail(
                message="AI模型返回无效响应",
                code="AI_RESPONSE_INVALID"
            )
        ],
        suggestions=["检查AI模型配置", "重试执行", "联系技术支持"]
    ),

    "timeout_error": AgentErrorResponse(
        error_code=AgentErrorCode.EXECUTION_TIMEOUT,
        error_category=AgentErrorCategory.TIMEOUT,
        message="智能体执行超时",
        agent_id="agent_123",
        suggestions=["增加超时配置", "优化提示词长度", "检查网络连接"]
    )
}


# ==================== 错误处理最佳实践 ====================

BEST_PRACTICES = """
智能体错误处理最佳实践:

1. 错误预防:
   - 在输入层进行严格的数据验证
   - 实施配置检查和健康检查
   - 设置合理的超时和限流策略

2. 错误捕获:
   - 使用结构化的错误代码体系
   - 记录完整的错误上下文信息
   - 实现链路追踪和监控

3. 错误恢复:
   - 实施智能重试机制
   - 提供降级和兜底方案
   - 支持熔断器模式

4. 错误通知:
   - 实现分级告警机制
   - 提供清晰的错误信息和修复建议
   - 建立错误处理文档和知识库

5. 错误分析:
   - 定期分析错误模式和趋势
   - 优化错误处理策略
   - 持续改进系统稳定性
"""
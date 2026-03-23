"""
智能体节点架构 - 数据模型设计
智能体作为工作流节点的完整数据模型定义
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import uuid

# ==================== 基础枚举定义 ====================

class AgentType(str, Enum):
    """智能体类型"""
    CONVERSATIONAL = "conversational"      # 对话型智能体
    TOOL_CALLING = "tool_calling"         # 工具调用智能体
    REASONING = "reasoning"               # 推理智能体
    PLANNING = "planning"                 # 规划智能体
    CODE_GENERATION = "code_generation"   # 代码生成智能体
    DATA_ANALYSIS = "data_analysis"       # 数据分析智能体
    DOCUMENT_PROCESSING = "document_processing" # 文档处理智能体

class AgentStatus(str, Enum):
    """智能体状态"""
    ACTIVE = "active"                     # 激活状态
    INACTIVE = "inactive"                 # 未激活状态
    TRAINING = "training"                 # 训练中
    DEPRECATED = "deprecated"             # 已弃用
    FAILED = "failed"                     # 失败状态

class AgentExecutionState(str, Enum):
    """智能体执行状态"""
    PENDING = "pending"                   # 等待执行
    RUNNING = "running"                   # 执行中
    THINKING = "thinking"                 # 思考中
    CALLING_TOOLS = "calling_tools"       # 调用工具
    WAITING_FOR_INPUT = "waiting_for_input" # 等待输入
    COMPLETED = "completed"               # 执行完成
    FAILED = "failed"                     # 执行失败
    TIMEOUT = "timeout"                   # 超时
    CANCELLED = "cancelled"               # 已取消

class ConversationRole(str, Enum):
    """对话角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

# ==================== 智能体核心模型 ====================

class AgentCapability(BaseModel):
    """智能体能力定义"""
    name: str = Field(..., description="能力名称")
    description: str = Field(..., description="能力描述")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="输入数据Schema")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="输出数据Schema")
    required_tools: List[str] = Field(default_factory=list, description="所需工具列表")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")

class AgentPersonality(BaseModel):
    """智能体人格设定"""
    name: str = Field(..., description="人格名称")
    description: str = Field(..., description="人格描述")
    traits: List[str] = Field(default_factory=list, description="人格特征")
    communication_style: str = Field(default="professional", description="沟通风格")
    expertise_areas: List[str] = Field(default_factory=list, description="专业领域")
    limitations: List[str] = Field(default_factory=list, description="能力限制")

class AgentConfiguration(BaseModel):
    """智能体配置"""
    model: str = Field(..., description="使用的模型", example="gpt-4")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="创造性参数")
    max_tokens: int = Field(default=2048, ge=1, le=32000, description="最大token数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核心采样参数")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: int = Field(default=300, ge=1, le=3600, description="执行超时时间(秒)")
    max_tool_calls: int = Field(default=10, ge=1, le=100, description="最大工具调用次数")
    enable_memory: bool = Field(default=True, description="是否启用记忆")
    memory_size: int = Field(default=20, ge=1, le=1000, description="记忆条目数量")

class AgentRegistry(BaseModel):
    """智能体注册表"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="智能体ID")
    name: str = Field(..., description="智能体名称", min_length=1, max_length=100)
    display_name: str = Field(..., description="显示名称", min_length=1, max_length=200)
    description: str = Field(..., description="智能体描述", max_length=2000)
    agent_type: AgentType = Field(..., description="智能体类型")
    status: AgentStatus = Field(default=AgentStatus.INACTIVE, description="智能体状态")
    version: str = Field(default="1.0.0", description="版本号")

    # 核心配置
    personality: AgentPersonality = Field(..., description="人格设定")
    capabilities: List[AgentCapability] = Field(..., description="智能体能力列表")
    configuration: AgentConfiguration = Field(..., description="配置参数")

    # 系统提示词
    system_prompt: str = Field(..., description="系统提示词")
    user_prompt_template: str = Field(default="{input}", description="用户提示词模板")

    # 工具集成
    available_tools: List[str] = Field(default_factory=list, description="可用工具列表")
    required_permissions: List[str] = Field(default_factory=list, description="所需权限列表")

    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签列表")
    category: str = Field(default="general", description="分类")
    author: str = Field(..., description="作者")
    created_by: str = Field(..., description="创建者ID")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    published_at: Optional[datetime] = Field(None, description="发布时间")

    # 统计信息
    usage_count: int = Field(default=0, ge=0, description="使用次数")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="成功率")
    average_execution_time: float = Field(default=0.0, ge=0.0, description="平均执行时间(秒)")

    # 验证
    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Agent name must be alphanumeric with hyphens or underscores')
        return v

# ==================== 智能体节点模型 ====================

class AgentNodeInput(BaseModel):
    """智能体节点输入"""
    content: str = Field(..., description="输入内容")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")
    variables: Dict[str, Any] = Field(default_factory=dict, description="变量数据")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class AgentNodeOutput(BaseModel):
    """智能体节点输出"""
    content: str = Field(..., description="输出内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="输出元数据")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用记录")
    reasoning_steps: List[str] = Field(default_factory=list, description="推理步骤")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="置信度评分")
    execution_time: float = Field(..., ge=0.0, description="执行时间(秒)")
    tokens_used: int = Field(default=0, ge=0, description="使用的token数")

class AgentNode(BaseModel):
    """智能体工作流节点"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="节点ID")
    workflow_id: str = Field(..., description="所属工作流ID")
    agent_id: str = Field(..., description="关联的智能体ID")
    node_name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")

    # 节点配置
    position: Dict[str, float] = Field(default_factory=dict, description="节点位置")
    size: Dict[str, float] = Field(default_factory=dict, description="节点大小")
    style: Dict[str, Any] = Field(default_factory=dict, description="节点样式")

    # 输入输出定义
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="输入字段映射")
    output_mapping: Dict[str, str] = Field(default_factory=dict, description="输出字段映射")

    # 执行配置
    retry_count: int = Field(default=3, ge=0, le=10, description="重试次数")
    retry_delay: int = Field(default=5, ge=1, le=300, description="重试延迟(秒)")
    enable_streaming: bool = Field(default=False, description="是否启用流式输出")

    # 上下文管理
    context_window_size: int = Field(default=10, ge=1, le=100, description="上下文窗口大小")
    preserve_conversation: bool = Field(default=True, description="是否保留对话历史")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

# ==================== 对话上下文管理 ====================

class ConversationMessage(BaseModel):
    """对话消息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息ID")
    role: ConversationRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class AgentContext(BaseModel):
    """智能体上下文"""
    conversation_id: str = Field(..., description="对话ID")
    agent_id: str = Field(..., description="智能体ID")
    node_id: str = Field(..., description="节点ID")

    # 对话历史
    messages: List[ConversationMessage] = Field(default_factory=list, description="对话消息列表")

    # 上下文状态
    current_state: AgentExecutionState = Field(default=AgentExecutionState.PENDING, description="当前状态")
    variables: Dict[str, Any] = Field(default_factory=dict, description="上下文变量")
    shared_memory: Dict[str, Any] = Field(default_factory=dict, description="共享内存")

    # 执行信息
    execution_count: int = Field(default=0, ge=0, description="执行次数")
    total_tokens: int = Field(default=0, ge=0, description="总token使用量")
    total_execution_time: float = Field(default=0.0, ge=0.0, description="总执行时间")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

# ==================== 执行记录 ====================

class AgentExecutionRecord(BaseModel):
    """智能体执行记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="执行记录ID")
    agent_id: str = Field(..., description="智能体ID")
    node_id: str = Field(..., description="节点ID")
    workflow_id: str = Field(..., description="工作流ID")
    execution_id: str = Field(..., description="工作流执行ID")

    # 输入输出
    input_data: AgentNodeInput = Field(..., description="输入数据")
    output_data: Optional[AgentNodeOutput] = Field(None, description="输出数据")

    # 执行状态
    state: AgentExecutionState = Field(..., description="执行状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")

    # 性能指标
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    execution_time: Optional[float] = Field(None, ge=0.0, description="执行时间(秒)")
    tokens_used: int = Field(default=0, ge=0, description="使用的token数")
    tool_calls_count: int = Field(default=0, ge=0, description="工具调用次数")

    # 质量评估
    success: bool = Field(default=False, description="是否成功")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="质量评分")
    user_feedback: Optional[str] = Field(None, description="用户反馈")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="执行元数据")

# ==================== API请求响应模型 ====================

class CreateAgentRequest(BaseModel):
    """创建智能体请求"""
    agent: AgentRegistry = Field(..., description="智能体信息")

class CreateAgentResponse(BaseModel):
    """创建智能体响应"""
    success: bool = Field(..., description="是否成功")
    agent_id: str = Field(..., description="智能体ID")
    message: str = Field(..., description="响应消息")
    created_at: datetime = Field(..., description="创建时间")

class ExecuteAgentRequest(BaseModel):
    """执行智能体请求"""
    agent_id: str = Field(..., description="智能体ID")
    input_data: AgentNodeInput = Field(..., description="输入数据")
    context: Optional[AgentContext] = Field(None, description="执行上下文")
    stream: bool = Field(default=False, description="是否流式输出")

class ExecuteAgentResponse(BaseModel):
    """执行智能体响应"""
    success: bool = Field(..., description="是否成功")
    execution_id: str = Field(..., description="执行ID")
    output_data: Optional[AgentNodeOutput] = Field(None, description="输出数据")
    context: AgentContext = Field(..., description="更新后的上下文")
    execution_record: AgentExecutionRecord = Field(..., description="执行记录")

class ListAgentsResponse(BaseModel):
    """智能体列表响应"""
    agents: List[AgentRegistry] = Field(..., description="智能体列表")
    total: int = Field(..., ge=0, description="总数")
    page: int = Field(..., ge=1, description="当前页")
    page_size: int = Field(..., ge=1, description="页面大小")

# ==================== 错误处理模型 ====================

class AgentError(BaseModel):
    """智能体错误"""
    error_code: str = Field(..., description="错误代码")
    error_type: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    agent_id: Optional[str] = Field(None, description="相关智能体ID")
    execution_id: Optional[str] = Field(None, description="相关执行ID")
"""
提示词工程数据模型
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TaskCategory(str, Enum):
    """任务分类枚举"""
    # 通用类
    CONVERSATION_UNDERSTANDING = "conversation_understanding"
    DIRECT_CHAT = "direct_chat"
    
    # 工作流类
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    WORKFLOW_THINKING = "workflow_thinking"
    WORKFLOW_ANALYSIS = "workflow_analysis"
    WORKFLOW_DESIGN = "workflow_design"
    
    # 智能体类
    METADATA_AGENT = "metadata_agent"
    DATA_QUERY_AGENT = "data_query_agent"
    DATA_CLEAN_AGENT = "data_clean_agent"
    DATA_ENRICH_AGENT = "data_enrich_agent"
    DATA_VALIDATION_AGENT = "data_validation_agent"
    ANALYSIS_AGENT = "analysis_agent"
    INSIGHT_AGENT = "insight_agent"
    CONTENT_AGENT = "content_agent"
    FORMAT_AGENT = "format_agent"
    QUALITY_CHECK_AGENT = "quality_check_agent"
    RESULT_SYNTHESIS_AGENT = "result_synthesis_agent"
    KNOWLEDGE_BASE_AGENT = "knowledge_base_agent"
    WORKFLOW_AGENT = "workflow_agent"
    MCP_TOOL_AGENT = "mcp_tool_agent"
    SAP_ODATA_AGENT = "sap_odata_agent"
    LEARNING_WORKFLOW_DESIGNER = "learning_workflow_designer"
    
    # 工具类
    TOOL_EXECUTION = "tool_execution"
    
    # 分析类
    DATA_ANALYSIS = "data_analysis"
    COMPLEX_REASONING = "complex_reasoning"
    
    # 内容类
    CODE_GENERATION = "code_generation"
    CONTENT_CREATION = "content_creation"
    
    # 知识类
    KNOWLEDGE_SEARCH = "knowledge_search"


class PromptRole(str, Enum):
    """提示词角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class PromptExample(BaseModel):
    """提示词示例"""
    user: str
    assistant: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PromptTemplateConfig(BaseModel):
    """提示词模板配置"""
    name: str
    description: str
    system_prompt: str
    examples: List[PromptExample] = Field(default_factory=list)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=100, le=8000)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=0.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    output_format: Optional[Dict[str, Any]] = None
    dynamic_placeholders: List[str] = Field(default_factory=list)


class PromptContext(BaseModel):
    """提示词上下文"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    user_profile: Optional[Dict[str, Any]] = None
    task_context: Optional[Dict[str, Any]] = None
    available_tools: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class OptimizedPrompt(BaseModel):
    """优化后的提示词"""
    messages: List[Dict[str, str]]
    temperature: float
    max_tokens: int
    template_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PromptValidationResult(BaseModel):
    """提示词验证结果"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


# 交互协议模型（从shared_libs导入，如果不可用则本地定义）
try:
    from luminaos_common.schemas.interaction_protocol import (
        InteractionType,
        ExecutionStatus,
        InteractiveMessage,
        UserAction,
        ExecutionState,
        ConfirmationRequest,
        UserInputRequest
    )
except ImportError:
    # 如果shared_libs不可用，使用本地定义
    from enum import Enum
    from datetime import datetime
    
    class InteractionType(str, Enum):
        EXECUTION_START = "execution_start"
        EXECUTION_PROGRESS = "execution_progress"
        EXECUTION_STEP = "execution_step"
        EXECUTION_PAUSED = "execution_paused"
        EXECUTION_RESUMED = "execution_resumed"
        EXECUTION_CANCELLED = "execution_cancelled"
        EXECUTION_COMPLETED = "execution_completed"
        EXECUTION_ERROR = "execution_error"
        USER_INTERACTION_REQUIRED = "user_interaction_required"
        CONFIRMATION_REQUIRED = "confirmation_required"
    
    class ExecutionStatus(str, Enum):
        PENDING = "pending"
        RUNNING = "running"
        PAUSED = "paused"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
        ERROR = "error"
        WAITING_FOR_INPUT = "waiting_for_input"
    
    class InteractiveMessage(BaseModel):
        type: InteractionType
        execution_id: str
        session_id: str
        timestamp: datetime = Field(default_factory=datetime.now)
        data: Dict[str, Any] = Field(default_factory=dict)
        actions: List[str] = Field(default_factory=list)
        progress: Optional[float] = Field(None, ge=0.0, le=1.0)
        metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class UserAction(BaseModel):
        action: str
        execution_id: str
        session_id: str
        parameters: Dict[str, Any] = Field(default_factory=dict)
        timestamp: datetime = Field(default_factory=datetime.now)
    
    class ExecutionState(BaseModel):
        execution_id: str
        session_id: str
        status: ExecutionStatus
        current_step: int = 0
        total_steps: int = 0
        progress: float = Field(0.0, ge=0.0, le=1.0)
        user_input: Optional[str] = None
        context: Dict[str, Any] = Field(default_factory=dict)
        paused: bool = False
        cancelled: bool = False
        waiting_for_input: Optional[str] = None
        created_at: datetime = Field(default_factory=datetime.now)
        updated_at: datetime = Field(default_factory=datetime.now)


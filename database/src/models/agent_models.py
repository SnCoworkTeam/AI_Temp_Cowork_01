"""
智能体相关数据库模型
定义智能体注册、节点、上下文和执行记录的SQLAlchemy模型
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# 导入共享的枚举定义
from shared_libs.luminaos_common.schemas.agent_schemas import (
    AgentType,
    AgentStatus,
    AgentExecutionState,
    ConversationRole
)

Base = declarative_base()


class AgentRegistryModel(Base):
    """智能体注册表模型"""
    __tablename__ = 'agent_registry'

    # 基本信息
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    agent_type = Column(
        ENUM(
            *[agent_type.value for agent_type in AgentType],
            name='agenttype',
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    status = Column(
        ENUM(
            *[status.value for status in AgentStatus],
            name='agentstatus',
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=AgentStatus.INACTIVE.value
    )
    version = Column(String, nullable=False, default='1.0.0')

    # 人格设定
    personality_name = Column(String, nullable=False)
    personality_description = Column(Text, nullable=False)
    personality_traits = Column(JSONB, nullable=False, default=[])
    communication_style = Column(String, nullable=False, default='professional')
    expertise_areas = Column(JSONB, nullable=False, default=[])
    limitations = Column(JSONB, nullable=False, default=[])

    # 能力列表 (JSONB格式存储AgentCapability列表)
    capabilities = Column(JSONB, nullable=False, default=[])

    # 配置参数
    model = Column(String, nullable=False)
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=2048)
    top_p = Column(Float, nullable=False, default=1.0)
    frequency_penalty = Column(Float, nullable=False, default=0.0)
    presence_penalty = Column(Float, nullable=False, default=0.0)
    timeout = Column(Integer, nullable=False, default=300)
    max_tool_calls = Column(Integer, nullable=False, default=10)
    enable_memory = Column(Boolean, nullable=False, default=True)
    memory_size = Column(Integer, nullable=False, default=20)

    # 提示词
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False, default='{input}')

    # 工具和权限
    available_tools = Column(JSONB, nullable=False, default=[])
    required_permissions = Column(JSONB, nullable=False, default=[])

    # 元数据
    tags = Column(JSONB, nullable=False, default=[])
    category = Column(String, nullable=False, default='general')
    author = Column(String, nullable=False)
    created_by = Column(String, nullable=False)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)
    published_at = Column(DateTime, nullable=True)

    # 统计信息
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)
    average_execution_time = Column(Float, nullable=False, default=0.0)

    # 关系
    nodes = relationship("AgentNodeModel", back_populates="agent", cascade="all, delete-orphan")
    contexts = relationship("AgentContextModel", back_populates="agent", cascade="all, delete-orphan")
    execution_records = relationship("AgentExecutionRecordModel", back_populates="agent", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_agent_registry_name', 'name'),
        Index('idx_agent_registry_type', 'agent_type'),
        Index('idx_agent_registry_status', 'status'),
        Index('idx_agent_registry_category', 'category'),
        Index('idx_agent_registry_created_by', 'created_by'),
    )


class AgentNodeModel(Base):
    """智能体节点模型"""
    __tablename__ = 'agent_nodes'

    # 基本信息
    id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=False)  # 关联到工作流
    agent_id = Column(String, ForeignKey('agent_registry.id'), nullable=False)
    node_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # 节点配置 (UI相关)
    position = Column(JSONB, nullable=True)  # {x: float, y: float}
    size = Column(JSONB, nullable=True)      # {width: float, height: float}
    style = Column(JSONB, nullable=True)     # 节点样式配置

    # 输入输出映射
    input_mapping = Column(JSONB, nullable=False, default={})   # 输入字段映射
    output_mapping = Column(JSONB, nullable=False, default={})  # 输出字段映射

    # 执行配置
    retry_count = Column(Integer, nullable=False, default=3)
    retry_delay = Column(Integer, nullable=False, default=5)
    enable_streaming = Column(Boolean, nullable=False, default=False)

    # 上下文管理
    context_window_size = Column(Integer, nullable=False, default=10)
    preserve_conversation = Column(Boolean, nullable=False, default=True)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    agent = relationship("AgentRegistryModel", back_populates="nodes")
    contexts = relationship("AgentContextModel", back_populates="node", cascade="all, delete-orphan")
    execution_records = relationship("AgentExecutionRecordModel", back_populates="node", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_agent_nodes_workflow_id', 'workflow_id'),
        Index('idx_agent_nodes_agent_id', 'agent_id'),
    )


class AgentContextModel(Base):
    """智能体上下文模型"""
    __tablename__ = 'agent_contexts'

    # 基本信息
    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey('agent_registry.id'), nullable=False)
    node_id = Column(String, ForeignKey('agent_nodes.id'), nullable=False)

    # 上下文状态
    current_state = Column(
        ENUM(
            *[state.value for state in AgentExecutionState],
            name='agentexecutionstate',
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=AgentExecutionState.PENDING.value
    )
    variables = Column(JSONB, nullable=False, default={})
    shared_memory = Column(JSONB, nullable=False, default={})

    # 执行信息
    execution_count = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_execution_time = Column(Float, nullable=False, default=0.0)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)

    # 关系
    agent = relationship("AgentRegistryModel", back_populates="contexts")
    node = relationship("AgentNodeModel", back_populates="contexts")
    messages = relationship("ConversationMessageModel", back_populates="context", cascade="all, delete-orphan")

    # 约束和索引
    __table_args__ = (
        UniqueConstraint('conversation_id', 'agent_id', 'node_id', name='uq_agent_context'),
        Index('idx_agent_contexts_conversation_id', 'conversation_id'),
        Index('idx_agent_contexts_agent_id', 'agent_id'),
        Index('idx_agent_contexts_node_id', 'node_id'),
        Index('idx_agent_contexts_expires_at', 'expires_at'),
    )


class ConversationMessageModel(Base):
    """对话消息模型"""
    __tablename__ = 'conversation_messages'

    # 基本信息
    id = Column(String, primary_key=True)
    conversation_id = Column(String, nullable=False)
    role = Column(
        ENUM(
            *[role.value for role in ConversationRole],
            name='conversationrole',
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB, nullable=False, default=[])
    # 注意：不能使用 metadata 作为属性名，因为它是 SQLAlchemy 的保留属性
    # 使用 message_metadata 作为属性名，映射到数据库的 metadata 列
    message_metadata = Column('metadata', JSONB, nullable=False, default={})
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # 可选的上下文关联
    context_id = Column(String, ForeignKey('agent_contexts.id'), nullable=True)

    # 关系
    context = relationship("AgentContextModel", back_populates="messages")

    # 索引
    __table_args__ = (
        Index('idx_conversation_messages_conversation_id', 'conversation_id'),
        Index('idx_conversation_messages_timestamp', 'timestamp'),
        Index('idx_conversation_messages_role', 'role'),
    )


class AgentExecutionRecordModel(Base):
    """智能体执行记录模型"""
    __tablename__ = 'agent_execution_records'

    # 基本信息
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey('agent_registry.id'), nullable=False)
    node_id = Column(String, ForeignKey('agent_nodes.id'), nullable=False)
    workflow_id = Column(String, nullable=False)  # 关联到工作流
    execution_id = Column(String, nullable=False)  # 工作流执行ID

    # 输入输出数据
    input_data = Column(JSONB, nullable=False)   # AgentNodeInput的JSON表示
    output_data = Column(JSONB, nullable=True)   # AgentNodeOutput的JSON表示

    # 执行状态
    state = Column(
        ENUM(
            *[state.value for state in AgentExecutionState],
            name='agentexecutionstate',
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    error_message = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)

    # 性能指标
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间(秒)
    tokens_used = Column(Integer, nullable=False, default=0)
    tool_calls_count = Column(Integer, nullable=False, default=0)

    # 质量评估
    success = Column(Boolean, nullable=False, default=False)
    quality_score = Column(Float, nullable=True)  # 0.0-1.0
    user_feedback = Column(Text, nullable=True)

    # 元数据
    # 注意：不能使用 metadata 作为属性名，因为它是 SQLAlchemy 的保留属性
    # 使用 record_metadata 作为属性名，映射到数据库的 metadata 列
    record_metadata = Column('metadata', JSONB, nullable=False, default={})

    # 关系
    agent = relationship("AgentRegistryModel", back_populates="execution_records")
    node = relationship("AgentNodeModel", back_populates="execution_records")

    # 索引
    __table_args__ = (
        Index('idx_agent_execution_records_agent_id', 'agent_id'),
        Index('idx_agent_execution_records_node_id', 'node_id'),
        Index('idx_agent_execution_records_workflow_id', 'workflow_id'),
        Index('idx_agent_execution_records_execution_id', 'execution_id'),
        Index('idx_agent_execution_records_start_time', 'start_time'),
        Index('idx_agent_execution_records_state', 'state'),
        Index('idx_agent_execution_records_success', 'success'),
    )
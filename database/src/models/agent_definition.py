"""
智能体定义表（简化版）
用于 agent-service 持久化智能体配置
"""
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.sql import func

from .base import Base


class AgentDefinitionStatus(str, Enum):
    """智能体状态枚举（简化版）"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"


class AgentDefinition(Base):
    """智能体定义模型（用于 agent-service 持久化）"""
    __tablename__ = "agent_definitions"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    capabilities = Column(JSONB, nullable=False, default=list)
    system_prompt = Column(Text, nullable=True)
    config = Column(JSONB, nullable=False, default=dict)
    # 避免使用 SQLAlchemy 保留属性名 metadata
    agent_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    status = Column(
        ENUM(
            *[status.value for status in AgentDefinitionStatus],
            name="agentdefstatus",
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=AgentDefinitionStatus.ACTIVE.value
    )
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_agent_definitions_name", "name"),
        Index("idx_agent_definitions_status", "status"),
    )

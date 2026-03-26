"""
待办事项相关数据模型
"""
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum
from datetime import datetime

from .base import BaseModel, TimestampMixin


class TodoCategory(str, Enum):
    """待办事项分类"""
    WORK = "work"
    PERSONAL = "personal"
    URGENT = "urgent"
    PROJECT = "project"
    OTHER = "other"


class TodoPriority(str, Enum):
    """待办事项优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoStatus(str, Enum):
    """待办事项状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Todo(BaseModel, TimestampMixin):
    """待办事项模型"""
    __tablename__ = "user_todos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="待办事项ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    title = Column(String(200), nullable=False, comment="标题")
    description = Column(Text, nullable=True, comment="描述")
    category = Column(
        SQLEnum(TodoCategory, name='todocategory', create_type=True, values_callable=lambda x: [e.value for e in TodoCategory]),
        default=TodoCategory.WORK,
        nullable=False,
        index=True,
        comment="分类"
    )
    priority = Column(
        SQLEnum(TodoPriority, name='todopriority', create_type=True, values_callable=lambda x: [e.value for e in TodoPriority]),
        default=TodoPriority.MEDIUM,
        nullable=False,
        index=True,
        comment="优先级"
    )
    status = Column(
        SQLEnum(TodoStatus, name='todostatus', create_type=True, values_callable=lambda x: [e.value for e in TodoStatus]),
        default=TodoStatus.PENDING,
        nullable=False,
        index=True,
        comment="状态"
    )
    due_date = Column(DateTime, nullable=True, index=True, comment="截止日期")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    project_id = Column(UUID(as_uuid=True), ForeignKey("pm_projects.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联项目ID")
    task_id = Column(UUID(as_uuid=True), ForeignKey("pm_tasks.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联任务ID")
    extra_metadata = Column("metadata", JSONB, nullable=True, default=dict, comment="扩展元数据")
    
    # 关系
    user = relationship("User", backref="todos")
    project = relationship("Project", backref="todos")
    task = relationship("Task", backref="todos")

    __table_args__ = (
        Index('idx_user_todos_user_status', 'user_id', 'status'),
        Index('idx_user_todos_user_due_date', 'user_id', 'due_date'),
    )




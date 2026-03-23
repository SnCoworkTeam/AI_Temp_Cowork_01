"""
数据库模型模块
"""
from .base import Base, TimestampMixin
from .user_models import User, Role, Permission, UserSession
from .workflow_models import WorkflowDefinition, WorkflowExecution, WorkflowNode, WorkflowConnection
from .knowledge_models import Document, DocumentChunk, KnowledgeGraphNode, KnowledgeGraphEdge
from .mcp_models import MCPTool, MCPToolExecution
from .system_models import SystemConfig, AuditLog
from .chat_models import Conversation, Message, MessageRole, MessageStatus
from .token_blacklist import TokenBlacklist
from .entity_mapping import EntityMapping, EntityMappingCreate, EntityMappingSchema
from .feedback import Feedback, QueryLog
from .business_activity import BusinessActivity
from .capability_unit import CapabilityUnit
from .activity_capability_mapping import ActivityCapabilityMapping
from .agent_definition import AgentDefinition, AgentDefinitionStatus
from .enterprise_architecture_models import (
    BusinessProcess, BusinessCapability, BusinessService,
    ApplicationSystem, ApplicationService, APIInterface,
    DataEntity, DataModel, DataFlow,
    TechnologyComponent, TechnologyStack, InfrastructureComponent,
    ArchitectureRelationship,
    OrganizationUnit, BusinessRole,
    TechnologyType, TechnologyInstance,
    OrganizationBusinessRelationship
)

# 注意：WorkflowVersion和WorkflowVersionTag在metadata-service中定义
# 如果需要跨服务使用，可以在这里导入

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Role",
    "Permission",
    "UserSession",
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowNode",
    "WorkflowConnection",
    "Document",
    "DocumentChunk",
    "KnowledgeGraphNode",
    "KnowledgeGraphEdge",
    "MCPTool",
    "MCPToolExecution",
    "SystemConfig",
    "AuditLog",
    "Conversation",
    "Message",
    "MessageRole",
    "MessageStatus",
    "TokenBlacklist",
    "EntityMapping",
    "EntityMappingCreate",
    "EntityMappingSchema",
    "Feedback",
    "QueryLog",
    "BusinessActivity",
    "CapabilityUnit",
    "ActivityCapabilityMapping",
    "AgentDefinition",
    "AgentDefinitionStatus",
    # 企业架构模型
    "BusinessProcess",
    "BusinessCapability",
    "BusinessService",
    "ApplicationSystem",
    "ApplicationService",
    "APIInterface",
    "DataEntity",
    "DataModel",
    "DataFlow",
    "TechnologyComponent",
    "TechnologyStack",
    "InfrastructureComponent",
    "ArchitectureRelationship",
    # 组织架构模型
    "OrganizationUnit",
    "BusinessRole",
    # 技术架构增强模型
    "TechnologyType",
    "TechnologyInstance",
    # 组织业务关系模型
    "OrganizationBusinessRelationship",
]

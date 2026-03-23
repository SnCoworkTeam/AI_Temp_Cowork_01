"""
LuminaOS Common Library

企业AI平台共享库 - 提供通用的数据模型、工具函数和业务逻辑
"""

__version__ = "1.0.0"
__author__ = "LuminaOS Team"

# 导出常用的模型和工具
from .schemas.workflow_states import (
    WorkflowStateTypedDict,
    WorkflowStateModel,
    WorkflowState,
    validate_workflow_state,
    create_workflow_state,
    AgentWorkflowState,
    MCPWorkflowState,
)

from .schemas.workflow_schemas import (
    WorkflowStatus,
    ExecutionStatus,
    NodeType,
    WorkflowNode,
    WorkflowDefinition,
    WorkflowInfo,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    NodeExecutionResult,
    WorkflowRegisterRequest,
    WorkflowRegisterResponse,
    WorkflowListResponse,
)

__all__ = [
    # Version
    "__version__",
    # Workflow States
    "WorkflowStateTypedDict",
    "WorkflowStateModel",
    "WorkflowState",
    "validate_workflow_state",
    "create_workflow_state",
    "AgentWorkflowState",
    "MCPWorkflowState",
    # Workflow Schemas
    "WorkflowStatus",
    "ExecutionStatus",
    "NodeType",
    "WorkflowNode",
    "WorkflowDefinition",
    "WorkflowInfo",
    "WorkflowExecutionRequest",
    "WorkflowExecutionResponse",
    "NodeExecutionResult",
    "WorkflowRegisterRequest",
    "WorkflowRegisterResponse",
    "WorkflowListResponse",
]

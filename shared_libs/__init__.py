"""
LuminaOS共享库 - 保持向后兼容的导入

这个模块保持了对现有导入方式的兼容性，同时提供了新的标准化导入方式。
"""

__version__ = "1.0.0"
__author__ = "LuminaOS Team"

# 保持向后兼容 - 现有的导入方式仍然可用
# 这样现有代码不需要立即修改

# 新的标准导入方式 (推荐)
try:
    # 从luminaos_common导入
    from .luminaos_common.schemas.workflow_states import (
        WorkflowStateTypedDict,
        WorkflowStateModel,
        WorkflowState,
        validate_workflow_state,
        create_workflow_state,
        AgentWorkflowState,
        MCPWorkflowState,
    )

    from .luminaos_common.schemas.workflow_schemas import (
        WorkflowCreate,
        WorkflowUpdate,
        WorkflowResponse,
    )

    from .luminaos_common.schemas.chat_schemas import (
        ChatRequest,
        ChatResponse,
    )

    from .luminaos_common.common.logger import setup_logger
    from .luminaos_common.common.error_handler import AppError, create_error_response
    
    # 创建common别名以保持向后兼容
    import sys
    from types import ModuleType
    common_module = ModuleType('shared_libs.common')
    common_module.logger = sys.modules['.luminaos_common.common.logger'.replace('.luminaos_common', 'shared_libs.luminaos_common')]
    common_module.error_handler = sys.modules['.luminaos_common.common.error_handler'.replace('.luminaos_common', 'shared_libs.luminaos_common')]
    sys.modules['shared_libs.common'] = common_module

except ImportError:
    # 如果新结构不存在，尝试从luminaos_common直接导入
    try:
        from luminaos_common.schemas.workflow_states import (
            WorkflowStateTypedDict,
            WorkflowStateModel,
            WorkflowState,
            validate_workflow_state,
            create_workflow_state,
            AgentWorkflowState,
            MCPWorkflowState,
        )
        from luminaos_common.schemas.workflow_schemas import (
            WorkflowCreate,
            WorkflowUpdate,
            WorkflowResponse,
        )
        from luminaos_common.schemas.chat_schemas import (
            ChatRequest,
            ChatResponse,
        )
        from luminaos_common.common.logger import setup_logger
        from luminaos_common.common.error_handler import AppError, create_error_response
    except ImportError:
        # 如果都失败，使用警告
        import warnings
        warnings.warn(
            "使用旧的shared_libs结构，建议升级到新的包结构",
            DeprecationWarning,
            stacklevel=2
        )

__all__ = [
    # 版本信息
    "__version__",

    # 工作流相关
    "WorkflowStateTypedDict",
    "WorkflowStateModel",
    "WorkflowState",
    "validate_workflow_state",
    "create_workflow_state",
    "AgentWorkflowState",
    "MCPWorkflowState",
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowResponse",

    # 聊天相关
    "ChatRequest",
    "ChatResponse",

    # 通用工具
    "setup_logger",
    "AppError",
    "create_error_response",
]
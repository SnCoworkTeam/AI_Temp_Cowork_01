"""
路由模块
"""
from . import agents
from . import executions
from . import models
from . import health
from . import chat
from . import stream_executions
from . import interactive_chat
from . import dynamic_workflow
from . import agent_registry
from . import prompts
from . import business_scenarios
from . import performance_monitoring
# 延迟导入server_operation，避免启动时错误
try:
    from . import server_operation
    _server_operation_available = True
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"无法导入server_operation路由: {e}，功能将不可用")
    _server_operation_available = False
    server_operation = None

__all__ = [
    "agents",
    "executions",
    "models",
    "health",
    "chat",
    "stream_executions",
    "interactive_chat",
    "dynamic_workflow",
    "agent_registry",
    "prompts",
    "business_scenarios",
    "performance_monitoring",
    "server_operation",  # 延迟导入，条件添加
    "_server_operation_available",  # 导出可用性标志
]

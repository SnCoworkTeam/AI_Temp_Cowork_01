"""
MCP工具模块
"""
from .tool_registry import ToolRegistry, ToolExecutionError

# 创建全局工具注册表实例
tool_registry = ToolRegistry()

__all__ = ["ToolRegistry", "ToolExecutionError", "tool_registry"]


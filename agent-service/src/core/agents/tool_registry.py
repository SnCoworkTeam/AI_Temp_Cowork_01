"""
工具注册表
统一管理所有工具
"""
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Tool(ABC):
    """工具基类"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（可选）
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        pass

    def validate_params(self, **kwargs) -> bool:
        """
        验证参数（可选实现）

        Args:
            **kwargs: 参数

        Returns:
            是否有效
        """
        return True

    def get_schema(self) -> Dict[str, Any]:
        """获取工具模式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        logger.info("工具注册表初始化")

    def register_tool(self, tool: Tool):
        """
        注册工具

        Args:
            tool: 工具实例
        """
        if tool.name in self.tools:
            logger.warning(f"工具 {tool.name} 已存在，将被覆盖")
        self.tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")

    def unregister_tool(self, name: str):
        """
        注销工具

        Args:
            name: 工具名称
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"注销工具: {name}")
        else:
            logger.warning(f"工具 {name} 不存在")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """
        列出所有工具

        Returns:
            工具列表
        """
        return list(self.tools.values())

    def get_tool_names(self) -> List[str]:
        """
        获取所有工具名称

        Returns:
            工具名称列表
        """
        return list(self.tools.keys())

    def has_tool(self, name: str) -> bool:
        """
        检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self.tools

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的模式

        Returns:
            工具模式列表
        """
        return [tool.get_schema() for tool in self.tools.values()]


# 全局工具注册表实例
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表实例（单例模式）

    Returns:
        工具注册表实例
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def reset_tool_registry():
    """重置工具注册表（主要用于测试）"""
    global _tool_registry
    _tool_registry = None


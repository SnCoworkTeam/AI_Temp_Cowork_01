"""
工具调用节点
调用MCP工具
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode
from shared_libs.luminaos_common.common.http_client import HTTPClient

logger = logging.getLogger(__name__)


class ToolNode(BaseNode):
    """工具调用节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.tool_name = self.config.get("tool_name", "")
        self.mcp_gateway_url = self.config.get("mcp_gateway_url", "http://mcp-gateway:8001")
        self.parameters = self.config.get("parameters", {})
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        if not self.tool_name:
            state["error"] = f"Tool Node '{self.name}': tool_name not specified"
            return state
        
        try:
            # 构建参数（可以使用状态变量）
            params = self._resolve_parameters(self.parameters, state)
            
            logger.info(f"Tool Node '{self.name}' calling tool: {self.tool_name}")
            
            # 调用MCP Gateway
            async with HTTPClient(self.mcp_gateway_url) as client:
                result = await client.post(
                    f"/api/tools/{self.tool_name}/execute",
                    data={
                        "parameters": params,
                        "timeout": self.config.get("timeout", 30)
                    }
                )
            
            # 将结果添加到状态
            state[f"{self.name}_output"] = result.get("result")
            state[f"{self.name}_success"] = result.get("success", False)
            
            return state
        
        except Exception as e:
            logger.error(f"Tool Node execution error: {str(e)}", exc_info=True)
            state["error"] = f"Tool Node '{self.name}' failed: {str(e)}"
            return state
    
    def _resolve_parameters(self, parameters: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数（支持状态变量引用）"""
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # 状态变量引用 ${variable_name}
                var_name = value[2:-1]
                resolved[key] = state.get(var_name, value)
            else:
                resolved[key] = value
        return resolved










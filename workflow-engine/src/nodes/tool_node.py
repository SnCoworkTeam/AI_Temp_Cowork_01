"""
MCP工具调用节点
调用MCP Gateway执行工具
"""
from typing import Dict, Any, Optional
import logging

from .base_node import BaseNode, NodeExecutionError
from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings

logger = logging.getLogger(__name__)


class ToolNode(BaseNode):
    """工具调用节点 - 调用MCP Gateway执行工具"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        self.tool_name = self.config.get("tool_name", "")
        self.mcp_gateway_url = self.config.get(
            "mcp_gateway_url",
            settings.MCP_GATEWAY_URL
        )
        self.parameters = self.config.get("parameters", {})
        self.timeout = self.config.get("timeout", 30)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        if not self.tool_name:
            raise NodeExecutionError(
                self.name,
                "tool_name not specified in node config"
            )
        
        try:
            # 解析参数（支持状态变量引用）
            params = self._resolve_parameters(self.parameters, state)
            
            logger.info(
                f"Tool Node '{self.name}' calling tool: {self.tool_name} "
                f"with parameters: {params}"
            )
            
            # 调用MCP Gateway
            try:
                async with HTTPClient(self.mcp_gateway_url, timeout=self.timeout) as client:
                    response = await client.post(
                        f"/api/tools/{self.tool_name}/execute",
                        data={
                            "parameters": params,
                            "timeout": self.timeout
                        }
                    )
            except Exception as e:
                raise NodeExecutionError(
                    self.name,
                    f"Failed to call MCP Gateway: {str(e)}",
                    e
                )
            
            # 检查响应
            if not response.get("success", False):
                error_msg = response.get("error", "Unknown error")
                raise NodeExecutionError(
                    self.name,
                    f"Tool execution failed: {error_msg}"
                )
            
            # 将结果添加到状态
            tool_result = response.get("result", {})
            output_key = f"{self.name}_output"
            state[output_key] = {
                "tool_name": self.tool_name,
                "result": tool_result,
                "execution_time": response.get("execution_time"),
                "node_name": self.name,
            }
            
            # 也添加到根级别（方便访问）
            state[f"{self.name}_result"] = tool_result
            state[f"{self.name}_success"] = True
            
            logger.info(f"Tool Node '{self.name}' completed successfully")
            
            return state
        
        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Tool Node execution failed: {str(e)}",
                e
            )
    
    def _resolve_parameters(self, parameters: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析参数（支持状态变量引用）
        
        Args:
            parameters: 参数配置
            state: 工作流状态
        
        Returns:
            解析后的参数
        """
        resolved = {}
        for key, value in parameters.items():
            resolved[key] = self._resolve_value(value, state)
        return resolved
    
    def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
        """
        递归解析值（支持状态变量引用）
        
        Args:
            value: 要解析的值
            state: 工作流状态
        
        Returns:
            解析后的值
        """
        if isinstance(value, str):
            # 检查是否是状态变量引用 ${variable_name}
            if value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                # 支持嵌套键（如 ${data.items.0}）
                resolved = self.get_state_value(state, var_name, value)
                return resolved
            # 检查是否包含模板变量
            if "${" in value:
                return self.resolve_template(value, state)
            return value
        elif isinstance(value, dict):
            return {k: self._resolve_value(v, state) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(item, state) for item in value]
        else:
            return value
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        if not self.tool_name:
            logger.warning(f"Tool Node '{self.name}' has no tool_name configured")
            return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        # 检查是否有输出
        output_key = f"{self.name}_output"
        if output_key not in output:
            logger.warning(f"Tool Node '{self.name}' did not produce output")
            return False
        
        return True










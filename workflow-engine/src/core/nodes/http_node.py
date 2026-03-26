"""
HTTP请求节点
发送HTTP请求
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode
from shared_libs.luminaos_common.common.http_client import HTTPClient

logger = logging.getLogger(__name__)


class HTTPNode(BaseNode):
    """HTTP请求节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.url = self.config.get("url", "")
        self.method = self.config.get("method", "GET").upper()
        self.headers = self.config.get("headers", {})
        self.body = self.config.get("body", {})
        self.timeout = self.config.get("timeout", 30)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行HTTP请求节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        if not self.url:
            state["error"] = f"HTTP Node '{self.name}': url not specified"
            return state
        
        try:
            # 解析URL（支持状态变量）
            url = self._resolve_template(self.url, state)
            
            # 解析body（支持状态变量）
            body = self._resolve_template(self.body, state) if self.body else None
            
            logger.info(f"HTTP Node '{self.name}' sending {self.method} request to {url}")
            
            # 发送HTTP请求
            async with HTTPClient(url, timeout=self.timeout) as client:
                if self.method == "GET":
                    result = await client.get("", params=body or {})
                elif self.method == "POST":
                    result = await client.post("", data=body)
                elif self.method == "PUT":
                    result = await client.put("", data=body)
                elif self.method == "DELETE":
                    result = await client.delete("")
                else:
                    raise ValueError(f"Unsupported HTTP method: {self.method}")
            
            # 将结果添加到状态
            state[f"{self.name}_response"] = result
            state[f"{self.name}_success"] = True
            
            return state
        
        except Exception as e:
            logger.error(f"HTTP Node execution error: {str(e)}", exc_info=True)
            state["error"] = f"HTTP Node '{self.name}' failed: {str(e)}"
            state[f"{self.name}_success"] = False
            return state
    
    def _resolve_template(self, template: Any, state: Dict[str, Any]) -> Any:
        """解析模板（支持${variable}格式的状态变量）"""
        if isinstance(template, str):
            # 简单的模板替换
            result = template
            for key, value in state.items():
                result = result.replace(f"${{{key}}}", str(value))
            return result
        elif isinstance(template, dict):
            return {k: self._resolve_template(v, state) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._resolve_template(item, state) for item in template]
        else:
            return template










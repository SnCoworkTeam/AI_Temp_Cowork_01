"""
日志节点
记录工作流状态和中间结果
"""
from typing import Dict, Any
import logging
import json

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class LogNode(BaseNode):
    """日志节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.log_level = self.config.get("log_level", "INFO").upper()
        self.log_message = self.config.get("message", "Log node executed")
        self.log_data = self.config.get("data", [])
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行日志节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            # 构建日志消息
            message = self.log_message.format(**state) if "{" in self.log_message else self.log_message
            
            # 提取要记录的数据
            log_data = {}
            for key in self.log_data:
                if key in state:
                    log_data[key] = state[key]
            
            # 记录日志
            log_method = getattr(logger, self.log_level.lower(), logger.info)
            log_method(
                f"Log Node '{self.name}': {message}",
                extra={"data": log_data}
            )
            
            # 将日志信息添加到状态
            state[f"{self.name}_logged"] = True
            state[f"{self.name}_log_message"] = message
            state[f"{self.name}_log_data"] = log_data
            
            return state
        
        except Exception as e:
            logger.error(f"Log Node execution error: {str(e)}")
            state["error"] = f"Log Node '{self.name}' failed: {str(e)}"
            return state










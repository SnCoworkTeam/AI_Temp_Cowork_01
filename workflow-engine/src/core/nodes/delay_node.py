"""
延迟节点
在工作流中添加延迟
"""
from typing import Dict, Any
import logging
import asyncio

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class DelayNode(BaseNode):
    """延迟节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.delay_seconds = self.config.get("delay_seconds", 1)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行延迟节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            logger.info(f"Delay Node '{self.name}' waiting {self.delay_seconds} seconds")
            await asyncio.sleep(self.delay_seconds)
            state[f"{self.name}_delayed"] = True
            return state
        except Exception as e:
            logger.error(f"Delay Node execution error: {str(e)}")
            state["error"] = f"Delay Node '{self.name}' failed: {str(e)}"
            return state










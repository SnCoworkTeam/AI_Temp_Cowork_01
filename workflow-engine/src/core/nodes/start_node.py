"""
开始节点
工作流的入口节点
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class StartNode(BaseNode):
    """开始节点"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description or "Start node")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行开始节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        logger.info(f"Start Node '{self.name}' executed")
        state["workflow_started"] = True
        state["start_node"] = self.name
        return state










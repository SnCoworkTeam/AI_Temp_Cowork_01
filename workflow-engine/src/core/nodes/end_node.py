"""
结束节点
工作流的出口节点
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class EndNode(BaseNode):
    """结束节点"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description or "End node")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行结束节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        logger.info(f"End Node '{self.name}' executed")
        state["workflow_completed"] = True
        state["end_node"] = self.name
        return state










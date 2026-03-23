"""
开始节点
工作流的入口节点
"""
from typing import Dict, Any, Optional
import logging

from .base_node import BaseNode

logger = logging.getLogger(__name__)


class StartNode(BaseNode):
    """开始节点 - 工作流的入口节点"""
    
    def __init__(
        self,
        name: str = "start",
        description: str = "Start node",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行开始节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        logger.info(f"Start Node '{self.name}' executed")
        
        # 标记工作流已开始
        state["workflow_started"] = True
        state["start_node"] = self.name
        state[f"{self.name}_executed"] = True
        
        logger.info(f"Start Node '{self.name}' completed successfully")
        
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        # 开始节点不需要验证输入
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        # 检查是否标记为已开始
        if "workflow_started" not in output:
            logger.warning(f"Start Node '{self.name}' did not mark workflow as started")
            return False
        return True










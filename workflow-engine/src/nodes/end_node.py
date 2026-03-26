"""
结束节点
工作流的出口节点
"""
from typing import Dict, Any, Optional
import logging

from .base_node import BaseNode

logger = logging.getLogger(__name__)


class EndNode(BaseNode):
    """结束节点 - 工作流的出口节点"""
    
    def __init__(
        self,
        name: str = "end",
        description: str = "End node",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行结束节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        logger.info(f"End Node '{self.name}' executed")
        
        # 标记工作流已完成
        state["workflow_completed"] = True
        state["end_node"] = self.name
        state[f"{self.name}_executed"] = True
        
        # 提取最终结果（排除元数据）
        final_result = {
            k: v for k, v in state.items()
            if not k.startswith("_") and k not in [
                "workflow_started",
                "start_node",
                "workflow_completed",
                "end_node",
                "execution_id",
                "workflow_id",
                "start_time",
            ]
        }
        state["final_result"] = final_result
        
        logger.info(f"End Node '{self.name}' completed successfully")
        
        return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        # 结束节点不需要验证输入
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        # 检查是否标记为已完成
        if "workflow_completed" not in output:
            logger.warning(f"End Node '{self.name}' did not mark workflow as completed")
            return False
        return True










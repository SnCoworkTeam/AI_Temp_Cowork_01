"""
条件判断节点
根据条件决定工作流分支
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class ConditionNode(BaseNode):
    """条件判断节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.condition = self.config.get("condition", "True")
        self.true_output = self.config.get("true_output", "true")
        self.false_output = self.config.get("false_output", "false")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行条件判断节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态（包含条件结果）
        """
        try:
            # 评估条件表达式
            # 注意：生产环境应使用更安全的表达式解析器
            condition_result = self._evaluate_condition(self.condition, state)
            
            logger.info(
                f"Condition Node '{self.name}': condition='{self.condition}' "
                f"result={condition_result}"
            )
            
            # 添加条件结果到状态
            state[f"{self.name}_condition_result"] = condition_result
            state[f"{self.name}_branch"] = self.true_output if condition_result else self.false_output
            
            return state
        
        except Exception as e:
            logger.error(f"Condition Node execution error: {str(e)}", exc_info=True)
            state["error"] = f"Condition Node '{self.name}' failed: {str(e)}"
            state[f"{self.name}_condition_result"] = False
            return state
    
    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件求值（注意：生产环境应使用更安全的方式）
            # 这里使用eval，实际应该使用ast.literal_eval或专门的表达式解析器
            safe_dict = {"state": state, "__builtins__": {}}
            result = eval(condition, safe_dict)
            return bool(result)
        except Exception as e:
            logger.warning(f"Condition evaluation failed: {str(e)}, defaulting to False")
            return False










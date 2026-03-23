"""
条件判断节点
根据条件表达式决定工作流分支
"""
from typing import Dict, Any, Optional
import logging
import ast
import operator

from .base_node import BaseNode, NodeExecutionError

logger = logging.getLogger(__name__)


class ConditionNode(BaseNode):
    """条件判断节点 - 根据条件表达式决定分支"""
    
    # 安全的操作符字典
    _safe_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        self.condition = self.config.get("condition", "True")
        self.true_output = self.config.get("true_output", "true")
        self.false_output = self.config.get("false_output", "false")
    
    def _evaluate_expression(self, expr: str, state: Dict[str, Any]) -> Any:
        """
        安全地评估表达式
        
        Args:
            expr: 表达式字符串
            state: 工作流状态
        
        Returns:
            表达式结果
        """
        try:
            # 使用AST解析表达式
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body, state)
        except Exception as e:
            logger.warning(f"Expression evaluation failed: {str(e)}, defaulting to False")
            return False
    
    def _eval_node(self, node: ast.AST, state: Dict[str, Any]) -> Any:
        """
        递归评估AST节点
        
        Args:
            node: AST节点
            state: 工作流状态
        
        Returns:
            节点值
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # 变量名 - 从state中获取
            return self.get_state_value(state, node.id, None)
        elif isinstance(node, ast.Attribute):
            # 属性访问 - 如 state.get
            obj = self._eval_node(node.value, state)
            return getattr(obj, node.attr, None)
        elif isinstance(node, ast.Subscript):
            # 下标访问 - 如 state["key"] 或 state[0]
            value = self._eval_node(node.value, state)
            key = self._eval_node(node.slice, state)
            if isinstance(value, (list, dict, str)):
                try:
                    return value[key]
                except (IndexError, KeyError, TypeError):
                    return None
            return None
        elif isinstance(node, ast.Call):
            # 函数调用 - 只允许安全的函数
            func = self._eval_node(node.func, state)
            if func is None:
                return None
            args = [self._eval_node(arg, state) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value, state) for kw in node.keywords}
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function call failed: {str(e)}")
                return None
        elif isinstance(node, ast.BinOp):
            # 二元运算
            op = self._safe_operators.get(type(node.op))
            if op is None:
                return None
            left = self._eval_node(node.left, state)
            right = self._eval_node(node.right, state)
            try:
                return op(left, right)
            except Exception:
                return None
        elif isinstance(node, ast.UnaryOp):
            # 一元运算
            op = self._safe_operators.get(type(node.op))
            if op is None:
                return None
            operand = self._eval_node(node.operand, state)
            try:
                return op(operand)
            except Exception:
                return None
        elif isinstance(node, ast.BoolOp):
            # 布尔运算
            op = self._safe_operators.get(type(node.op))
            if op is None:
                return None
            values = [self._eval_node(v, state) for v in node.values]
            try:
                result = values[0]
                for v in values[1:]:
                    result = op(result, v)
                return result
            except Exception:
                return None
        elif isinstance(node, ast.Compare):
            # 比较运算
            left = self._eval_node(node.left, state)
            for op_node, comparator in zip(node.ops, node.comparators):
                op = self._safe_operators.get(type(op_node))
                if op is None:
                    return False
                right = self._eval_node(comparator, state)
                try:
                    if not op(left, right):
                        return False
                    left = right
                except Exception:
                    return False
            return True
        else:
            logger.warning(f"Unsupported AST node type: {type(node)}")
            return None
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行条件判断节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态（包含条件结果和分支信息）
        """
        try:
            # 评估条件表达式
            condition_result = self._evaluate_expression(self.condition, state)
            condition_result_bool = bool(condition_result)
            
            logger.info(
                f"Condition Node '{self.name}': condition='{self.condition}' "
                f"result={condition_result_bool}"
            )
            
            # 添加条件结果到状态
            output_key = f"{self.name}_output"
            state[output_key] = {
                "condition": self.condition,
                "result": condition_result,
                "result_bool": condition_result_bool,
                "branch": self.true_output if condition_result_bool else self.false_output,
                "node_name": self.name,
            }
            
            # 添加到根级别（方便访问）
            state[f"{self.name}_condition_result"] = condition_result_bool
            state[f"{self.name}_branch"] = self.true_output if condition_result_bool else self.false_output
            
            logger.info(f"Condition Node '{self.name}' completed successfully")
            
            return state
        
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Condition evaluation failed: {str(e)}",
                e
            )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        if not self.condition:
            logger.warning(f"Condition Node '{self.name}' has empty condition")
            return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        # 检查是否有条件结果
        output_key = f"{self.name}_output"
        if output_key not in output:
            logger.warning(f"Condition Node '{self.name}' did not produce output")
            return False
        
        return True










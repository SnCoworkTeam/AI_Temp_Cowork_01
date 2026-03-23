"""
基础工作流节点
统一的节点接口、状态管理和错误处理
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class NodeExecutionError(Exception):
    """节点执行错误"""
    def __init__(self, node_name: str, message: str, original_error: Optional[Exception] = None):
        self.node_name = node_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"Node '{node_name}' execution failed: {message}")


class BaseNode(ABC):
    """工作流节点基类"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.config = config or {}
        self.node_id = node_id or name
        self._execution_count = 0
        self._last_execution_time: Optional[datetime] = None
        self._last_error: Optional[str] = None
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点逻辑
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        pass
    
    async def execute_with_error_handling(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行节点（带错误处理）
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        start_time = datetime.now()
        
        try:
            # 验证输入
            if not self.validate_input(state):
                raise NodeExecutionError(
                    self.name,
                    "Input validation failed"
                )
            
            # 记录执行开始
            logger.info(f"Node '{self.name}' execution started")
            
            # 执行节点逻辑
            result = await self.execute(state)
            
            # 验证输出
            if not self.validate_output(result):
                raise NodeExecutionError(
                    self.name,
                    "Output validation failed"
                )
            
            # 更新执行统计
            self._execution_count += 1
            self._last_execution_time = datetime.now()
            self._last_error = None
            
            # 添加节点执行元数据
            result[f"{self.name}_executed_at"] = self._last_execution_time.isoformat()
            result[f"{self.name}_execution_count"] = self._execution_count
            
            logger.info(f"Node '{self.name}' execution completed successfully")
            
            return result
        
        except NodeExecutionError as e:
            self._last_error = str(e)
            logger.error(
                f"Node '{self.name}' execution failed: {str(e)}",
                exc_info=True
            )
            
            # 将错误信息添加到状态
            state["error"] = str(e)
            state["error_node"] = self.name
            state["error_time"] = datetime.now().isoformat()
            
            return state
        
        except Exception as e:
            self._last_error = str(e)
            error_msg = f"Unexpected error in node '{self.name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 将错误信息添加到状态
            state["error"] = error_msg
            state["error_node"] = self.name
            state["error_time"] = datetime.now().isoformat()
            state["error_traceback"] = traceback.format_exc()
            
            return state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        验证输入状态
        
        Args:
            state: 当前工作流状态
        
        Returns:
            是否通过验证
        """
        # 默认实现：检查是否有错误
        if "error" in state:
            logger.warning(f"Node '{self.name}' received state with error: {state.get('error')}")
            return False
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        验证输出状态
        
        Args:
            output: 输出状态
        
        Returns:
            是否通过验证
        """
        # 默认实现：检查是否有错误
        if "error" in output and output.get("error_node") == self.name:
            return False
        return True
    
    def resolve_template(self, template: str, state: Dict[str, Any]) -> str:
        """
        解析模板字符串（支持状态变量引用）
        
        支持两种格式：
        1. ${variable_name} - 完整格式
        2. {variable_name} - 简化格式（兼容性）
        
        支持嵌套访问，如 {input_data.input} 或 ${input_data.input}
        
        Args:
            template: 模板字符串
            state: 工作流状态
        
        Returns:
            解析后的字符串
        """
        import re
        
        result = template
        
        def get_nested_value(obj: Any, path: str) -> Any:
            """获取嵌套值，支持点号分隔的路径"""
            keys = path.split('.')
            value = obj
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif hasattr(value, key):
                    value = getattr(value, key)
                else:
                    return None
                if value is None:
                    return None
            return value
        
        def replace_var(match):
            """替换单个变量"""
            # 获取变量名（可能包含点号），支持 ${var} 和 {var} 两种格式
            var_expr = match.group(1) or match.group(2)
            if not var_expr:
                return match.group(0)
            
            # 先尝试嵌套访问
            value = get_nested_value(state, var_expr)
            if value is not None:
                return str(value)
            # 如果嵌套访问失败，尝试直接访问
            if var_expr in state:
                return str(state[var_expr])
            # 如果都失败，返回原字符串
            return match.group(0)
        
        # 匹配 ${variable} 或 {variable} 格式
        # 支持嵌套路径，如 {input_data.input} 或 ${input_data.input}
        pattern = r'\$\{([^}]+)\}|\{([^}]+)\}'
        result = re.sub(pattern, replace_var, result)
        
        # 特殊处理：如果模板是 {input}，尝试从 input_data.input 获取
        if result == template and '{input}' in template:
            input_value = get_nested_value(state, 'input_data.input') or get_nested_value(state, 'input')
            if input_value:
                result = template.replace('{input}', str(input_value))
        
        return result
    
    def get_state_value(self, state: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        从状态中获取值（支持嵌套键）
        
        Args:
            state: 工作流状态
            key: 键名，支持点号分隔的嵌套键（如 "data.items.0"）
            default: 默认值
        
        Returns:
            状态值
        """
        keys = key.split(".")
        value = state
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            elif isinstance(value, list) and k.isdigit():
                try:
                    value = value[int(k)]
                except (IndexError, ValueError):
                    return default
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set_state_value(self, state: Dict[str, Any], key: str, value: Any):
        """
        设置状态值（支持嵌套键）
        
        Args:
            state: 工作流状态
            key: 键名，支持点号分隔的嵌套键
            value: 要设置的值
        """
        keys = key.split(".")
        current = state
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取节点执行统计信息"""
        return {
            "node_id": self.node_id,
            "node_name": self.name,
            "execution_count": self._execution_count,
            "last_execution_time": self._last_execution_time.isoformat() if self._last_execution_time else None,
            "last_error": self._last_error,
        }


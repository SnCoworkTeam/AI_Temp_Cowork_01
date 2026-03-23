"""
数据转换节点
转换和格式化数据
"""
from typing import Dict, Any
import logging

from ...nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class TransformNode(BaseNode):
    """数据转换节点"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description)
        self.config = config or {}
        self.transform_function = self.config.get("transform", "identity")
        self.mapping = self.config.get("mapping", {})
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据转换节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            logger.info(f"Transform Node '{self.name}' executing")
            
            # 应用转换
            if self.transform_function == "mapping":
                result = self._apply_mapping(state)
            elif self.transform_function == "filter":
                result = self._apply_filter(state)
            elif self.transform_function == "format":
                result = self._apply_format(state)
            else:
                # 默认：identity（不转换）
                result = state.copy()
            
            # 合并结果到状态
            state.update(result)
            state[f"{self.name}_transformed"] = True
            
            return state
        
        except Exception as e:
            logger.error(f"Transform Node execution error: {str(e)}", exc_info=True)
            state["error"] = f"Transform Node '{self.name}' failed: {str(e)}"
            return state
    
    def _apply_mapping(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """应用字段映射"""
        result = {}
        for target_key, source_key in self.mapping.items():
            if isinstance(source_key, str):
                # 简单字段映射
                result[target_key] = state.get(source_key)
            elif isinstance(source_key, dict):
                # 复杂映射（可扩展）
                result[target_key] = source_key
        return result
    
    def _apply_filter(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """应用过滤"""
        filter_keys = self.config.get("filter_keys", [])
        if filter_keys:
            return {k: v for k, v in state.items() if k in filter_keys}
        return state
    
    def _apply_format(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """应用格式化"""
        format_template = self.config.get("format_template", "")
        if format_template:
            formatted = format_template.format(**state)
            return {"formatted_output": formatted}
        return state










"""
数据转换节点
转换和格式化数据
"""
from typing import Dict, Any, Optional, List
import logging
import json

from .base_node import BaseNode, NodeExecutionError

logger = logging.getLogger(__name__)


class DataTransformNode(BaseNode):
    """数据转换节点 - 转换和格式化数据"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        self.transform_type = self.config.get("transform", "identity")
        self.mapping = self.config.get("mapping", {})
        self.filter_keys = self.config.get("filter_keys", [])
        self.format_template = self.config.get("format_template", "")
        self.input_key = self.config.get("input_key", "")
        self.output_key = self.config.get("output_key", f"{self.name}_output")
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行数据转换节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            logger.info(
                f"Data Transform Node '{self.name}' executing "
                f"transform type: {self.transform_type}"
            )
            
            # 获取输入数据
            input_data = state
            if self.input_key:
                input_data = self.get_state_value(state, self.input_key, {})
                if input_data is None:
                    input_data = {}
            
            # 根据转换类型应用转换
            if self.transform_type == "mapping":
                result = self._apply_mapping(input_data, state)
            elif self.transform_type == "filter":
                result = self._apply_filter(input_data)
            elif self.transform_type == "format":
                result = self._apply_format(input_data, state)
            elif self.transform_type == "json_parse":
                result = self._apply_json_parse(input_data)
            elif self.transform_type == "json_stringify":
                result = self._apply_json_stringify(input_data)
            elif self.transform_type == "merge":
                result = self._apply_merge(input_data, state)
            else:
                # 默认：identity（不转换）
                result = input_data.copy() if isinstance(input_data, dict) else input_data
            
            # 将结果添加到状态
            if isinstance(result, dict):
                state.update(result)
            else:
                state[self.output_key] = result
            
            # 添加转换元数据
            state[f"{self.name}_transformed"] = True
            state[f"{self.name}_transform_type"] = self.transform_type
            
            logger.info(f"Data Transform Node '{self.name}' completed successfully")
            
            return state
        
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Data transformation failed: {str(e)}",
                e
            )
    
    def _apply_mapping(self, data: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用字段映射
        
        Args:
            data: 输入数据
            state: 工作流状态
        
        Returns:
            映射后的数据
        """
        result = {}
        
        if not isinstance(data, dict):
            data = {"value": data}
        
        for target_key, source_config in self.mapping.items():
            if isinstance(source_config, str):
                # 简单字段映射
                source_value = self.get_state_value(data, source_config)
                if source_value is not None:
                    result[target_key] = source_value
            elif isinstance(source_config, dict):
                # 复杂映射配置
                source_path = source_config.get("source", "")
                default_value = source_config.get("default")
                transform = source_config.get("transform")
                
                source_value = self.get_state_value(data, source_path, default_value)
                
                # 应用转换函数
                if transform == "upper" and isinstance(source_value, str):
                    source_value = source_value.upper()
                elif transform == "lower" and isinstance(source_value, str):
                    source_value = source_value.lower()
                elif transform == "int" and source_value is not None:
                    try:
                        source_value = int(source_value)
                    except (ValueError, TypeError):
                        source_value = default_value
                elif transform == "float" and source_value is not None:
                    try:
                        source_value = float(source_value)
                    except (ValueError, TypeError):
                        source_value = default_value
                
                result[target_key] = source_value
        
        return result
    
    def _apply_filter(self, data: Any) -> Dict[str, Any]:
        """
        应用过滤
        
        Args:
            data: 输入数据
        
        Returns:
            过滤后的数据
        """
        if not isinstance(data, dict):
            return {"value": data}
        
        if self.filter_keys:
            return {k: v for k, v in data.items() if k in self.filter_keys}
        
        return data
    
    def _apply_format(self, data: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用格式化
        
        Args:
            data: 输入数据
            state: 工作流状态
        
        Returns:
            格式化后的数据
        """
        if self.format_template:
            # 合并数据和状态用于模板解析
            template_context = {**state, **data} if isinstance(data, dict) else {**state, "data": data}
            formatted = self.resolve_template(self.format_template, template_context)
            return {"formatted_output": formatted}
        
        return data if isinstance(data, dict) else {"value": data}
    
    def _apply_json_parse(self, data: Any) -> Any:
        """
        解析JSON字符串
        
        Args:
            data: 输入数据（JSON字符串）
        
        Returns:
            解析后的对象
        """
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                raise NodeExecutionError(
                    self.name,
                    f"JSON parse failed: {str(e)}"
                )
        return data
    
    def _apply_json_stringify(self, data: Any) -> str:
        """
        将对象转换为JSON字符串
        
        Args:
            data: 输入数据
        
        Returns:
            JSON字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise NodeExecutionError(
                self.name,
                f"JSON stringify failed: {str(e)}"
            )
    
    def _apply_merge(self, data: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并数据
        
        Args:
            data: 输入数据
            state: 工作流状态
        
        Returns:
            合并后的数据
        """
        merge_keys = self.config.get("merge_keys", [])
        
        result = {}
        if isinstance(data, dict):
            result.update(data)
        
        for key in merge_keys:
            value = self.get_state_value(state, key)
            if value is not None:
                if isinstance(value, dict) and isinstance(result, dict):
                    result.update(value)
                else:
                    result[key] = value
        
        return result
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        # 检查是否有输入数据
        if self.input_key:
            input_data = self.get_state_value(state, self.input_key)
            if input_data is None:
                logger.warning(
                    f"Data Transform Node '{self.name}' input key '{self.input_key}' not found"
                )
                # 不强制要求，允许使用默认值
                return True
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        # 检查是否有输出
        if self.output_key not in output and f"{self.name}_transformed" not in output:
            logger.warning(f"Data Transform Node '{self.name}' did not produce output")
            return False
        
        return True










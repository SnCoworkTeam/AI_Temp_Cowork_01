"""
测试数据工厂
使用工厂模式生成测试数据
"""
from typing import Optional
from datetime import datetime
from uuid import uuid4
import factory


class ToolDefinitionFactory:
    """工具定义工厂"""
    
    @staticmethod
    def create(
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """创建工具定义"""
        defaults = {
            "id": uuid4(),
            "name": name or f"tool_{uuid4().hex[:8]}",
            "description": description or "Test tool",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            "created_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_batch(count: int, **kwargs):
        """批量创建工具定义"""
        return [
            ToolDefinitionFactory.create(**kwargs)
            for _ in range(count)
        ]


class ToolExecutionFactory:
    """工具执行工厂"""
    
    @staticmethod
    def create(
        tool_id: Optional[str] = None,
        status: str = "completed",
        **kwargs
    ):
        """创建工具执行记录"""
        defaults = {
            "id": uuid4(),
            "tool_id": tool_id or str(uuid4()),
            "input_data": {"input": "test"},
            "output_data": {"result": "success"},
            "status": status,
            "execution_time": 0.5,
            "created_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults










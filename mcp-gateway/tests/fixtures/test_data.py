"""
测试数据生成
"""
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any


def create_tool_definition(
    name: str = "test_tool",
    description: str = "Test tool",
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """创建工具定义测试数据"""
    return {
        "id": str(uuid4()),
        "name": name,
        "description": description,
        "parameters_schema": parameters or {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"]
        },
        "created_at": datetime.utcnow().isoformat()
    }


def create_tool_execution(
    tool_id: str = None,
    input_data: Dict[str, Any] = None,
    status: str = "completed"
) -> Dict[str, Any]:
    """创建工具执行测试数据"""
    return {
        "id": str(uuid4()),
        "tool_id": tool_id or str(uuid4()),
        "input_data": input_data or {"input": "test"},
        "output_data": {"result": "success"},
        "status": status,
        "execution_time": 0.5,
        "created_at": datetime.utcnow().isoformat()
    }


def create_tool_config(
    tool_name: str = "test_tool",
    enabled: bool = True
) -> Dict[str, Any]:
    """创建工具配置测试数据"""
    return {
        "tool_name": tool_name,
        "enabled": enabled,
        "rate_limit": 100,
        "timeout": 30,
        "retry_count": 3
    }










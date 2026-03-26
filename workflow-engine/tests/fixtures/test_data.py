"""
Workflow Engine 测试数据
"""
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any


def create_workflow_definition(
    name: str = "test_workflow",
    description: str = "Test workflow"
) -> Dict[str, Any]:
    """创建工作流定义测试数据"""
    return {
        "id": str(uuid4()),
        "name": name,
        "description": description,
        "status": "draft",
        "config": {
            "nodes": [
                {
                    "id": "node1",
                    "type": "start",
                    "position": {"x": 0, "y": 0}
                }
            ],
            "connections": []
        },
        "created_at": datetime.utcnow().isoformat()
    }


def create_workflow_execution(
    workflow_id: str = None,
    input_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """创建工作流执行测试数据"""
    return {
        "id": str(uuid4()),
        "workflow_id": workflow_id or str(uuid4()),
        "status": "pending",
        "input_data": input_data or {},
        "created_at": datetime.utcnow().isoformat()
    }










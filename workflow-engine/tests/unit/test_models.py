"""
Workflow Engine 模型单元测试
"""
import pytest
from datetime import datetime
from uuid import uuid4


@pytest.mark.unit
class TestWorkflowModels:
    """工作流模型测试"""
    
    def test_workflow_definition_creation(self):
        """测试工作流定义创建"""
        from database.src.models.workflow_models import (
            WorkflowDefinition, WorkflowStatus
        )
        
        workflow = WorkflowDefinition(
            id=uuid4(),
            name="test_workflow",
            description="Test workflow",
            status=WorkflowStatus.DRAFT,
            config={"nodes": [], "connections": []},
            created_at=datetime.utcnow()
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.status == WorkflowStatus.DRAFT
        assert workflow.config == {"nodes": [], "connections": []}
    
    def test_workflow_node_creation(self):
        """测试工作流节点创建"""
        from database.src.models.workflow_models import WorkflowNode
        
        node = WorkflowNode(
            id=uuid4(),
            workflow_id=uuid4(),
            node_id="node1",
            node_type="llm",
            config={"model": "gpt-3.5-turbo"},
            position={"x": 0, "y": 0}
        )
        
        assert node.node_type == "llm"
        assert node.config == {"model": "gpt-3.5-turbo"}


@pytest.mark.unit
class TestExecutionModels:
    """执行模型测试"""
    
    def test_workflow_execution_creation(self):
        """测试工作流执行创建"""
        from database.src.models.workflow_models import (
            WorkflowExecution, ExecutionStatus
        )
        
        execution = WorkflowExecution(
            id=uuid4(),
            workflow_id=uuid4(),
            status=ExecutionStatus.PENDING,
            input_data={"input": "test"},
            created_at=datetime.utcnow()
        )
        
        assert execution.status == ExecutionStatus.PENDING
        assert execution.input_data == {"input": "test"}










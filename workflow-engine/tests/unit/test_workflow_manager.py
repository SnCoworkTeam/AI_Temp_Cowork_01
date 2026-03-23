"""
工作流管理器单元测试
"""
import pytest
import sys
import uuid
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestWorkflowManager:
    """工作流管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建工作流管理器实例"""
        from src.workflows.workflow_manager import WorkflowManager
        return WorkflowManager()
    
    @pytest.fixture
    def sample_workflow(self):
        """示例工作流定义"""
        from src.models.workflow_models import WorkflowDefinition, WorkflowNode
        from shared_libs.schemas.workflow_schemas import NodeType
        
        node = WorkflowNode(
            id="start",
            name="开始",
            node_type=NodeType.START
        )
        
        return WorkflowDefinition(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes=[node],
            start_node_id="start",
            end_node_ids=["start"]
        )
    
    @pytest.mark.asyncio
    async def test_save_workflow(self, manager, sample_workflow):
        """测试保存工作流"""
        workflow_id = await manager.save_workflow(sample_workflow)
        assert workflow_id is not None
        assert workflow_id in manager._workflows
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, manager, sample_workflow):
        """测试获取工作流"""
        workflow_id = await manager.save_workflow(sample_workflow)
        workflow = await manager.get_workflow_by_id(workflow_id)
        assert workflow is not None
        assert workflow.workflow.name == sample_workflow.name
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, manager, sample_workflow):
        """测试列出工作流"""
        await manager.save_workflow(sample_workflow)
        workflows = await manager.list_workflows()
        assert len(workflows) > 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, manager, sample_workflow):
        """测试执行工作流"""
        workflow_id = await manager.save_workflow(sample_workflow)
        
        # execute_workflow接受workflow_name，需要mock execute_workflow_by_id
        with patch.object(manager, 'execute_workflow_by_id', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {
                "execution_id": "exec-123",
                "status": "completed",
                "result": {"output": "test"}
            }
            
            # execute_workflow使用workflow_name
            result = await manager.execute_workflow(sample_workflow.name, {"input": "test"}, {})
            assert result is not None
            assert "execution_id" in result
            assert result["execution_id"] == "exec-123"
    
    @pytest.mark.asyncio
    async def test_delete_workflow(self, manager, sample_workflow):
        """测试删除工作流"""
        workflow_id = await manager.save_workflow(sample_workflow)
        await manager.delete_workflow(workflow_id)
        
        workflow = await manager.get_workflow_by_id(workflow_id)
        assert workflow is None
    
    @pytest.mark.asyncio
    async def test_workflow_overwrite(self, manager, sample_workflow):
        """测试工作流覆盖"""
        workflow_id = await manager.save_workflow(sample_workflow)
        
        # 修改工作流
        sample_workflow.description = "Updated description"
        new_id = await manager.save_workflow(sample_workflow, overwrite=True)
        
        assert new_id == workflow_id
        workflow = await manager.get_workflow_by_id(workflow_id)
        assert workflow.workflow.description == "Updated description"
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, manager, sample_workflow):
        """测试获取执行状态"""
        workflow_id = await manager.save_workflow(sample_workflow)
        
        # 创建执行记录
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        manager._executions[execution_id] = {
            "workflow_id": workflow_id,
            "status": "running",
            "input": {"input": "test"},
            "output": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # get_execution_status不是async方法
        status = manager.get_execution_status(execution_id)
        assert status is not None
        assert status["status"] == "running"

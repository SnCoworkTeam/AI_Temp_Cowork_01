"""
动态工作流引擎单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestDynamicWorkflowEngine:
    """动态工作流引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建动态工作流引擎实例"""
        from src.core.dynamic_workflow_engine import DynamicWorkflowEngine
        return DynamicWorkflowEngine()
    
    @pytest.fixture
    def sample_config(self):
        """示例工作流配置"""
        return {
            "name": "test_workflow",
            "description": "测试工作流",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "name": "开始"
                },
                {
                    "id": "end",
                    "type": "end",
                    "name": "结束"
                }
            ],
            "connections": [
                {
                    "source": {"node_id": "start"},
                    "target": {"node_id": "end"}
                }
            ],
            "start_node_id": "start",
            "end_node_ids": ["end"]
        }
    
    def test_build_from_config(self, engine, sample_config):
        """测试从配置构建工作流"""
        workflow_id = engine.build_from_config(sample_config)
        assert workflow_id is not None
        assert workflow_id in engine._workflows
    
    def test_get_workflow(self, engine, sample_config):
        """测试获取工作流"""
        workflow_id = engine.build_from_config(sample_config)
        workflow = engine.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow.name == "test_workflow"
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, engine, sample_config):
        """测试执行工作流"""
        workflow_id = engine.build_from_config(sample_config)
        
        with patch.object(engine, '_execute_graph', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "completed", "output": {}}
            
            result = await engine.execute_workflow(workflow_id, {"input": "test"})
            assert result is not None
    
    def test_list_workflows(self, engine, sample_config):
        """测试列出工作流"""
        engine.build_from_config(sample_config)
        workflows = engine.list_workflows()
        assert len(workflows) > 0
    
    def test_delete_workflow(self, engine, sample_config):
        """测试删除工作流"""
        workflow_id = engine.build_from_config(sample_config)
        engine.delete_workflow(workflow_id)
        
        workflow = engine.get_workflow(workflow_id)
        assert workflow is None


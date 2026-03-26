"""
工作流管理器（数据库版本）单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestWorkflowManagerDB:
    """工作流管理器（数据库版本）测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def manager(self, mock_db):
        """创建工作流管理器实例"""
        from src.workflows.workflow_manager_db import WorkflowManagerDB
        return WorkflowManagerDB(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, manager, mock_db):
        """测试创建工作流"""
        workflow_data = {
            "name": "test_workflow",
            "description": "Test",
            "version": "1.0.0",
            "nodes": [],
            "connections": [],
            "start_node_id": "start",
            "end_node_ids": ["end"]
        }
        
        with patch.object(manager, '_workflow_repo') as mock_repo:
            mock_workflow = MagicMock()
            mock_workflow.id = uuid4()
            mock_repo.create.return_value = mock_workflow
            
            result = await manager.create_workflow(workflow_data)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, manager, mock_db):
        """测试获取工作流"""
        workflow_id = uuid4()
        
        with patch.object(manager, '_workflow_repo') as mock_repo:
            mock_workflow = MagicMock()
            mock_repo.get_by_id.return_value = mock_workflow
            
            result = await manager.get_workflow(workflow_id)
            assert result == mock_workflow
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, manager, mock_db):
        """测试列出工作流"""
        with patch.object(manager, '_workflow_repo') as mock_repo:
            mock_workflows = [MagicMock(), MagicMock()]
            mock_repo.list.return_value = mock_workflows
            
            result = await manager.list_workflows(skip=0, limit=10)
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, manager, mock_db):
        """测试更新工作流"""
        workflow_id = uuid4()
        updates = {"description": "Updated"}
        
        with patch.object(manager, '_workflow_repo') as mock_repo:
            mock_workflow = MagicMock()
            mock_repo.get_by_id.return_value = mock_workflow
            mock_repo.update.return_value = mock_workflow
            
            result = await manager.update_workflow(workflow_id, **updates)
            assert result == mock_workflow
    
    @pytest.mark.asyncio
    async def test_delete_workflow(self, manager, mock_db):
        """测试删除工作流"""
        workflow_id = uuid4()
        
        with patch.object(manager, '_workflow_repo') as mock_repo:
            mock_workflow = MagicMock()
            mock_repo.get_by_id.return_value = mock_workflow
            
            result = await manager.delete_workflow(workflow_id)
            assert result is True


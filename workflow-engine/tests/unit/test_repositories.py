"""
工作流Repository单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestWorkflowRepository:
    """工作流Repository测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        session = MagicMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """创建工作流Repository实例"""
        from src.repositories.workflow_repository import WorkflowRepository
        return WorkflowRepository(mock_session)
    
    def test_create_workflow(self, repository, mock_session):
        """测试创建工作流"""
        # Mock get_by_name_and_version返回None（工作流不存在）
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.create_workflow(
            name="test_workflow",
            description="Test",
            version="1.0.0"
        )
        assert mock_session.add.called
        assert mock_session.flush.called
        assert result is not None
    
    def test_get_by_id(self, repository, mock_session):
        """测试根据ID获取工作流"""
        workflow_id = uuid4()
        mock_workflow = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_workflow
        
        result = repository.get_by_id(workflow_id)
        assert result == mock_workflow
    
    def test_get_by_name(self, repository, mock_session):
        """测试根据名称获取工作流"""
        mock_workflow = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_workflow
        
        result = repository.get_by_name("test_workflow")
        assert result == mock_workflow
    
    def test_list_workflows(self, repository, mock_session):
        """测试列出工作流"""
        mock_workflows = [MagicMock(), MagicMock()]
        # Mock _db_repo.get_all方法
        repository._db_repo.get_all = MagicMock(return_value=mock_workflows)
        
        result = repository.list_workflows(skip=0, limit=10)
        assert len(result) == 2
        repository._db_repo.get_all.assert_called_once()
    
    def test_update_workflow(self, repository, mock_session):
        """测试更新工作流"""
        workflow_id = str(uuid4())
        updates = {"description": "Updated"}
        
        mock_workflow = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_workflow
        
        result = repository.update_workflow(workflow_id, **updates)
        assert result is not None


@pytest.mark.unit
class TestExecutionRepository:
    """执行Repository测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def repository(self, mock_session):
        """创建执行Repository实例"""
        from src.repositories.execution_repository import ExecutionRepository
        return ExecutionRepository(mock_session)
    
    def test_create_execution(self, repository, mock_session):
        """测试创建执行记录"""
        workflow_id = str(uuid4())
        
        result = repository.create_execution(
            workflow_id=workflow_id,
            input_data={}
        )
        assert mock_session.add.called
        assert mock_session.flush.called
        assert result is not None
    
    def test_get_by_id(self, repository, mock_session):
        """测试根据ID获取执行记录"""
        execution_id = str(uuid4())
        mock_execution = MagicMock()
        repository._db_repo.get_by_id = MagicMock(return_value=mock_execution)
        
        result = repository.get_by_id(execution_id)
        assert result == mock_execution
    
    def test_list_executions(self, repository, mock_session):
        """测试列出执行记录"""
        workflow_id = str(uuid4())
        mock_executions = [MagicMock(), MagicMock()]
        repository._db_repo.get_by_workflow_id = MagicMock(return_value=mock_executions)
        
        result = repository.get_by_workflow_id(workflow_id, skip=0, limit=10)
        assert len(result) == 2
        repository._db_repo.get_by_workflow_id.assert_called_once()


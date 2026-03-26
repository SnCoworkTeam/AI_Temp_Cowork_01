"""
状态管理器单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestWorkflowStateManager:
    """工作流状态管理器测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()
    
    @pytest.fixture
    def state_manager(self, mock_db):
        """创建状态管理器实例"""
        from src.core.state_manager import WorkflowStateManager
        return WorkflowStateManager(mock_db)
    
    @pytest.mark.asyncio
    async def test_save_state(self, state_manager, mock_db):
        """测试保存状态"""
        # Mock execution repository
        mock_execution = MagicMock()
        mock_execution.metadata = {}
        
        with patch('src.repositories.execution_repository.ExecutionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_execution
            mock_repo_class.return_value = mock_repo
            
            with patch.object(state_manager, '_get_redis', new_callable=AsyncMock) as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                
                result = await state_manager.save_state("exec-123", {"key": "value"}, is_active=True)
                assert result is True
                assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_load_state_from_cache(self, state_manager):
        """测试从缓存加载状态"""
        with patch.object(state_manager, '_get_redis', new_callable=AsyncMock) as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.get.return_value = '{"key": "cached_value"}'
            
            state = await state_manager.load_state("exec-123", prefer_cache=True)
            assert state == {"key": "cached_value"}
    
    @pytest.mark.asyncio
    async def test_load_state_from_database(self, state_manager, mock_db):
        """测试从数据库加载状态"""
        mock_execution = MagicMock()
        mock_execution.metadata = {
            "state_snapshot": {
                "data": {"key": "db_value"},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        mock_execution.status.value = "running"
        
        with patch('src.repositories.execution_repository.ExecutionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_execution
            mock_repo_class.return_value = mock_repo
            
            with patch.object(state_manager, '_get_redis', new_callable=AsyncMock) as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                mock_redis_client.get.return_value = None
                
                state = await state_manager.load_state("exec-123", prefer_cache=False)
                assert state == {"key": "db_value"}
    
    @pytest.mark.asyncio
    async def test_update_state(self, state_manager):
        """测试更新状态"""
        with patch.object(state_manager, 'load_state', new_callable=AsyncMock) as mock_load:
            with patch.object(state_manager, 'save_state', new_callable=AsyncMock) as mock_save:
                mock_load.return_value = {"existing": "value"}
                mock_save.return_value = True
                
                result = await state_manager.update_state("exec-123", {"new": "data"}, merge=True)
                assert result is True
                mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_state(self, state_manager):
        """测试删除状态"""
        with patch.object(state_manager, '_get_redis', new_callable=AsyncMock) as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            result = await state_manager.delete_state("exec-123", clear_cache=True)
            assert result is True
            mock_redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_executions(self, state_manager):
        """测试获取活跃执行列表"""
        with patch.object(state_manager, '_get_redis', new_callable=AsyncMock) as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.smembers.return_value = [b"exec-1", b"exec-2"]
            
            executions = await state_manager.get_active_executions()
            assert len(executions) == 2
            assert "exec-1" in executions
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self, state_manager, mock_db):
        """测试保存检查点"""
        mock_execution = MagicMock()
        mock_execution.metadata = {}
        
        with patch('src.repositories.execution_repository.ExecutionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_execution
            mock_repo_class.return_value = mock_repo
            
            result = await state_manager.save_checkpoint(
                "exec-123",
                "checkpoint_1",
                {"state": "data"},
                {"metadata": "info"}
            )
            assert result is True
            assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_load_checkpoint(self, state_manager, mock_db):
        """测试加载检查点"""
        mock_execution = MagicMock()
        mock_execution.metadata = {
            "checkpoints": {
                "checkpoint_1": {
                    "state": {"key": "value"},
                    "metadata": {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "latest_checkpoint": "checkpoint_1"
        }
        
        with patch('src.repositories.execution_repository.ExecutionRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_execution
            mock_repo_class.return_value = mock_repo
            
            checkpoint = await state_manager.load_checkpoint("exec-123", "checkpoint_1")
            assert checkpoint is not None
            assert checkpoint["state"] == {"key": "value"}


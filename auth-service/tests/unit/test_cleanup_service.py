"""
清理服务单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestCleanupService:
    """清理服务测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_blacklist_repo(self):
        """模拟黑名单仓库"""
        repo = MagicMock()
        repo.cleanup_expired = AsyncMock(return_value=10)
        return repo

    @pytest.fixture
    def cleanup_service(self, mock_db, mock_blacklist_repo):
        """创建CleanupService实例"""
        with patch('src.services.cleanup_service.TokenBlacklistRepository', return_value=mock_blacklist_repo):
            from src.services.cleanup_service import CleanupService
            service = CleanupService(mock_db)
            service.blacklist_repo = mock_blacklist_repo
            return service

    def test_cleanup_service_initialization(self, cleanup_service, mock_db):
        """测试清理服务初始化"""
        assert cleanup_service is not None
        assert cleanup_service.db == mock_db
        assert cleanup_service.blacklist_repo is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_blacklist_tokens_success(self, cleanup_service, mock_blacklist_repo):
        """测试清理过期黑名单令牌成功"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(return_value=15)

        result = await cleanup_service.cleanup_expired_blacklist_tokens()

        assert result == 15
        mock_blacklist_repo.cleanup_expired.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_blacklist_tokens_zero(self, cleanup_service, mock_blacklist_repo):
        """测试没有过期令牌需要清理"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(return_value=0)

        result = await cleanup_service.cleanup_expired_blacklist_tokens()

        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_blacklist_tokens_error(self, cleanup_service, mock_blacklist_repo):
        """测试清理过期令牌时发生错误"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(side_effect=Exception("Database error"))

        result = await cleanup_service.cleanup_expired_blacklist_tokens()

        assert result == 0  # 错误时返回0

    @pytest.mark.asyncio
    async def test_cleanup_all_success(self, cleanup_service, mock_blacklist_repo):
        """测试执行所有清理任务成功"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(return_value=20)

        result = await cleanup_service.cleanup_all()

        assert "blacklist_tokens" in result
        assert result["blacklist_tokens"] == 20
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)

    @pytest.mark.asyncio
    async def test_cleanup_all_with_error(self, cleanup_service, mock_blacklist_repo):
        """测试清理任务发生错误"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(side_effect=Exception("Cleanup error"))

        result = await cleanup_service.cleanup_all()

        # 即使发生错误也应返回结果
        assert "blacklist_tokens" in result
        assert result["blacklist_tokens"] == 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_cleanup_all_timestamp_format(self, cleanup_service):
        """测试清理结果时间戳格式"""
        result = await cleanup_service.cleanup_all()

        assert "timestamp" in result
        # 验证时间戳是ISO格式
        timestamp = result["timestamp"]
        datetime.fromisoformat(timestamp)  # 如果格式不正确会抛出异常

    @pytest.mark.asyncio
    async def test_run_cleanup_task_success(self, mock_db):
        """测试运行清理任务（全局函数）"""
        with patch('src.services.cleanup_service.CleanupService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.cleanup_all = AsyncMock(return_value={"blacklist_tokens": 5, "timestamp": "2024-01-01"})
            mock_service_class.return_value = mock_service

            from src.services.cleanup_service import run_cleanup_task

            result = await run_cleanup_task(mock_db)

            assert result["blacklist_tokens"] == 5
            mock_service.cleanup_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_cleanup_cycles(self, cleanup_service, mock_blacklist_repo):
        """测试多次清理循环"""
        # 模拟多次清理，每次清理不同数量的记录
        cleanup_counts = [10, 5, 2, 0]
        mock_blacklist_repo.cleanup_expired = AsyncMock(side_effect=cleanup_counts)

        results = []
        for _ in range(4):
            result = await cleanup_service.cleanup_expired_blacklist_tokens()
            results.append(result)

        assert results == cleanup_counts
        assert mock_blacklist_repo.cleanup_expired.call_count == 4

    @pytest.mark.asyncio
    async def test_cleanup_all_with_partial_failure(self, cleanup_service, mock_blacklist_repo):
        """测试部分清理任务失败"""
        # 黑名单清理失败但不应该中断整个清理流程
        mock_blacklist_repo.cleanup_expired = AsyncMock(side_effect=Exception("Partial failure"))

        result = await cleanup_service.cleanup_all()

        # 应该返回结果，即使某些任务失败
        assert result is not None
        assert "timestamp" in result
        assert result["blacklist_tokens"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_service_concurrent_calls(self, cleanup_service, mock_blacklist_repo):
        """测试并发清理调用"""
        import asyncio

        mock_blacklist_repo.cleanup_expired = AsyncMock(return_value=3)

        # 模拟并发调用
        tasks = [
            cleanup_service.cleanup_expired_blacklist_tokens()
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)

        assert all(r == 3 for r in results)
        assert mock_blacklist_repo.cleanup_expired.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_logging(self, cleanup_service, mock_blacklist_repo):
        """测试清理日志记录"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(return_value=7)

        with patch('src.services.cleanup_service.logger') as mock_logger:
            await cleanup_service.cleanup_expired_blacklist_tokens()

            # 验证日志被调用
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "7" in log_message
            assert "expired blacklist records" in log_message.lower()

    @pytest.mark.asyncio
    async def test_cleanup_error_logging(self, cleanup_service, mock_blacklist_repo):
        """测试清理错误日志记录"""
        mock_blacklist_repo.cleanup_expired = AsyncMock(side_effect=Exception("Test error"))

        with patch('src.services.cleanup_service.logger') as mock_logger:
            result = await cleanup_service.cleanup_expired_blacklist_tokens()

            assert result == 0
            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "Failed to cleanup" in log_message

"""
数据分类定时任务调度器单元测试
"""
import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestClassificationScheduler:
    """数据分类定时任务调度器测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        return db

    @pytest.fixture
    def scheduler(self, mock_db):
        """创建ClassificationScheduler实例"""
        from src.services.classification_scheduler import ClassificationScheduler
        return ClassificationScheduler(mock_db, interval_minutes=1)

    def test_scheduler_initialization(self, scheduler, mock_db):
        """测试调度器初始化"""
        assert scheduler is not None
        assert scheduler.db == mock_db
        assert scheduler.interval_minutes == 1
        assert scheduler.is_running is False
        assert scheduler.task is None
        assert scheduler.last_run is None
        assert scheduler.run_count == 0
        assert scheduler.error_count == 0

    def test_scheduler_with_custom_interval(self, mock_db):
        """测试自定义时间间隔"""
        from src.services.classification_scheduler import ClassificationScheduler
        scheduler = ClassificationScheduler(mock_db, interval_minutes=30)

        assert scheduler.interval_minutes == 30

    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler):
        """测试启动调度器"""
        with patch.object(scheduler, '_run_periodically', new_callable=AsyncMock):
            await scheduler.start()

            assert scheduler.is_running is True
            assert scheduler.task is not None

            # 清理
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_scheduler_already_running(self, scheduler):
        """测试重复启动调度器"""
        with patch.object(scheduler, '_run_periodically', new_callable=AsyncMock):
            await scheduler.start()
            assert scheduler.is_running is True

            # 尝试再次启动
            with patch('src.services.classification_scheduler.logger') as mock_logger:
                await scheduler.start()
                mock_logger.warning.assert_called_once()

            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler):
        """测试停止调度器"""
        with patch.object(scheduler, '_run_periodically', new_callable=AsyncMock):
            await scheduler.start()
            assert scheduler.is_running is True

            await scheduler.stop()

            assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_stop_scheduler_not_running(self, scheduler):
        """测试停止未运行的调度器"""
        assert scheduler.is_running is False

        # 应该能正常停止，不抛出异常
        await scheduler.stop()

        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_run_classification_success(self, scheduler):
        """测试执行分类任务成功"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={
            "success": True,
            "classified_assets": 10,
            "persisted_assets": 10
        })
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            await scheduler._run_classification()

            assert scheduler.run_count == 1
            assert scheduler.last_run is not None
            assert isinstance(scheduler.last_run, datetime)
            mock_classifier.classify_data_assets.assert_called_once_with(persist=True)
            mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_classification_error(self, scheduler):
        """测试执行分类任务失败"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(side_effect=Exception("Classification error"))
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            with pytest.raises(Exception) as exc_info:
                await scheduler._run_classification()

            assert "Classification error" in str(exc_info.value)
            assert scheduler.error_count == 1
            mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_classification_multiple_times(self, scheduler):
        """测试多次执行分类任务"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={
            "classified_assets": 5,
            "persisted_assets": 5
        })
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            await scheduler._run_classification()
            await scheduler._run_classification()
            await scheduler._run_classification()

            assert scheduler.run_count == 3
            assert mock_classifier.classify_data_assets.call_count == 3

    @pytest.mark.asyncio
    async def test_run_periodically_cancellation(self, scheduler):
        """测试定期执行任务的取消"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={"classified_assets": 1})
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            # 启动任务
            scheduler.is_running = True
            task = asyncio.create_task(scheduler._run_periodically())

            # 等待一小段时间
            await asyncio.sleep(0.1)

            # 停止任务
            scheduler.is_running = False
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_run_periodically_with_errors(self, scheduler):
        """测试定期执行任务中的错误处理"""
        mock_classifier = MagicMock()
        # 第一次调用失败，第二次成功
        mock_classifier.classify_data_assets = AsyncMock(
            side_effect=[Exception("Error"), {"classified_assets": 1}]
        )
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            with patch('src.services.classification_scheduler.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                scheduler.is_running = True
                task = asyncio.create_task(scheduler._run_periodically())

                # 等待执行
                await asyncio.sleep(0.2)

                scheduler.is_running = False
                task.cancel()

                try:
                    await task
                except asyncio.CancelledError:
                    pass

                # 验证错误计数增加
                assert scheduler.error_count >= 1

    def test_get_status(self, scheduler):
        """测试获取调度器状态"""
        status = scheduler.get_status()

        assert "is_running" in status
        assert status["is_running"] is False
        assert "interval_minutes" in status
        assert status["interval_minutes"] == 1
        assert "last_run" in status
        assert status["last_run"] is None
        assert "run_count" in status
        assert status["run_count"] == 0
        assert "error_count" in status
        assert status["error_count"] == 0
        assert "next_run_estimate" in status
        assert status["next_run_estimate"] is None

    @pytest.mark.asyncio
    async def test_get_status_after_run(self, scheduler):
        """测试运行后的状态"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={"classified_assets": 5})
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            await scheduler._run_classification()

            status = scheduler.get_status()

            assert status["run_count"] == 1
            assert status["last_run"] is not None
            assert status["next_run_estimate"] is not None

            # 验证next_run_estimate是有效的ISO时间戳
            next_run = datetime.fromisoformat(status["next_run_estimate"])
            assert isinstance(next_run, datetime)

    @pytest.mark.asyncio
    async def test_scheduler_logging(self, scheduler):
        """测试日志记录"""
        with patch('src.services.classification_scheduler.logger') as mock_logger:
            with patch.object(scheduler, '_run_periodically', new_callable=AsyncMock):
                await scheduler.start()
                mock_logger.info.assert_called_with(
                    f"Classification scheduler started (interval: {scheduler.interval_minutes} minutes)"
                )

                await scheduler.stop()
                mock_logger.info.assert_called_with("Classification scheduler stopped")

    @pytest.mark.asyncio
    async def test_run_classification_logging(self, scheduler):
        """测试分类任务执行日志"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={
            "classified_assets": 8,
            "persisted_assets": 7
        })
        mock_classifier.close = AsyncMock()

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            with patch('src.services.classification_scheduler.logger') as mock_logger:
                await scheduler._run_classification()

                # 验证日志包含分类信息
                calls = [str(call) for call in mock_logger.info.call_args_list]
                log_output = " ".join(calls)
                assert "Classification completed" in log_output or "Starting" in log_output

    @pytest.mark.asyncio
    async def test_scheduler_interval_zero(self, mock_db):
        """测试零时间间隔（边界情况）"""
        from src.services.classification_scheduler import ClassificationScheduler
        scheduler = ClassificationScheduler(mock_db, interval_minutes=0)

        assert scheduler.interval_minutes == 0

        # 应该能正常创建，但不建议使用
        status = scheduler.get_status()
        assert status["interval_minutes"] == 0

    @pytest.mark.asyncio
    async def test_error_count_increment(self, scheduler):
        """测试错误计数递增"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(side_effect=Exception("Test error"))
        mock_classifier.close = AsyncMock()

        initial_error_count = scheduler.error_count

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            for i in range(3):
                try:
                    await scheduler._run_classification()
                except Exception:
                    pass

        assert scheduler.error_count == initial_error_count + 3

    @pytest.mark.asyncio
    async def test_last_run_timestamp_update(self, scheduler):
        """测试last_run时间戳更新"""
        mock_classifier = MagicMock()
        mock_classifier.classify_data_assets = AsyncMock(return_value={"classified_assets": 1})
        mock_classifier.close = AsyncMock()

        assert scheduler.last_run is None

        with patch('src.services.classification_scheduler.DataClassifier', return_value=mock_classifier):
            first_run_time = datetime.now()
            await scheduler._run_classification()
            first_last_run = scheduler.last_run

            assert first_last_run is not None
            assert first_last_run >= first_run_time

            # 等待一小段时间再执行
            await asyncio.sleep(0.1)
            await scheduler._run_classification()
            second_last_run = scheduler.last_run

            assert second_last_run > first_last_run

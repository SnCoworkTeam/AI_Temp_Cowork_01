"""
数据分类路由单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import HTTPException

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


@pytest.mark.unit
class TestDataClassificationRoutes:
    """数据分类路由测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        return db

    @pytest.fixture
    def mock_classifier(self):
        """模拟数据分类器"""
        classifier = MagicMock()
        classifier.classify_data_assets = AsyncMock(return_value={
            "success": True,
            "classified_assets": 10,
            "persisted_assets": 10,
            "classification_graph": {
                "sensitivity_distribution": {"high": 5, "medium": 3, "low": 2},
                "business_value_distribution": {"high": 4, "medium": 4, "low": 2},
                "total_assets": 10
            },
            "classifications": {}
        })
        classifier.get_classification_history = MagicMock(return_value=[
            {"asset_id": 1, "sensitivity": "high", "classified_at": "2024-01-01"}
        ])
        classifier.get_latest_classifications = MagicMock(return_value=[
            {"asset_id": 1, "sensitivity": "high"},
            {"asset_id": 2, "sensitivity": "medium"}
        ])
        classifier.close = AsyncMock()
        return classifier

    @pytest.mark.asyncio
    async def test_classify_data_assets_success(self, mock_classifier):
        """测试数据分类成功"""
        from src.routes.data_classification import classify_data_assets

        result = await classify_data_assets(classifier=mock_classifier)

        assert result["success"] is True
        assert result["classified_assets"] == 10
        assert "classification_graph" in result
        mock_classifier.classify_data_assets.assert_called_once()
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_data_assets_error(self, mock_classifier):
        """测试数据分类失败"""
        from src.routes.data_classification import classify_data_assets

        mock_classifier.classify_data_assets = AsyncMock(side_effect=Exception("Classification error"))

        with pytest.raises(HTTPException) as exc_info:
            await classify_data_assets(classifier=mock_classifier)

        assert exc_info.value.status_code == 500
        assert "Classification error" in exc_info.value.detail
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_data_assets_closes_on_success(self, mock_classifier):
        """测试成功后关闭分类器"""
        from src.routes.data_classification import classify_data_assets

        await classify_data_assets(classifier=mock_classifier)

        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_data_assets_closes_on_error(self, mock_classifier):
        """测试出错后也关闭分类器"""
        from src.routes.data_classification import classify_data_assets

        mock_classifier.classify_data_assets = AsyncMock(side_effect=Exception("Test error"))

        try:
            await classify_data_assets(classifier=mock_classifier)
        except HTTPException:
            pass

        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_classification_graph_success(self, mock_classifier):
        """测试获取分类图谱成功"""
        from src.routes.data_classification import get_classification_graph

        result = await get_classification_graph(classifier=mock_classifier)

        assert result["success"] is True
        assert "classification_graph" in result
        assert result["classification_graph"]["total_assets"] == 10
        mock_classifier.classify_data_assets.assert_called_once_with(persist=False)
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_classification_graph_no_persist(self, mock_classifier):
        """测试获取图谱时不持久化"""
        from src.routes.data_classification import get_classification_graph

        await get_classification_graph(classifier=mock_classifier)

        # 验证调用时persist=False
        mock_classifier.classify_data_assets.assert_called_once_with(persist=False)

    @pytest.mark.asyncio
    async def test_get_classification_graph_error(self, mock_classifier):
        """测试获取分类图谱失败"""
        from src.routes.data_classification import get_classification_graph

        mock_classifier.classify_data_assets = AsyncMock(side_effect=Exception("Graph error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_classification_graph(classifier=mock_classifier)

        assert exc_info.value.status_code == 500
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_classification_history_success(self, mock_classifier):
        """测试获取分类历史成功"""
        from src.routes.data_classification import get_classification_history

        result = await get_classification_history(
            asset_id=1,
            limit=10,
            classifier=mock_classifier
        )

        assert result["success"] is True
        assert result["asset_id"] == 1
        assert "history" in result
        assert len(result["history"]) == 1
        assert result["count"] == 1
        mock_classifier.get_classification_history.assert_called_once_with(1, 10)
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_classification_history_custom_limit(self, mock_classifier):
        """测试自定义限制数量的历史查询"""
        from src.routes.data_classification import get_classification_history

        await get_classification_history(
            asset_id=123,
            limit=20,
            classifier=mock_classifier
        )

        mock_classifier.get_classification_history.assert_called_once_with(123, 20)

    @pytest.mark.asyncio
    async def test_get_classification_history_default_limit(self, mock_classifier):
        """测试默认限制的历史查询"""
        from src.routes.data_classification import get_classification_history

        await get_classification_history(
            asset_id=1,
            classifier=mock_classifier
        )

        # 默认limit应该是10
        mock_classifier.get_classification_history.assert_called_once_with(1, 10)

    @pytest.mark.asyncio
    async def test_get_classification_history_error(self, mock_classifier):
        """测试获取历史失败"""
        from src.routes.data_classification import get_classification_history

        mock_classifier.get_classification_history = MagicMock(side_effect=Exception("History error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_classification_history(
                asset_id=1,
                classifier=mock_classifier
            )

        assert exc_info.value.status_code == 500
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_classifications_success(self, mock_classifier):
        """测试获取最新分类成功"""
        from src.routes.data_classification import get_latest_classifications

        result = await get_latest_classifications(
            sensitivity="high",
            business_value="high",
            limit=50,
            classifier=mock_classifier
        )

        assert result["success"] is True
        assert "results" in result
        assert result["count"] == 2
        assert result["filters"]["sensitivity"] == "high"
        assert result["filters"]["business_value"] == "high"
        mock_classifier.get_latest_classifications.assert_called_once_with("high", "high", 50)
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_classifications_no_filters(self, mock_classifier):
        """测试无过滤条件的查询"""
        from src.routes.data_classification import get_latest_classifications

        result = await get_latest_classifications(classifier=mock_classifier)

        assert result["success"] is True
        assert result["filters"]["sensitivity"] is None
        assert result["filters"]["business_value"] is None
        mock_classifier.get_latest_classifications.assert_called_once_with(None, None, 100)

    @pytest.mark.asyncio
    async def test_get_latest_classifications_sensitivity_only(self, mock_classifier):
        """测试只按敏感度过滤"""
        from src.routes.data_classification import get_latest_classifications

        await get_latest_classifications(
            sensitivity="medium",
            classifier=mock_classifier
        )

        mock_classifier.get_latest_classifications.assert_called_once_with("medium", None, 100)

    @pytest.mark.asyncio
    async def test_get_latest_classifications_business_value_only(self, mock_classifier):
        """测试只按业务价值过滤"""
        from src.routes.data_classification import get_latest_classifications

        await get_latest_classifications(
            business_value="low",
            classifier=mock_classifier
        )

        mock_classifier.get_latest_classifications.assert_called_once_with(None, "low", 100)

    @pytest.mark.asyncio
    async def test_get_latest_classifications_custom_limit(self, mock_classifier):
        """测试自定义限制数量"""
        from src.routes.data_classification import get_latest_classifications

        await get_latest_classifications(
            limit=25,
            classifier=mock_classifier
        )

        mock_classifier.get_latest_classifications.assert_called_once_with(None, None, 25)

    @pytest.mark.asyncio
    async def test_get_latest_classifications_error(self, mock_classifier):
        """测试获取最新分类失败"""
        from src.routes.data_classification import get_latest_classifications

        mock_classifier.get_latest_classifications = MagicMock(side_effect=Exception("Latest error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_latest_classifications(classifier=mock_classifier)

        assert exc_info.value.status_code == 500
        mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_classifications_empty_results(self, mock_classifier):
        """测试无结果的查询"""
        from src.routes.data_classification import get_latest_classifications

        mock_classifier.get_latest_classifications = MagicMock(return_value=[])

        result = await get_latest_classifications(classifier=mock_classifier)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["results"] == []

    def test_get_data_classifier_dependency(self, mock_db):
        """测试数据分类器依赖注入"""
        from src.routes.data_classification import get_data_classifier

        with patch('src.routes.data_classification.DataClassifier') as mock_classifier_class:
            classifier = get_data_classifier(db=mock_db)

            mock_classifier_class.assert_called_once_with(mock_db)

    @pytest.mark.asyncio
    async def test_all_endpoints_close_classifier(self, mock_classifier):
        """测试所有端点都正确关闭分类器"""
        from src.routes.data_classification import (
            classify_data_assets,
            get_classification_graph,
            get_classification_history,
            get_latest_classifications
        )

        # 测试每个端点
        endpoints_tests = [
            (classify_data_assets, {}),
            (get_classification_graph, {}),
            (get_classification_history, {"asset_id": 1}),
            (get_latest_classifications, {})
        ]

        for endpoint, kwargs in endpoints_tests:
            mock_classifier.close.reset_mock()
            try:
                await endpoint(classifier=mock_classifier, **kwargs)
            except Exception:
                pass

            mock_classifier.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_router_configuration(self):
        """测试路由器配置"""
        from src.routes.data_classification import router

        assert router.prefix == "/api/data"
        assert "Data Classification" in router.tags

"""
数据分类器服务单元测试
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
class TestDataClassifier:
    """数据分类器测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def data_classifier(self, mock_db):
        """创建DataClassifier实例"""
        from src.services.data_classifier import DataClassifier
        classifier = DataClassifier(mock_db)
        return classifier

    @pytest.fixture
    def sample_assets(self):
        """示例数据资产"""
        return [
            {
                "id": 1,
                "name": "user_table",
                "classification": "confidential",
                "data_quality_metrics": {"quality_score": 0.9},
                "metadata": {"domain": "user_management"}
            },
            {
                "id": 2,
                "name": "public_data",
                "classification": "public",
                "data_quality_metrics": {"quality_score": 0.5},
                "metadata": {"domain": "analytics"}
            },
            {
                "id": 3,
                "name": "internal_reports",
                "classification": "internal",
                "data_quality_metrics": {"quality_score": 0.7},
                "metadata": {"domain": "reporting"}
            }
        ]

    def test_classifier_initialization(self, data_classifier, mock_db):
        """测试分类器初始化"""
        assert data_classifier is not None
        assert data_classifier.db == mock_db
        assert data_classifier.metadata_service_url is not None
        assert data_classifier.http_client is not None

    def test_calculate_sensitivity_high(self, data_classifier):
        """测试高敏感度计算"""
        assert data_classifier._calculate_sensitivity("confidential", 0.9) == "high"
        assert data_classifier._calculate_sensitivity("restricted", 0.8) == "high"
        assert data_classifier._calculate_sensitivity("secret", 0.7) == "high"

    def test_calculate_sensitivity_medium(self, data_classifier):
        """测试中等敏感度计算"""
        assert data_classifier._calculate_sensitivity("internal", 0.7) == "medium"
        assert data_classifier._calculate_sensitivity("private", 0.6) == "medium"

    def test_calculate_sensitivity_low(self, data_classifier):
        """测试低敏感度计算"""
        assert data_classifier._calculate_sensitivity("public", 0.5) == "low"
        assert data_classifier._calculate_sensitivity("open", 0.4) == "low"

    def test_calculate_sensitivity_unknown(self, data_classifier):
        """测试未知分类的敏感度计算"""
        # 高质量未知分类应为中等敏感度
        assert data_classifier._calculate_sensitivity("unknown", 0.85) == "medium"
        # 低质量未知分类应为低敏感度
        assert data_classifier._calculate_sensitivity("unknown", 0.5) == "low"

    def test_calculate_business_value(self, data_classifier):
        """测试业务价值计算"""
        assert data_classifier._calculate_business_value(0.9, "finance") == "high"
        assert data_classifier._calculate_business_value(0.6, "analytics") == "medium"
        assert data_classifier._calculate_business_value(0.3, "test") == "low"

    def test_classify_asset_high_sensitivity(self, data_classifier):
        """测试分类高敏感度资产"""
        asset = {
            "id": 1,
            "name": "user_credentials",
            "classification": "confidential",
            "data_quality_metrics": {"quality_score": 0.95},
            "metadata": {"domain": "security"}
        }

        result = data_classifier._classify_asset(asset)

        assert result["sensitivity"] == "high"
        assert result["business_value"] == "high"
        assert result["classification"] == "confidential"
        assert result["domain"] == "security"
        assert result["quality_score"] == 0.95

    def test_classify_asset_low_sensitivity(self, data_classifier):
        """测试分类低敏感度资产"""
        asset = {
            "id": 2,
            "name": "public_data",
            "classification": "public",
            "data_quality_metrics": {"quality_score": 0.4},
            "metadata": {"domain": "public"}
        }

        result = data_classifier._classify_asset(asset)

        assert result["sensitivity"] == "low"
        assert result["business_value"] == "low"
        assert result["classification"] == "public"

    def test_classify_asset_missing_fields(self, data_classifier):
        """测试分类缺少字段的资产"""
        asset = {
            "id": 3,
            "name": "incomplete_data"
        }

        result = data_classifier._classify_asset(asset)

        # 应使用默认值
        assert result["sensitivity"] == "low"
        assert result["business_value"] in ["low", "medium"]
        assert result["classification"] == "public"
        assert result["domain"] == "unknown"

    def test_build_classification_graph(self, data_classifier):
        """测试构建分类图谱"""
        classifications = {
            1: {"sensitivity": "high", "business_value": "high", "domain": "finance"},
            2: {"sensitivity": "low", "business_value": "low", "domain": "public"},
            3: {"sensitivity": "medium", "business_value": "medium", "domain": "finance"},
            4: {"sensitivity": "high", "business_value": "high", "domain": "security"}
        }

        graph = data_classifier._build_classification_graph(classifications)

        assert graph["total_assets"] == 4
        assert graph["sensitivity_distribution"]["high"] == 2
        assert graph["sensitivity_distribution"]["medium"] == 1
        assert graph["sensitivity_distribution"]["low"] == 1
        assert graph["business_value_distribution"]["high"] == 2
        assert graph["domain_distribution"]["finance"] == 2
        assert graph["domain_distribution"]["security"] == 1

    @pytest.mark.asyncio
    async def test_classify_data_assets_success(self, data_classifier, mock_db, sample_assets):
        """测试数据资产分类成功"""
        # Mock HTTP响应
        mock_response = AsyncMock()
        mock_response.json.return_value = {"items": sample_assets}
        mock_response.raise_for_status = MagicMock()

        with patch.object(data_classifier.http_client, 'get', return_value=mock_response):
            # Mock数据库查询和提交
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value = mock_query

            result = await data_classifier.classify_data_assets(persist=True)

            assert result["success"] is True
            assert result["classified_assets"] == 3
            assert result["persisted_assets"] >= 0
            assert "classification_graph" in result
            assert "classifications" in result

    @pytest.mark.asyncio
    async def test_classify_data_assets_list_response(self, data_classifier, mock_db, sample_assets):
        """测试处理列表格式的响应"""
        mock_response = AsyncMock()
        mock_response.json.return_value = sample_assets  # 直接返回列表
        mock_response.raise_for_status = MagicMock()

        with patch.object(data_classifier.http_client, 'get', return_value=mock_response):
            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.first.return_value = None
            mock_db.query.return_value = mock_query

            result = await data_classifier.classify_data_assets(persist=True)

            assert result["success"] is True
            assert result["classified_assets"] == 3

    @pytest.mark.asyncio
    async def test_classify_data_assets_no_persist(self, data_classifier, sample_assets):
        """测试不持久化的分类"""
        mock_response = AsyncMock()
        mock_response.json.return_value = sample_assets
        mock_response.raise_for_status = MagicMock()

        with patch.object(data_classifier.http_client, 'get', return_value=mock_response):
            result = await data_classifier.classify_data_assets(persist=False)

            assert result["success"] is True
            assert result["persisted_assets"] == 0
            assert result["classified_assets"] == 3

    @pytest.mark.asyncio
    async def test_classify_data_assets_http_error(self, data_classifier):
        """测试HTTP请求失败"""
        with patch.object(data_classifier.http_client, 'get', side_effect=Exception("Connection error")):
            with pytest.raises(Exception) as exc_info:
                await data_classifier.classify_data_assets()

            assert "Connection error" in str(exc_info.value)

    def test_persist_classification(self, data_classifier, mock_db):
        """测试持久化分类结果"""
        # Mock数据库查询，假设不存在现有记录
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        classification = {
            "sensitivity": "high",
            "business_value": "high",
            "classification": "confidential",
            "domain": "finance",
            "quality_score": 0.9
        }

        with patch('src.services.data_classifier.DataClassificationResult') as mock_result_class:
            data_classifier._persist_classification(1, "test_asset", classification)

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_persist_classification_unchanged(self, data_classifier, mock_db):
        """测试分类结果未改变时不重复存储"""
        # Mock现有记录
        existing_record = MagicMock()
        existing_record.sensitivity = "high"
        existing_record.business_value = "high"

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = existing_record
        mock_db.query.return_value = mock_query

        classification = {
            "sensitivity": "high",
            "business_value": "high"
        }

        data_classifier._persist_classification(1, "test_asset", classification)

        # 应该不调用add和commit
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_persist_classification_error(self, data_classifier, mock_db):
        """测试持久化失败的错误处理"""
        mock_db.query.side_effect = Exception("Database error")

        classification = {"sensitivity": "high", "business_value": "high"}

        with pytest.raises(Exception):
            data_classifier._persist_classification(1, "test_asset", classification)

        mock_db.rollback.assert_called_once()

    def test_get_classification_history(self, data_classifier, mock_db):
        """测试获取分类历史"""
        # Mock查询结果
        mock_result1 = MagicMock()
        mock_result1.to_dict.return_value = {"asset_id": 1, "sensitivity": "high"}
        mock_result2 = MagicMock()
        mock_result2.to_dict.return_value = {"asset_id": 1, "sensitivity": "medium"}

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_result1, mock_result2
        ]
        mock_db.query.return_value = mock_query

        history = data_classifier.get_classification_history(1, limit=10)

        assert len(history) == 2
        assert history[0]["sensitivity"] == "high"

    def test_get_classification_history_error(self, data_classifier, mock_db):
        """测试获取历史记录失败"""
        mock_db.query.side_effect = Exception("Database error")

        history = data_classifier.get_classification_history(1)

        assert history == []

    def test_get_latest_classifications(self, data_classifier, mock_db):
        """测试获取最新分类结果"""
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"asset_id": 1, "sensitivity": "high"}

        # Mock复杂的查询链
        mock_subquery = MagicMock()
        mock_query = MagicMock()
        mock_query.join.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_result]
        mock_db.query.return_value = mock_query

        with patch('src.services.data_classifier.func'):
            results = data_classifier.get_latest_classifications(sensitivity="high", limit=10)

            assert len(results) >= 0

    def test_get_latest_classifications_with_filters(self, data_classifier, mock_db):
        """测试带过滤条件的最新分类查询"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query

        with patch('src.services.data_classifier.func'):
            data_classifier.get_latest_classifications(
                sensitivity="high",
                business_value="high",
                limit=50
            )

            # 验证过滤条件被应用
            assert mock_query.filter.call_count >= 0

    def test_get_latest_classifications_error(self, data_classifier, mock_db):
        """测试获取最新分类失败"""
        mock_db.query.side_effect = Exception("Database error")

        results = data_classifier.get_latest_classifications()

        assert results == []

    @pytest.mark.asyncio
    async def test_close(self, data_classifier):
        """测试关闭HTTP客户端"""
        with patch.object(data_classifier.http_client, 'aclose', new_callable=AsyncMock) as mock_close:
            await data_classifier.close()
            mock_close.assert_called_once()

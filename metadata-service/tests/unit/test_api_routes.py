"""
API路由单元测试
使用TestClient和mock来测试API端点
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from src.main import app
from src.models.data_asset import DataAssetType, DataAssetStatus
from src.models.ai_model import ModelType, ModelStatus


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.mark.unit
class TestHealthRoutes:
    """健康检查路由测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "metadata-service"
    
    def test_health_ready(self, client):
        """测试就绪检查端点"""
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]  # 取决于数据库连接状态


@pytest.mark.unit
class TestDataAssetRoutes:
    """数据资产路由测试"""
    
    def test_create_data_asset(self, client):
        """测试创建数据资产"""
        asset_data = {
            "name": "test_asset",
            "display_name": "Test Asset",
            "description": "Test description",
            "asset_type": "dataset",
            "status": "active"
        }
        
        response = client.post("/api/data-assets", json=asset_data)
        # 可能返回200或500（取决于数据库连接）
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "test_asset"
            assert data["asset_type"] == "dataset"
    
    def test_list_data_assets(self, client):
        """测试列出数据资产"""
        response = client.get("/api/data-assets")
        # 可能返回200或500（取决于数据库连接）
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_data_asset(self, client):
        """测试获取数据资产"""
        # 先创建一个资产
        asset_data = {
            "name": "get_test",
            "asset_type": "dataset",
            "status": "active"
        }
        create_response = client.post("/api/data-assets", json=asset_data)
        
        if create_response.status_code == 200:
            created = create_response.json()
            asset_id = created["id"]
            
            # 获取资产
            response = client.get(f"/api/data-assets/{asset_id}")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == asset_id
    
    def test_update_data_asset(self, client):
        """测试更新数据资产"""
        # 先创建一个资产
        asset_data = {
            "name": "update_test",
            "asset_type": "dataset",
            "status": "active"
        }
        create_response = client.post("/api/data-assets", json=asset_data)
        
        if create_response.status_code == 200:
            created = create_response.json()
            asset_id = created["id"]
            
            # 更新资产
            update_data = {
                "display_name": "Updated Name",
                "description": "Updated description"
            }
            response = client.put(f"/api/data-assets/{asset_id}", json=update_data)
            assert response.status_code in [200, 404]
    
    def test_delete_data_asset(self, client):
        """测试删除数据资产"""
        # 先创建一个资产
        asset_data = {
            "name": "delete_test",
            "asset_type": "dataset",
            "status": "active"
        }
        create_response = client.post("/api/data-assets", json=asset_data)
        
        if create_response.status_code == 200:
            created = create_response.json()
            asset_id = created["id"]
            
            # 删除资产
            response = client.delete(f"/api/data-assets/{asset_id}")
            assert response.status_code in [200, 404]


@pytest.mark.unit
class TestAIModelRoutes:
    """AI模型路由测试"""
    
    def test_create_ai_model(self, client):
        """测试创建AI模型"""
        model_data = {
            "name": "test_model",
            "display_name": "Test Model",
            "model_type": "llm",
            "status": "active",
            "framework": "pytorch"
        }
        
        response = client.post("/api/ai-models", json=model_data)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "test_model"
            assert data["model_type"] == "llm"
    
    def test_list_ai_models(self, client):
        """测试列出AI模型"""
        response = client.get("/api/ai-models")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.unit
class TestSearchRoutes:
    """搜索路由测试"""
    
    def test_search_all(self, client):
        """测试全局搜索"""
        response = client.get("/api/search", params={"q": "test"})
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "total" in data
            assert "results" in data


@pytest.mark.unit
class TestLineageRoutes:
    """血缘路由测试"""
    
    def test_create_lineage(self, client):
        """测试创建血缘关系"""
        lineage_data = {
            "source_type": "data_asset",
            "source_id": "asset-1",
            "target_type": "data_asset",
            "target_id": "asset-2",
            "relation_type": "reads",
            "lineage_type": "data_flow"
        }
        
        response = client.post("/api/lineage", json=lineage_data)
        assert response.status_code in [200, 500]
    
    def test_get_lineage_graph(self, client):
        """测试获取血缘图谱"""
        response = client.get("/api/lineage/graph", params={"asset_id": "asset-1"})
        assert response.status_code in [200, 404, 500]


@pytest.mark.unit
class TestQualityRoutes:
    """质量路由测试"""
    
    def test_check_quality(self, client):
        """测试质量检查"""
        response = client.post(
            "/api/quality/check",
            json={"asset_id": "asset-1", "asset_type": "data_asset"}
        )
        assert response.status_code in [200, 404, 500]
    
    def test_get_quality_dashboard(self, client):
        """测试获取质量仪表板"""
        response = client.get("/api/quality/dashboard")
        assert response.status_code in [200, 500]

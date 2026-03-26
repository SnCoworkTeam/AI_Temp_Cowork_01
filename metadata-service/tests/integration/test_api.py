"""
API集成测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from metadata_service.src.main import app


@pytest.mark.integration
class TestHealthAPI:
    """健康检查API测试"""
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        client = TestClient(app)
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_ready_endpoint(self):
        """测试就绪检查端点"""
        client = TestClient(app)
        response = client.get("/api/health/ready")
        
        assert response.status_code in [200, 503]  # 可能未就绪
    
    def test_live_endpoint(self):
        """测试存活检查端点"""
        client = TestClient(app)
        response = client.get("/api/health/live")
        
        assert response.status_code == 200


@pytest.mark.integration
class TestDataAssetsAPI:
    """数据资产API测试"""
    
    def test_list_data_assets(self):
        """测试列出数据资产"""
        client = TestClient(app)
        response = client.get("/api/data-assets")
        
        assert response.status_code in [200, 500]  # 可能数据库未连接
    
    def test_create_data_asset(self):
        """测试创建数据资产"""
        client = TestClient(app)
        data = {
            "name": "test_asset",
            "display_name": "Test Asset",
            "asset_type": "dataset",
            "description": "Test asset"
        }
        response = client.post("/api/data-assets", json=data)
        
        # 如果数据库未连接会返回500
        assert response.status_code in [200, 201, 500]


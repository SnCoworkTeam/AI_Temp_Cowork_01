"""
根路径路由单元测试
"""
import pytest
from fastapi.testclient import TestClient


class TestRootRoute:
    """根路径路由测试"""
    
    def test_root_endpoint(self, test_client: TestClient):
        """测试根路径端点"""
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "features" in data
        
        assert data["service"] == "API Gateway"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0
    
    def test_root_response_structure(self, test_client: TestClient):
        """测试根路径响应结构"""
        response = test_client.get("/")
        data = response.json()
        
        # 验证必需字段
        required_fields = ["service", "version", "status", "features"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # 验证features是列表且包含预期功能
        assert isinstance(data["features"], list)
        expected_features = [
            "Service Discovery",
            "Load Balancing",
            "Rate Limiting"
        ]
        for feature in expected_features:
            assert feature in data["features"], f"Missing expected feature: {feature}"





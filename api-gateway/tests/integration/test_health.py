"""
健康检查集成测试
"""
import pytest
import requests
from tests.conftest import BASE_URL


class TestHealthIntegration:
    """健康检查集成测试"""
    
    @pytest.mark.integration
    def test_health_endpoint_http(self, base_url: str):
        """测试健康检查端点（HTTP）"""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert data["service"] == "api-gateway"
            assert data["status"] in ["healthy", "degraded"]
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")
    
    @pytest.mark.integration
    def test_health_response_time(self, base_url: str):
        """测试健康检查响应时间"""
        try:
            import time
            start = time.time()
            response = requests.get(f"{base_url}/health", timeout=10)
            elapsed = time.time() - start
            
            assert response.status_code == 200
            # 放宽响应时间要求（服务发现可能需要更多时间）
            assert elapsed < 5.0, f"Health check took too long: {elapsed}s"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")
    
    @pytest.mark.integration
    def test_health_content_type(self, base_url: str):
        """测试健康检查Content-Type"""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")





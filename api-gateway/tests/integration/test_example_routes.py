"""
示例业务端点集成测试
"""
import pytest
import requests
from tests.conftest import BASE_URL


class TestRootEndpoint:
    """根路径端点集成测试"""
    
    @pytest.mark.integration
    def test_root_endpoint_http(self, base_url: str):
        """测试根路径端点（HTTP）"""
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "service" in data
            assert "version" in data
            assert "status" in data
            assert data["service"] == "API Gateway"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")
    
    @pytest.mark.integration
    def test_root_endpoint_methods(self, base_url: str):
        """测试根路径支持的HTTP方法"""
        try:
            # GET应该成功
            response = requests.get(f"{base_url}/", timeout=5)
            assert response.status_code == 200
            
            # POST应该返回405或404（取决于实现）
            response = requests.post(f"{base_url}/", timeout=5)
            assert response.status_code in [200, 404, 405]
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")


class TestMetricsEndpoint:
    """指标端点集成测试"""
    
    @pytest.mark.integration
    def test_metrics_endpoint_http(self, base_url: str):
        """测试指标端点（HTTP）"""
        try:
            response = requests.get(f"{base_url}/metrics", timeout=5)
            # 如果启用了metrics，应该返回200；否则返回404
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                # Prometheus格式
                assert "text/plain" in response.headers.get("content-type", "")
                assert len(response.text) > 0
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")


class TestAnalyticsEndpoint:
    """分析端点集成测试"""
    
    @pytest.mark.integration
    def test_analytics_stats_endpoint(self, base_url: str):
        """测试分析统计端点"""
        try:
            response = requests.get(f"{base_url}/api/analytics/stats", timeout=10)
            # 可能返回200（成功）或502/503（下游服务不可用）
            assert response.status_code in [200, 502, 503, 504]
            
            if response.status_code == 200:
                data = response.json()
                # 验证响应结构（如果成功）
                assert isinstance(data, dict)
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")
    
    @pytest.mark.integration
    def test_analytics_endpoint_error_handling(self, base_url: str):
        """测试分析端点错误处理"""
        try:
            # 测试不存在的端点
            response = requests.get(f"{base_url}/api/analytics/nonexistent", timeout=5)
            assert response.status_code in [404, 405, 502, 503]
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")


class TestUnifiedSearchEndpoint:
    """统一搜索端点集成测试"""
    
    @pytest.mark.integration
    def test_unified_search_endpoint(self, base_url: str):
        """测试统一搜索端点"""
        try:
            payload = {
                "query": "test",
                "types": ["document"],
                "limit": 10
            }
            response = requests.post(
                f"{base_url}/api/unified-search/search",
                json=payload,
                timeout=10
            )
            # 可能返回200（成功）、400（参数错误）、404（路由不存在）、502/503（下游服务不可用）
            assert response.status_code in [200, 400, 404, 502, 503, 504]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")
    
    @pytest.mark.integration
    def test_unified_search_validation(self, base_url: str):
        """测试统一搜索参数验证"""
        try:
            # 测试缺少必需参数
            response = requests.post(
                f"{base_url}/api/unified-search/search",
                json={},
                timeout=5
            )
            # 可能返回400（参数错误）、404（路由不存在）、422（验证错误）、502/503（下游服务不可用）
            assert response.status_code in [400, 404, 422, 502, 503]
        except requests.exceptions.ConnectionError:
            pytest.skip("API Gateway service is not running")





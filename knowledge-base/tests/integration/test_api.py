"""
Knowledge Base API集成测试
"""
import pytest
import os
import requests

BASE_URL = os.getenv("KB_BASE_URL", "http://localhost:8004")


@pytest.mark.integration
class TestKnowledgeBaseAPI:
    """Knowledge Base API测试"""
    
    @pytest.fixture
    def client(self):
        """HTTP 客户端（直连已启动的服务）"""
        class HttpClient:
            def get(self, path, **kwargs):
                return requests.get(BASE_URL + path, timeout=10, **kwargs)
            def post(self, path, **kwargs):
                return requests.post(BASE_URL + path, timeout=10, **kwargs)
        return HttpClient()
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_list_documents(self, client):
        """测试列出文档"""
        response = client.get("/api/documents")
        assert response.status_code == 200
    
    def test_search_documents(self, client):
        """测试搜索文档"""
        response = client.post(
            "/api/search/semantic",
            json={"query": "test query", "limit": 10}
        )
        assert response.status_code in [200, 400]










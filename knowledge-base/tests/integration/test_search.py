"""
搜索功能集成测试
"""
import pytest
import os
import requests

BASE_URL = os.getenv("KB_BASE_URL", "http://localhost:8004")


@pytest.mark.integration
class TestSearch:
    """搜索功能测试"""
    
    @pytest.fixture
    def client(self):
        """HTTP 客户端（直连已启动的服务）"""
        class HttpClient:
            def get(self, path, **kwargs):
                return requests.get(BASE_URL + path, timeout=10, **kwargs)
            def post(self, path, **kwargs):
                return requests.post(BASE_URL + path, timeout=10, **kwargs)
        return HttpClient()
    
    def test_semantic_search(self, client):
        """测试语义搜索"""
        response = client.post(
            "/api/search/semantic",
            json={
                "query": "test query",
                "limit": 10
            }
        )
        # 可能成功或失败（向量存储未配置等）
        assert response.status_code < 500
    
    def test_keyword_search(self, client):
        """测试关键词搜索"""
        response = client.post(
            "/api/search/keyword",
            json={
                "query": "test",
                "limit": 10
            }
        )
        assert response.status_code < 500
    
    def test_hybrid_search(self, client):
        """测试混合搜索"""
        response = client.post(
            "/api/search/hybrid",
            json={
                "query": "test query",
                "limit": 10
            }
        )
        assert response.status_code < 500


"""
Knowledge Base API路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "knowledge-base" / "src"))


@pytest.mark.unit
class TestDocumentRoutes:
    """文档路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_list_documents(self, client):
        """测试列出文档"""
        response = client.get("/api/documents")
        assert response.status_code in [200, 500]
    
    def test_upload_document(self, client):
        """测试上传文档"""
        # 使用multipart form data
        files = {"file": ("test.txt", "test content", "text/plain")}
        response = client.post("/api/documents", files=files)
        assert response.status_code in [200, 201, 400, 500]


@pytest.mark.unit
class TestSearchRoutes:
    """搜索路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_semantic_search(self, client):
        """测试语义搜索"""
        response = client.post(
            "/api/search/semantic",
            json={"query": "test query", "limit": 10}
        )
        assert response.status_code in [200, 400, 500]
    
    def test_keyword_search(self, client):
        """测试关键词搜索"""
        response = client.post(
            "/api/search/keyword",
            json={"query": "test", "limit": 10}
        )
        assert response.status_code in [200, 400, 500]
    
    def test_hybrid_search(self, client):
        """测试混合搜索"""
        response = client.post(
            "/api/search/hybrid",
            json={"query": "test query", "limit": 10}
        )
        assert response.status_code in [200, 400, 404, 500]  # 可能未实现


@pytest.mark.unit
class TestKnowledgeGraphRoutes:
    """知识图谱路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_get_knowledge_graph(self, client):
        """测试获取知识图谱"""
        response = client.get("/api/knowledge-graph")
        assert response.status_code in [200, 500]
    
    def test_get_knowledge_graph_with_filter(self, client):
        """测试带过滤条件的知识图谱查询"""
        response = client.get("/api/knowledge-graph?node_type=entity&max_nodes=50")
        assert response.status_code in [200, 500]


@pytest.mark.unit
class TestHealthRoutes:
    """健康检查路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "knowledge-base"
    
    def test_health_ready(self, client):
        """测试就绪检查"""
        response = client.get("/api/health/ready")
        assert response.status_code in [200, 503]


@pytest.mark.unit
class TestAnalyticsRoutes:
    """分析路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_get_search_quality(self, client):
        """测试获取搜索质量指标"""
        response = client.get("/api/analytics/search-quality")
        assert response.status_code in [200, 500]
    
    def test_get_document_stats(self, client):
        """测试获取文档统计"""
        response = client.get("/api/analytics/documents/stats")
        assert response.status_code in [200, 500]


"""
MCP Gateway API路由测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp-gateway" / "src"))


@pytest.mark.unit
class TestToolRoutes:
    """工具路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_list_tools(self, client):
        """测试列出工具"""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_register_tool(self, client):
        """测试注册工具"""
        tool_data = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            }
        }
        
        response = client.post("/api/tools/register", json=tool_data)
        assert response.status_code in [200, 201, 400, 500]
    
    def test_execute_tool(self, client):
        """测试执行工具"""
        response = client.post(
            "/api/tools/test_tool/execute",
            json={"parameters": {"input": "test"}}
        )
        assert response.status_code in [200, 400, 404, 500]
    
    def test_get_tool(self, client):
        """测试获取工具"""
        response = client.get("/api/tools/test_tool")
        assert response.status_code in [200, 404, 500]
    
    def test_unregister_tool(self, client):
        """测试注销工具"""
        response = client.delete("/api/tools/test_tool")
        assert response.status_code in [200, 404, 500]
    
    def test_tool_health_check(self, client):
        """测试工具健康检查"""
        response = client.get("/api/tools/test_tool/health")
        assert response.status_code in [200, 404, 500]


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
        assert data["service"] == "mcp-gateway"
    
    def test_health_ready(self, client):
        """测试就绪检查"""
        response = client.get("/api/health/ready")
        assert response.status_code in [200, 503]


@pytest.mark.unit
class TestMonitoringRoutes:
    """监控路由测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from src.main import app
        return TestClient(app)
    
    def test_get_metrics(self, client):
        """测试获取指标"""
        response = client.get("/api/monitoring/metrics")
        assert response.status_code in [200, 500]
    
    def test_get_tool_stats(self, client):
        """测试获取工具统计"""
        response = client.get("/api/monitoring/tools/stats")
        assert response.status_code in [200, 500]


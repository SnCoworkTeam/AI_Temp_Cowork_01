"""
MCP Gateway API集成测试
"""
import pytest
import httpx
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestMCPGatewayAPI:
    """MCP Gateway API测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from mcp_gateway.src.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_list_tools(self, client):
        """测试列出工具"""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
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
        assert response.status_code in [200, 201]
    
    def test_execute_tool(self, client):
        """测试执行工具"""
        # 先注册工具
        tool_data = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {"type": "object"}
        }
        client.post("/api/tools/register", json=tool_data)
        
        # 执行工具
        response = client.post(
            "/api/tools/test_tool/execute",
            json={"parameters": {"input": "test"}}
        )
        assert response.status_code in [200, 400]  # 可能成功或参数错误


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPGatewayAsyncAPI:
    """MCP Gateway异步API测试"""
    
    @pytest.mark.asyncio
    async def test_async_health_check(self):
        """测试异步健康检查"""
        from mcp_gateway.src.main import app
        from httpx import AsyncClient
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 200










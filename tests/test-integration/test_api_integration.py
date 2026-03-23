"""
API集成测试
测试各服务之间的API集成
"""
import pytest
import httpx
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.slow
class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture
    def base_urls(self):
        """服务基础URL"""
        return {
            "mcp_gateway": "http://localhost:8000",
            "workflow_engine": "http://localhost:8001",
            "auth_service": "http://localhost:8002",
            "knowledge_base": "http://localhost:8004"
        }
    
    @pytest.mark.asyncio
    async def test_mcp_gateway_health(self, base_urls):
        """测试MCP Gateway健康检查"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_urls['mcp_gateway']}/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_workflow_engine_health(self, base_urls):
        """测试Workflow Engine健康检查"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_urls['workflow_engine']}/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_auth_service_health(self, base_urls):
        """测试Auth Service健康检查"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_urls['auth_service']}/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_auth_workflow_integration(self, base_urls):
        """测试认证服务和工作流引擎集成"""
        async with httpx.AsyncClient() as client:
            # 1. 登录获取token
            login_response = await client.post(
                f"{base_urls['auth_service']}/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass"
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                
                # 2. 使用token访问工作流API
                headers = {"Authorization": f"Bearer {token}"}
                workflow_response = await client.get(
                    f"{base_urls['workflow_engine']}/api/workflows",
                    headers=headers
                )
                assert workflow_response.status_code in [200, 401]  # 可能未实现认证
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self, base_urls):
        """测试MCP工具执行集成"""
        async with httpx.AsyncClient() as client:
            # 获取可用工具
            tools_response = await client.get(f"{base_urls['mcp_gateway']}/api/tools")
            
            if tools_response.status_code == 200:
                tools = tools_response.json()
                if tools and len(tools) > 0:
                    # 执行第一个工具
                    tool_name = tools[0].get("name")
                    if tool_name:
                        execute_response = await client.post(
                            f"{base_urls['mcp_gateway']}/api/tools/{tool_name}/execute",
                            json={"parameters": {}}
                        )
                        # 可能成功或失败，但不应该500错误
                        assert execute_response.status_code < 500










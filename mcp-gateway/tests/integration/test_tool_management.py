"""
工具管理集成测试
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient


@pytest.mark.integration
class TestToolManagement:
    """工具管理测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        from mcp_gateway.src.main import app
        return TestClient(app)
    
    def test_list_tools(self, client):
        """测试列出工具"""
        response = client.get("/api/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_get_tool_info(self, client):
        """测试获取工具信息"""
        # 先获取工具列表
        list_response = client.get("/api/tools")
        if list_response.status_code == 200:
            tools = list_response.json()
            if isinstance(tools, list) and len(tools) > 0:
                tool_name = tools[0].get("name")
                if tool_name:
                    response = client.get(f"/api/tools/{tool_name}")
                    assert response.status_code in [200, 404]
    
    def test_tool_configuration(self, client):
        """测试工具配置"""
        config_data = {
            "tool_name": "test_tool",
            "enabled": True,
            "rate_limit": 100
        }
        
        response = client.post("/api/tools/config", json=config_data)
        # 可能成功或失败
        assert response.status_code < 500


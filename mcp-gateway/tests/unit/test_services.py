"""
MCP Gateway 服务单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp-gateway" / "src"))


@pytest.mark.unit
class TestToolService:
    """工具服务测试"""
    
    @pytest.fixture
    def tool_service(self):
        """工具服务fixture"""
        try:
            from src.services.tool_service import ToolService
            return ToolService()
        except ImportError:
            pytest.skip("ToolService not available")
    
    def test_register_tool(self, tool_service):
        """测试工具注册"""
        tool_data = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {"type": "object"}
        }
        
        result = tool_service.register_tool(tool_data)
        
        assert result is not None
        assert result["name"] == "test_tool"
    
    def test_get_tool(self, tool_service):
        """测试获取工具"""
        # 先注册工具
        tool_data = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {"type": "object"}
        }
        tool_service.register_tool(tool_data)
        
        # 获取工具
        tool = tool_service.get_tool("test_tool")
        
        assert tool is not None
        assert tool["name"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, tool_service):
        """测试工具执行"""
        # 注册工具
        tool_data = {
            "name": "test_tool",
            "description": "Test tool",
            "parameters": {"type": "object"}
        }
        tool_service.register_tool(tool_data)
        
        # 执行工具
        result = await tool_service.execute_tool(
            "test_tool",
            {"input": "test"}
        )
        
        assert result is not None


@pytest.mark.unit
class TestRateLimiter:
    """速率限制器测试"""
    
    @pytest.fixture
    def rate_limiter(self):
        """速率限制器fixture"""
        try:
            from src.core.rate_limiter import RateLimiter
            return RateLimiter(max_requests=10, window_seconds=60)
        except ImportError:
            pytest.skip("RateLimiter not available")
    
    def test_rate_limit_check(self, rate_limiter):
        """测试速率限制检查"""
        user_id = "test_user"
        
        # 前10次请求应该通过
        for i in range(10):
            allowed = rate_limiter.is_allowed(user_id)
            assert allowed is True
        
        # 第11次应该被限制
        allowed = rate_limiter.is_allowed(user_id)
        assert allowed is False








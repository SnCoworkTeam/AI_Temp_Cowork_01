"""
基础节点单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestBaseNode:
    """基础节点测试"""
    
    @pytest.fixture
    def base_node_impl(self):
        """创建BaseNode的具体实现"""
        from src.nodes.base_node import BaseNode
        
        class TestNode(BaseNode):
            async def execute(self, state):
                return {**state, "processed": True}
        
        return TestNode
    
    def test_node_initialization(self, base_node_impl):
        """测试节点初始化"""
        node = base_node_impl(
            name="test_node",
            description="Test node",
            config={"key": "value"},
            node_id="node_1"
        )
        
        assert node.name == "test_node"
        assert node.description == "Test node"
        assert node.config == {"key": "value"}
        assert node.node_id == "node_1"
        assert node._execution_count == 0
    
    @pytest.mark.asyncio
    async def test_node_execution(self, base_node_impl):
        """测试节点执行"""
        node = base_node_impl(name="test_node")
        result = await node.execute({"input": "test"})
        
        assert result["processed"] is True
        assert result["input"] == "test"
    
    @pytest.mark.asyncio
    async def test_execute_with_error_handling_success(self, base_node_impl):
        """测试带错误处理的成功执行"""
        node = base_node_impl(name="test_node")
        result = await node.execute_with_error_handling({"input": "test"})
        
        assert result["processed"] is True
        assert node._execution_count == 1
        assert node._last_error is None
    
    @pytest.mark.asyncio
    async def test_execute_with_error_handling_failure(self, base_node_impl):
        """测试带错误处理的失败执行"""
        from src.nodes.base_node import NodeExecutionError
        
        class ErrorNode(base_node_impl):
            async def execute(self, state):
                raise ValueError("Test error")
        
        node = ErrorNode(name="error_node")
        result = await node.execute_with_error_handling({"input": "test"})
        
        assert "error" in result
        assert node._last_error is not None
    
    def test_validate_input(self, base_node_impl):
        """测试输入验证"""
        node = base_node_impl(name="test_node")
        
        # 正常状态
        assert node.validate_input({"key": "value"}) is True
        
        # 包含错误的状态
        assert node.validate_input({"error": "some error"}) is False
    
    def test_validate_output(self, base_node_impl):
        """测试输出验证"""
        node = base_node_impl(name="test_node")
        
        # 正常输出
        assert node.validate_output({"key": "value"}) is True
        
        # 包含错误的输出
        assert node.validate_output({"error": "error", "error_node": "test_node"}) is False
    
    def test_resolve_template(self, base_node_impl):
        """测试模板解析"""
        node = base_node_impl(name="test_node")
        
        template = "Hello ${name}, value is ${value}"
        state = {"name": "World", "value": 123}
        
        result = node.resolve_template(template, state)
        assert result == "Hello World, value is 123"
    
    def test_get_state_value(self, base_node_impl):
        """测试获取状态值"""
        node = base_node_impl(name="test_node")
        
        state = {
            "simple": "value",
            "nested": {"key": "nested_value"},
            "list": [{"item": "first"}, {"item": "second"}]
        }
        
        assert node.get_state_value(state, "simple") == "value"
        assert node.get_state_value(state, "nested.key") == "nested_value"
        assert node.get_state_value(state, "list.0.item") == "first"
        assert node.get_state_value(state, "nonexistent", "default") == "default"
    
    def test_set_state_value(self, base_node_impl):
        """测试设置状态值"""
        node = base_node_impl(name="test_node")
        
        state = {}
        node.set_state_value(state, "simple", "value")
        node.set_state_value(state, "nested.key", "nested_value")
        
        assert state["simple"] == "value"
        assert state["nested"]["key"] == "nested_value"
    
    def test_get_statistics(self, base_node_impl):
        """测试获取统计信息"""
        node = base_node_impl(name="test_node")
        stats = node.get_statistics()
        
        assert stats["node_id"] == "test_node"
        assert stats["node_name"] == "test_node"
        assert stats["execution_count"] == 0
        assert stats["last_execution_time"] is None
        assert stats["last_error"] is None


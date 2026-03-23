"""
节点注册表单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestNodeRegistry:
    """节点注册表测试"""
    
    @pytest.fixture
    def registry(self):
        """获取节点注册表"""
        from src.core.node_registry import node_registry
        return node_registry
    
    def test_list_node_types(self, registry):
        """测试列出节点类型"""
        node_types = registry.list_node_types()
        assert isinstance(node_types, list)
        assert len(node_types) > 0
        assert "start" in node_types
        assert "end" in node_types
    
    def test_create_start_node(self, registry):
        """测试创建开始节点"""
        node_config = {
            "id": "start_1",
            "type": "start",
            "name": "开始"
        }
        
        node = registry.create_node(node_config)
        assert node is not None
        assert node.name == "开始"
    
    def test_create_end_node(self, registry):
        """测试创建结束节点"""
        node_config = {
            "id": "end_1",
            "type": "end",
            "name": "结束"
        }
        
        node = registry.create_node(node_config)
        assert node is not None
        assert node.name == "结束"
    
    def test_create_llm_node(self, registry):
        """测试创建LLM节点"""
        node_config = {
            "id": "llm_1",
            "type": "llm",
            "name": "LLM处理",
            "config": {
                "model": "gpt-4",
                "prompt_template": "Process: {input}"
            }
        }
        
        node = registry.create_node(node_config)
        assert node is not None
        assert node.name == "LLM处理"
    
    def test_create_unknown_node_type(self, registry):
        """测试创建未知节点类型"""
        node_config = {
            "id": "unknown_1",
            "type": "unknown_type",
            "name": "未知节点"
        }
        
        with pytest.raises(ValueError):
            registry.create_node(node_config)
    
    def test_register_custom_node(self, registry):
        """测试注册自定义节点"""
        from src.nodes.base_node import BaseNode
        
        class CustomNode(BaseNode):
            async def execute(self, state):
                return state
        
        def factory_func(config):
            return CustomNode(
                name=config.get("name", "custom"),
                config=config.get("config", {})
            )
        
        registry.register_node_type("custom", factory_func)
        assert "custom" in registry.list_node_types()
        
        node = registry.create_node({
            "id": "custom_1",
            "type": "custom",
            "name": "自定义节点"
        })
        assert isinstance(node, CustomNode)


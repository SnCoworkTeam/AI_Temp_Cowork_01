"""
核心组件单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestConfigParser:
    """配置解析器测试"""
    
    @pytest.fixture
    def parser(self):
        """创建配置解析器实例"""
        from src.core.config_parser import WorkflowConfigParser
        return WorkflowConfigParser()
    
    def test_parse_simple_config(self, parser):
        """测试解析简单配置"""
        config = {
            "name": "test",
            "nodes": [{"id": "start", "type": "start"}],
            "connections": []
        }
        
        workflow_def = parser.parse(config)
        assert workflow_def.name == "test"
        assert len(workflow_def.nodes) == 1
    
    def test_parse_complex_config(self, parser):
        """测试解析复杂配置"""
        config = {
            "name": "complex_workflow",
            "description": "Complex workflow",
            "nodes": [
                {"id": "start", "type": "start", "name": "开始"},
                {"id": "llm", "type": "llm", "name": "LLM处理", "config": {"model": "gpt-4"}},
                {"id": "end", "type": "end", "name": "结束"}
            ],
            "connections": [
                {"source": "start", "target": "llm"},
                {"source": "llm", "target": "end"}
            ]
        }
        
        workflow_def = parser.parse(config)
        assert workflow_def.name == "complex_workflow"
        assert len(workflow_def.nodes) == 3
        assert len(workflow_def.connections) == 2


@pytest.mark.unit
class TestNodeRegistry:
    """节点注册表测试"""
    
    @pytest.fixture
    def registry(self):
        """获取节点注册表"""
        from src.core.node_registry import node_registry
        return node_registry
    
    def test_register_node(self, registry):
        """测试注册节点"""
        class TestNode:
            pass
        
        registry.register("test_node", TestNode)
        assert "test_node" in registry._nodes
    
    def test_get_node_class(self, registry):
        """测试获取节点类"""
        class TestNode:
            pass
        
        registry.register("test_node", TestNode)
        node_class = registry.get("test_node")
        assert node_class == TestNode
    
    def test_list_node_types(self, registry):
        """测试列出节点类型"""
        node_types = registry.list_types()
        assert isinstance(node_types, list)


@pytest.mark.unit
class TestStateManagerInCoreComponents:
    """状态管理器测试（在core_components中）"""
    
    # 注意：StateManager的测试在test_state_manager.py中
    # 这里只保留其他核心组件的测试
    pass


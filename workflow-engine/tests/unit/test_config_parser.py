"""
配置解析器单元测试
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestWorkflowConfigParser:
    """工作流配置解析器测试"""
    
    @pytest.fixture
    def parser(self):
        """创建配置解析器实例"""
        from src.core.config_parser import WorkflowConfigParser
        return WorkflowConfigParser()
    
    def test_parse_simple_workflow(self, parser):
        """测试解析简单工作流"""
        config = {
            "name": "test_workflow",
            "description": "Test workflow",
            "version": "1.0.0",
            "nodes": [
                {"id": "start", "type": "start", "name": "开始"},
                {"id": "end", "type": "end", "name": "结束"}
            ],
            "connections": [
                {"source": {"node_id": "start"}, "target": {"node_id": "end"}}
            ],
            "start_node_id": "start",
            "end_node_ids": ["end"]
        }
        
        workflow_def = parser.parse(config)
        assert workflow_def.name == "test_workflow"
        assert len(workflow_def.nodes) == 2
        assert len(workflow_def.connections) == 1
    
    def test_parse_complex_workflow(self, parser):
        """测试解析复杂工作流"""
        config = {
            "name": "complex_workflow",
            "description": "Complex workflow test",
            "nodes": [
                {"id": "start", "type": "start"},
                {"id": "task1", "type": "task", "config": {"model": "gpt-4"}},
                {"id": "condition", "type": "condition", "config": {"condition": "value > 10"}},
                {"id": "end", "type": "end"}
            ],
            "connections": [
                {"source": {"node_id": "start"}, "target": {"node_id": "task1"}},
                {"source": {"node_id": "task1"}, "target": {"node_id": "condition"}},
                {"source": {"node_id": "condition"}, "target": {"node_id": "end"}}
            ],
            "start_node_id": "start",
            "end_node_ids": ["end"]
        }
        
        workflow_def = parser.parse(config)
        assert workflow_def.name == "complex_workflow"
        assert len(workflow_def.nodes) == 4
    
    def test_parse_invalid_config_missing_nodes(self, parser):
        """测试解析无效配置（缺少节点）"""
        config = {
            "name": "invalid",
            "nodes": [],
            "start_node_id": "start"
        }
        
        with pytest.raises(ValueError):
            parser.parse(config)
    
    def test_parse_invalid_config_duplicate_node_id(self, parser):
        """测试解析无效配置（重复节点ID）"""
        config = {
            "name": "invalid",
            "nodes": [
                {"id": "node1", "type": "start"},
                {"id": "node1", "type": "end"}
            ],
            "start_node_id": "node1"
        }
        
        with pytest.raises(ValueError):
            parser.parse(config)
    
    def test_parse_invalid_start_node(self, parser):
        """测试解析无效配置（起始节点不存在）"""
        config = {
            "name": "invalid",
            "nodes": [
                {"id": "start", "type": "start"}
            ],
            "start_node_id": "nonexistent"
        }
        
        with pytest.raises(ValueError):
            parser.parse(config)
    
    def test_parse_invalid_connection(self, parser):
        """测试解析无效配置（连接指向不存在的节点）"""
        config = {
            "name": "invalid",
            "nodes": [
                {"id": "start", "type": "start"}
            ],
            "connections": [
                {"source": {"node_id": "start"}, "target": {"node_id": "nonexistent"}}
            ],
            "start_node_id": "start"
        }
        
        with pytest.raises(ValueError):
            parser.parse(config)
    
    def test_parse_with_variables(self, parser):
        """测试解析带变量的工作流"""
        config = {
            "name": "workflow_with_vars",
            "description": "Workflow with variables",
            "nodes": [
                {"id": "start", "type": "start"}
            ],
            "variables": {
                "var1": "value1",
                "var2": 123
            },
            "start_node_id": "start"
        }
        
        workflow_def = parser.parse(config)
        assert workflow_def.variables == {"var1": "value1", "var2": 123}


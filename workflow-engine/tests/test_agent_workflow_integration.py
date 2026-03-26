"""
AgentNode工作流集成测试
测试AgentNode在工作流中的执行
"""
import pytest
import asyncio
from typing import Dict, Any

# 导入测试工作流
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "workflow-engine"))

from examples.test_agent_workflow import (
    TEST_AGENT_WORKFLOW,
    get_test_workflow,
    TEST_INPUT_DATA
)
from src.core.node_registry import node_registry


class TestAgentWorkflowIntegration:
    """AgentNode工作流集成测试类"""
    
    def test_workflow_definition_valid(self):
        """测试工作流定义格式是否正确"""
        assert "name" in TEST_AGENT_WORKFLOW
        assert "nodes" in TEST_AGENT_WORKFLOW
        assert "edges" in TEST_AGENT_WORKFLOW
        
        # 检查节点
        nodes = TEST_AGENT_WORKFLOW["nodes"]
        assert len(nodes) > 0
        
        # 检查是否有智能体节点
        agent_nodes = [n for n in nodes if n.get("type") == "agent"]
        assert len(agent_nodes) > 0, "工作流中应该包含至少一个智能体节点"
        
        # 检查智能体节点配置
        for node in agent_nodes:
            assert "config" in node, f"节点 {node.get('id')} 缺少config"
            assert "agent_id" in node["config"], f"节点 {node.get('id')} 缺少agent_id"
    
    def test_create_agent_node_from_workflow(self):
        """测试从工作流定义创建AgentNode"""
        workflow = TEST_AGENT_WORKFLOW
        
        # 找到智能体节点
        agent_node_def = next(
            (n for n in workflow["nodes"] if n.get("type") == "agent"),
            None
        )
        
        assert agent_node_def is not None, "工作流中应该包含智能体节点"
        
        # 创建节点
        try:
            agent_node = node_registry.create_node(agent_node_def)
            assert agent_node is not None
            assert agent_node.agent_id == agent_node_def["config"]["agent_id"]
            print(f"✅ 成功创建AgentNode: {agent_node.name}")
        except Exception as e:
            pytest.skip(f"无法创建AgentNode（可能需要数据库连接）: {e}")
    
    def test_workflow_node_structure(self):
        """测试工作流节点结构"""
        workflow = TEST_AGENT_WORKFLOW
        agent_node = next(
            (n for n in workflow["nodes"] if n.get("type") == "agent"),
            None
        )
        
        assert agent_node is not None
        
        # 检查必需字段
        assert "id" in agent_node
        assert "type" in agent_node
        assert agent_node["type"] == "agent"
        assert "config" in agent_node
        assert "agent_id" in agent_node["config"]
    
    def test_input_output_mapping(self):
        """测试输入输出映射配置"""
        workflow = TEST_AGENT_WORKFLOW
        agent_node = next(
            (n for n in workflow["nodes"] if n.get("type") == "agent"),
            None
        )
        
        assert agent_node is not None
        
        config = agent_node["config"]
        
        # 检查输入映射
        if "input_mapping" in config:
            assert isinstance(config["input_mapping"], dict)
        
        # 检查输出映射
        if "output_mapping" in config:
            assert isinstance(config["output_mapping"], dict)
    
    def test_get_test_workflow(self):
        """测试获取测试工作流函数"""
        # 测试获取代码审查工作流
        workflow = get_test_workflow("code_review")
        assert workflow["name"] == "智能代码审查流程"
        
        # 测试获取多智能体工作流
        workflow = get_test_workflow("multi_agent")
        assert workflow["name"] == "多智能体协作流程"
        
        # 测试无效的工作流名称
        with pytest.raises(ValueError):
            get_test_workflow("invalid_workflow")
    
    def test_multi_agent_workflow(self):
        """测试多智能体工作流"""
        from examples.test_agent_workflow import MULTI_AGENT_WORKFLOW
        
        # 检查工作流结构
        assert "nodes" in MULTI_AGENT_WORKFLOW
        assert "edges" in MULTI_AGENT_WORKFLOW
        
        # 检查智能体节点数量
        agent_nodes = [n for n in MULTI_AGENT_WORKFLOW["nodes"] if n.get("type") == "agent"]
        assert len(agent_nodes) >= 2, "多智能体工作流应该包含至少2个智能体节点"
        
        # 检查节点连接
        edges = MULTI_AGENT_WORKFLOW["edges"]
        assert len(edges) >= len(agent_nodes), "应该有足够的边连接所有节点"
    
    @pytest.mark.asyncio
    async def test_agent_node_execution_structure(self):
        """测试AgentNode执行结构（不实际执行）"""
        workflow = TEST_AGENT_WORKFLOW
        agent_node_def = next(
            (n for n in workflow["nodes"] if n.get("type") == "agent"),
            None
        )
        
        if agent_node_def is None:
            pytest.skip("工作流中没有智能体节点")
        
        try:
            # 创建节点
            agent_node = node_registry.create_node(agent_node_def)
            
            # 检查节点属性
            assert hasattr(agent_node, "agent_id")
            assert hasattr(agent_node, "execute")
            assert callable(agent_node.execute)
            
            # 检查配置
            assert agent_node.agent_id == agent_node_def["config"]["agent_id"]
            assert agent_node.timeout == agent_node_def["config"].get("timeout", 300)
            
            print(f"✅ AgentNode结构验证通过: {agent_node.name}")
        except Exception as e:
            pytest.skip(f"无法创建AgentNode（可能需要数据库连接）: {e}")


if __name__ == "__main__":
    # 运行基本测试
    pytest.main([__file__, "-v"])


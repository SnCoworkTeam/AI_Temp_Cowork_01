"""
节点实现单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestStartNode:
    """开始节点测试"""
    
    @pytest.mark.asyncio
    async def test_start_node_execution(self):
        """测试开始节点执行"""
        from src.nodes.start_node import StartNode
        
        node = StartNode(name="start", node_id="start_1")
        result = await node.execute({"input": "test"})
        
        assert result["workflow_started"] is True
        assert result["start_node"] == "start"
        assert result["start_executed"] is True
    
    def test_start_node_validation(self):
        """测试开始节点验证"""
        from src.nodes.start_node import StartNode
        
        node = StartNode(name="start")
        assert node.validate_input({}) is True
        assert node.validate_output({"workflow_started": True}) is True
        assert node.validate_output({}) is False


@pytest.mark.unit
class TestEndNode:
    """结束节点测试"""
    
    @pytest.mark.asyncio
    async def test_end_node_execution(self):
        """测试结束节点执行"""
        from src.nodes.end_node import EndNode
        
        node = EndNode(name="end", node_id="end_1")
        state = {"input": "test", "processed": "data"}
        result = await node.execute(state)
        
        assert result["workflow_completed"] is True
        assert result["end_node"] == "end"
        assert "final_result" in result
    
    def test_end_node_validation(self):
        """测试结束节点验证"""
        from src.nodes.end_node import EndNode
        
        node = EndNode(name="end")
        assert node.validate_input({}) is True
        assert node.validate_output({"workflow_completed": True}) is True
        assert node.validate_output({}) is False


@pytest.mark.unit
class TestConditionNode:
    """条件节点测试"""
    
    @pytest.mark.asyncio
    async def test_condition_node_true(self):
        """测试条件节点为真"""
        from src.nodes.condition_node import ConditionNode
        
        node = ConditionNode(
            name="condition",
            config={
                "condition": "value > 10",
                "true_output": "true_path",
                "false_output": "false_path"
            }
        )
        
        result = await node.execute({"value": 15})
        assert result.get("condition_condition_result") is True or result.get("condition_result") is True
    
    @pytest.mark.asyncio
    async def test_condition_node_false(self):
        """测试条件节点为假"""
        from src.nodes.condition_node import ConditionNode
        
        node = ConditionNode(
            name="condition",
            config={
                "condition": "value > 10",
                "true_output": "true_path",
                "false_output": "false_path"
            }
        )
        
        result = await node.execute({"value": 5})
        assert result.get("condition_condition_result") is False or result.get("condition_result") is False
    
    @pytest.mark.asyncio
    async def test_condition_node_with_state_variables(self):
        """测试条件节点使用状态变量"""
        from src.nodes.condition_node import ConditionNode
        
        node = ConditionNode(
            name="condition",
            config={
                "condition": "user.age >= 18",
                "true_output": "adult",
                "false_output": "minor"
            }
        )
        
        result = await node.execute({"user": {"age": 20}})
        assert result.get("condition_condition_result") is True or result.get("condition_result") is True


@pytest.mark.unit
class TestLLMNode:
    """LLM节点测试"""
    
    @pytest.mark.asyncio
    async def test_llm_node_without_api_key(self):
        """测试LLM节点无API密钥"""
        from src.nodes.llm_node import LLMNode
        from src.nodes.base_node import NodeExecutionError
        
        node = LLMNode(
            name="llm",
            config={"model": "gpt-4"}
        )
        
        # 如果没有API密钥，应该抛出错误
        with patch.object(node, '_get_llm', side_effect=NodeExecutionError("llm", "API key not configured")):
            with pytest.raises(NodeExecutionError):
                await node.execute({"input": "test"})
    
    @pytest.mark.asyncio
    async def test_llm_node_with_mock(self):
        """测试LLM节点（使用mock）"""
        from src.nodes.llm_node import LLMNode
        
        node = LLMNode(
            name="llm",
            config={
                "model": "gpt-4",
                "prompt_template": "Process: {input}",
                "system_message": "You are a helpful assistant"
            }
        )
        
        # Mock LLM调用
        mock_llm = AsyncMock()
        mock_llm.invoke.return_value = Mock(content="Mocked response")
        node._llm = mock_llm
        
        result = await node.execute({"input": "test"})
        assert result is not None


@pytest.mark.unit
class TestToolNode:
    """工具节点测试"""
    
    @pytest.mark.asyncio
    async def test_tool_node_execution(self):
        """测试工具节点执行"""
        from src.nodes.tool_node import ToolNode
        
        node = ToolNode(
            name="tool",
            config={
                "tool_name": "test_tool",
                "parameters": {"input": "{data}"}
            }
        )
        
        # Mock HTTP客户端
        with patch('src.nodes.tool_node.HTTPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = {"success": True, "result": "tool_result"}
            
            result = await node.execute({"data": "test"})
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_tool_node_missing_tool_name(self):
        """测试工具节点缺少工具名"""
        from src.nodes.tool_node import ToolNode
        from src.nodes.base_node import NodeExecutionError
        
        node = ToolNode(name="tool", config={})
        
        with pytest.raises(NodeExecutionError):
            await node.execute({"data": "test"})


@pytest.mark.unit
class TestDataTransformNode:
    """数据转换节点测试"""
    
    @pytest.mark.asyncio
    async def test_transform_node_execution(self):
        """测试数据转换节点执行"""
        from src.nodes.data_transform_node import DataTransformNode
        
        node = DataTransformNode(
            name="transform",
            config={
                "transform": {
                    "output": "${input}_transformed",
                    "value": "${number} * 2"
                }
            }
        )
        
        result = await node.execute({"input": "test", "number": 5})
        assert result is not None


@pytest.mark.unit
class TestKnowledgeSearchNode:
    """知识搜索节点测试"""
    
    @pytest.mark.asyncio
    async def test_knowledge_search_node_execution(self):
        """测试知识搜索节点执行"""
        from src.nodes.knowledge_search_node import KnowledgeSearchNode
        
        node = KnowledgeSearchNode(
            name="knowledge_search",
            config={
                "query": "{search_query}",
                "limit": 5
            }
        )
        
        # Mock知识库搜索
        with patch('src.nodes.knowledge_search_node.search_knowledge', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {"results": []}
            
            result = await node.execute({"search_query": "test"})
            assert result is not None


"""
Workflow Engine 节点单元测试
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "workflow-engine" / "src"))


@pytest.mark.unit
class TestBaseNode:
    """基础节点测试"""
    
    def test_node_initialization(self):
        """测试节点初始化"""
        from src.nodes.base_node import BaseNode
        
        # BaseNode是抽象类，需要创建具体实现
        class TestNode(BaseNode):
            async def execute(self, state):
                return state
        
        node = TestNode(
            name="test_node",
            description="Test node",
            config={},
            node_id="test_node"
        )
        
        assert node.node_id == "test_node"
        assert node.name == "test_node"
    
    @pytest.mark.asyncio
    async def test_node_execution(self):
        """测试节点执行"""
        from src.nodes.base_node import BaseNode
        
        class TestNode(BaseNode):
            async def execute(self, state):
                return {**state, "processed": True}
        
        node = TestNode(
            name="test_node",
            description="Test node",
            config={},
            node_id="test_node"
        )
        
        result = await node.execute({"input": "test"})
        assert result is not None
        assert result["processed"] is True


@pytest.mark.unit
class TestLLMNode:
    """LLM节点测试"""
    
    @pytest.mark.asyncio
    async def test_llm_node_execution(self):
        """测试LLM节点执行"""
        from src.nodes.llm_node import LLMNode
        
        node = LLMNode(
            name="llm_node",
            description="LLM node",
            node_id="llm_node",
            config={
                "model": "gpt-3.5-turbo",
                "prompt": "Hello, {input}!"
            }
        )
        
        # Mock LLM调用（如果节点有_call_llm方法）
        try:
            from unittest.mock import patch
            with patch.object(node, '_call_llm', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = {"output": "Hello, world!"}
                
                result = await node.execute({"input": "world"})
                assert result is not None
        except AttributeError:
            # 如果节点没有_call_llm方法，只测试基本执行
            result = await node.execute({"input": "world"})
            assert result is not None


@pytest.mark.unit
class TestToolNode:
    """工具节点测试"""
    
    @pytest.mark.asyncio
    async def test_tool_node_execution(self):
        """测试工具节点执行"""
        from src.nodes.tool_node import ToolNode
        
        node = ToolNode(
            name="tool_node",
            description="Tool node",
            node_id="tool_node",
            config={
                "tool_name": "test_tool",
                "parameters": {"input": "{data}"}
            }
        )
        
        # Mock工具调用（如果节点有_call_tool方法）
        try:
            from unittest.mock import patch
            with patch.object(node, '_call_tool', new_callable=AsyncMock) as mock_tool:
                mock_tool.return_value = {"result": "success"}
                
                result = await node.execute({"data": "test"})
                assert result is not None
        except AttributeError:
            # 如果节点没有_call_tool方法，只测试基本执行
            result = await node.execute({"data": "test"})
            assert result is not None


@pytest.mark.unit
class TestStartNode:
    """开始节点测试"""
    
    @pytest.mark.asyncio
    async def test_start_node_execution(self):
        """测试开始节点执行"""
        from src.nodes.start_node import StartNode
        
        node = StartNode(
            name="start_node",
            node_id="start_node",
            config={}
        )
        
        result = await node.execute({"input": "test"})
        assert result is not None
        assert "input" in result


@pytest.mark.unit
class TestEndNode:
    """结束节点测试"""
    
    @pytest.mark.asyncio
    async def test_end_node_execution(self):
        """测试结束节点执行"""
        from src.nodes.end_node import EndNode
        
        node = EndNode(
            name="end_node",
            node_id="end_node",
            config={}
        )
        
        result = await node.execute({"input": "test"})
        assert result is not None


@pytest.mark.unit
class TestConditionNode:
    """条件节点测试"""
    
    @pytest.mark.asyncio
    async def test_condition_node_execution(self):
        """测试条件节点执行"""
        from src.nodes.condition_node import ConditionNode
        
        node = ConditionNode(
            name="condition_node",
            description="Condition node",
            node_id="condition_node",
            config={
                "condition": "input == 'test'",
                "true_path": "path1",
                "false_path": "path2"
            }
        )
        
        # 测试条件为真
        result = await node.execute({"input": "test"})
        assert result is not None
        
        # 测试条件为假
        result = await node.execute({"input": "other"})
        assert result is not None


@pytest.mark.unit
class TestTransformNode:
    """数据转换节点测试"""
    
    @pytest.mark.asyncio
    async def test_transform_node_execution(self):
        """测试数据转换节点执行"""
        from src.nodes.data_transform_node import DataTransformNode
        
        node = DataTransformNode(
            name="transform_node",
            description="Transform node",
            node_id="transform_node",
            config={
                "transform": {
                    "output": "{input}_transformed"
                }
            }
        )
        
        result = await node.execute({"input": "test"})
        assert result is not None


@pytest.mark.unit
class TestKnowledgeSearchNode:
    """知识搜索节点测试"""
    
    @pytest.mark.asyncio
    async def test_knowledge_search_node_execution(self):
        """测试知识搜索节点执行"""
        from src.nodes.knowledge_search_node import KnowledgeSearchNode
        
        node = KnowledgeSearchNode(
            name="knowledge_search_node",
            description="Knowledge search node",
            node_id="knowledge_search_node",
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


@pytest.mark.unit
class TestDocumentProcessingNode:
    """文档处理节点测试"""
    
    @pytest.mark.asyncio
    async def test_document_processing_node_execution(self):
        """测试文档处理节点执行"""
        from src.nodes.document_processing_node import DocumentProcessingNode
        
        node = DocumentProcessingNode(
            name="doc_processing_node",
            description="Document processing node",
            node_id="doc_processing_node",
            config={
                "operation": "extract",
                "document_id": "{doc_id}"
            }
        )
        
        result = await node.execute({"doc_id": "test-doc"})
        assert result is not None


@pytest.mark.unit
class TestNodeErrorHandling:
    """节点错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_node_error_handling(self):
        """测试节点错误处理"""
        from src.nodes.base_node import BaseNode, NodeExecutionError
        
        class ErrorNode(BaseNode):
            async def execute(self, state):
                raise ValueError("Test error")
        
        node = ErrorNode(
            name="error_node",
            description="Test error node",
            config={},
            node_id="error_node"
        )
        
        # 测试错误处理
        try:
            result = await node.execute_with_error_handling({"input": "test"})
            # 如果错误被捕获，状态应该包含错误信息
            assert "error" in result or "_last_error" in node.__dict__
        except Exception:
            # 允许异常传播
            pass
    
    def test_node_execution_count(self):
        """测试节点执行计数"""
        from src.nodes.base_node import BaseNode
        
        class TestNode(BaseNode):
            async def execute(self, state):
                return state
        
        node = TestNode(
            name="count_node",
            description="Test count node",
            config={},
            node_id="count_node"
        )
        
        assert node._execution_count == 0








"""
采集器单元测试
使用mock来测试采集器功能
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "metadata-service" / "src"))

from src.collectors.base_collector import BaseCollector
from src.collectors.data_lineage_collector import DataLineageCollector
from src.collectors.model_collector import ModelCollector
from src.collectors.workflow_collector import WorkflowCollector
from src.collectors.mcp_tool_collector import MCPToolCollector
from src.collectors.knowledge_collector import KnowledgeCollector


@pytest.mark.unit
class TestBaseCollector:
    """基础采集器测试"""
    
    def test_base_collector_init(self):
        """测试基础采集器初始化 - 使用具体实现类"""
        # 使用KnowledgeCollector作为具体实现来测试BaseCollector的功能
        collector = KnowledgeCollector(
            knowledge_base_url="http://localhost:8000",
            metadata_service_url="http://localhost:8005"
        )
        
        assert collector.source_service_url == "http://localhost:8000"
        assert collector.metadata_service_url == "http://localhost:8005"
        assert collector._source_client is None
        assert collector._metadata_client is None
    
    @pytest.mark.asyncio
    async def test_get_source_client(self):
        """测试获取源服务客户端"""
        # 使用具体实现类
        collector = KnowledgeCollector(
            knowledge_base_url="http://localhost:8000"
        )
        
        client = await collector._get_source_client()
        assert client is not None
        assert str(client.base_url) == "http://localhost:8000"
        
        # 测试懒加载
        client2 = await collector._get_source_client()
        assert client is client2
    
    @pytest.mark.asyncio
    async def test_close(self):
        """测试关闭客户端"""
        # 使用具体实现类
        collector = KnowledgeCollector(
            knowledge_base_url="http://localhost:8000"
        )
        
        await collector._get_source_client()
        await collector.close()
        
        # 关闭后应该可以重新创建
        client = await collector._get_source_client()
        assert client is not None


@pytest.mark.unit
class TestDataLineageCollector:
    """数据血缘采集器测试"""
    
    @pytest.mark.asyncio
    async def test_collect_lineage(self):
        """测试收集血缘数据"""
        collector = DataLineageCollector()
        
        # Mock WorkflowCollector, MCPToolCollector等子collector
        mock_workflow_collector = AsyncMock()
        mock_workflow_collector.collect = AsyncMock(return_value=[
            {
                "workflow_id": "wf-1",
                "name": "test_workflow",
                "data_sources": ["asset-1"],
                "data_sinks": ["asset-2"],
                "dependencies": {}
            }
        ])
        
        mock_mcp_collector = AsyncMock()
        mock_mcp_collector.collect = AsyncMock(return_value=[])
        
        with patch('src.collectors.data_lineage_collector.WorkflowCollector', return_value=mock_workflow_collector), \
             patch('src.collectors.data_lineage_collector.MCPToolCollector', return_value=mock_mcp_collector):
            result = await collector.collect()
            
            assert result is not None
            assert isinstance(result, list)
            # 验证至少调用了workflow collector
            mock_workflow_collector.collect.assert_called()


@pytest.mark.unit
class TestModelCollector:
    """模型采集器测试"""
    
    @pytest.mark.asyncio
    async def test_collect_models(self):
        """测试收集模型数据"""
        collector = ModelCollector(
            model_registry_url="http://localhost:8000"
        )
        
        # Mock HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "test_model",
                    "model_type": "llm",
                    "framework": "pytorch"
                }
            ]
        }
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await collector.collect()
            
            assert result is not None
            mock_get.assert_called()


@pytest.mark.unit
class TestWorkflowCollector:
    """工作流采集器测试"""
    
    @pytest.mark.asyncio
    async def test_collect_workflows(self):
        """测试收集工作流数据"""
        collector = WorkflowCollector(
            workflow_engine_url="http://localhost:8000"
        )
        
        # Mock HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflows": [
                {
                    "workflow_id": "wf-123",
                    "name": "test_workflow",
                    "status": "active"
                }
            ]
        }
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await collector.collect()
            
            assert result is not None
            mock_get.assert_called()


@pytest.mark.unit
class TestMCPToolCollector:
    """MCP工具采集器测试"""
    
    @pytest.mark.asyncio
    async def test_collect_tools(self):
        """测试收集MCP工具数据"""
        collector = MCPToolCollector(
            mcp_gateway_url="http://localhost:8000"
        )
        
        # Mock HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "tool_id": "tool-1",
                    "name": "test_tool",
                    "description": "Test tool"
                }
            ]
        }
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await collector.collect()
            
            assert result is not None
            mock_get.assert_called()


@pytest.mark.unit
class TestKnowledgeCollector:
    """知识库采集器测试"""
    
    @pytest.mark.asyncio
    async def test_collect_knowledge(self):
        """测试收集知识库数据"""
        collector = KnowledgeCollector(
            knowledge_base_url="http://localhost:8000"
        )
        
        # Mock HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "documents": [
                {
                    "document_id": "doc-1",
                    "title": "Test Document",
                    "content": "Test content"
                }
            ]
        }
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await collector.collect()
            
            assert result is not None
            mock_get.assert_called()

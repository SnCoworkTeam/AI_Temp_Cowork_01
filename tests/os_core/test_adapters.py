"""
资源适配器单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加os-core到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
OS_CORE_PATH = PROJECT_ROOT / "os-core"
sys.path.insert(0, str(OS_CORE_PATH))

from resource_registry import ResourceRegistry
import sys
sys.path.insert(0, str(OS_CORE_PATH / "adapters"))
from business_object_adapter import BusinessObjectAdapter
from system_endpoint_adapter import SystemEndpointAdapter
from knowledge_adapter import KnowledgeAdapter
from workflow_adapter import WorkflowAdapter
from resource_model import ResourceType


class TestBusinessObjectAdapter:
    """业务对象适配器测试"""
    
    @pytest.fixture
    def registry(self):
        return ResourceRegistry()
    
    @pytest.fixture
    def adapter(self, registry):
        return BusinessObjectAdapter(registry)
    
    def test_adapt_from_metadata(self, adapter):
        """测试从元数据适配"""
        metadata = {
            "id": "order:001",
            "business_id": "ORDER-001",
            "name": "采购订单001",
            "description": "测试订单",
            "owner_department": "采购部",
            "lifecycle_state": "active"
        }
        
        resource = adapter.adapt_from_metadata(metadata)
        
        assert resource.id == "order:001"
        assert resource.business_id == "ORDER-001"
        assert resource.type == ResourceType.BUSINESS_OBJECT
        assert resource.owner_department == "采购部"
    
    def test_adapt_from_database(self, adapter):
        """测试从数据库记录适配"""
        record = {
            "id": 123,
            "name": "采购订单123",
            "title": "订单标题",
            "description": "订单描述",
            "department": "采购部",
            "status": "active"
        }
        
        resource = adapter.adapt_from_database("orders", record)
        
        assert resource.id == "orders:123"
        assert resource.business_id == "123"
        assert resource.type == ResourceType.BUSINESS_OBJECT
    
    def test_register_business_objects(self, adapter):
        """测试批量注册业务对象"""
        objects = [
            {
                "id": "order:001",
                "business_id": "ORDER-001",
                "name": "订单001",
                "description": "测试",
                "owner_department": "采购部"
            },
            {
                "id": "order:002",
                "business_id": "ORDER-002",
                "name": "订单002",
                "description": "测试",
                "owner_department": "采购部"
            }
        ]
        
        count = adapter.register_business_objects(objects, source="metadata")
        assert count == 2
        assert adapter.registry.count() == 2


class TestSystemEndpointAdapter:
    """系统端点适配器测试"""
    
    @pytest.fixture
    def registry(self):
        return ResourceRegistry()
    
    @pytest.fixture
    def adapter(self, registry):
        return SystemEndpointAdapter(registry)
    
    def test_adapt_from_mcp_server(self, adapter):
        """测试从MCP服务器适配"""
        server_info = {
            "name": "file_system",
            "display_name": "文件系统MCP服务器",
            "description": "文件系统操作",
            "url": "mcp://file_system",
            "auth_required": False,
            "tools": [
                {"name": "read_file"},
                {"name": "write_file"}
            ]
        }
        
        resource = adapter.adapt_from_mcp_server(server_info)
        
        assert resource.id == "mcp:file_system"
        assert resource.type == ResourceType.SYSTEM_ENDPOINT
        assert resource.endpoint_type == "mcp"
        assert "invoke" in resource.get_capabilities()
    
    def test_adapt_from_api_endpoint(self, adapter):
        """测试从API端点适配"""
        endpoint_info = {
            "id": "create_po",
            "name": "创建采购订单",
            "path": "/api/sap/create_po",
            "method": "POST",
            "description": "创建采购订单接口",
            "auth_required": True
        }
        
        resource = adapter.adapt_from_api_endpoint(endpoint_info)
        
        assert resource.id == "api:create_po"
        assert resource.type == ResourceType.SYSTEM_ENDPOINT
        assert resource.endpoint_type == "api"
    
    def test_register_system_endpoints(self, adapter):
        """测试批量注册系统端点"""
        endpoints = [
            {
                "name": "mcp_server_1",
                "display_name": "MCP服务器1",
                "description": "测试服务器",
                "url": "mcp://server1"
            }
        ]
        
        count = adapter.register_system_endpoints(endpoints, source="mcp")
        assert count == 1


class TestKnowledgeAdapter:
    """知识项适配器测试"""
    
    @pytest.fixture
    def registry(self):
        return ResourceRegistry()
    
    @pytest.fixture
    def adapter(self, registry):
        return KnowledgeAdapter(registry)
    
    def test_adapt_from_knowledge_base(self, adapter):
        """测试从知识库适配"""
        kb_item = {
            "id": "doc:001",
            "title": "采购流程文档",
            "description": "采购流程说明",
            "content": "这是详细的采购流程说明...",
            "kb_id": "kb_procurement",
            "category": "流程文档"
        }
        
        resource = adapter.adapt_from_knowledge_base(kb_item)
        
        assert resource.id == "kb:doc:001"
        assert resource.type == ResourceType.KNOWLEDGE_ITEM
        assert resource.content_type == "document"
        assert len(resource.content) > 0
    
    def test_adapt_from_ea_node(self, adapter):
        """测试从EA节点适配"""
        ea_node = {
            "id": "process:001",
            "name": "采购流程",
            "type": "BusinessProcess",
            "description": "企业采购流程",
            "business_domain": "采购",
            "relationships": {
                "uses": ["system:sap"]
            }
        }
        
        resource = adapter.adapt_from_ea_node(ea_node)
        
        assert resource.id == "ea:process:001"
        assert resource.type == ResourceType.KNOWLEDGE_ITEM
        assert resource.content_type == "ea_node"
        assert "采购流程" in resource.content
    
    def test_register_knowledge_items(self, adapter):
        """测试批量注册知识项"""
        items = [
            {
                "id": "doc:001",
                "title": "文档1",
                "content": "内容1",
                "description": "描述1"
            }
        ]
        
        count = adapter.register_knowledge_items(items, source="kb")
        assert count == 1


class TestWorkflowAdapter:
    """工作流适配器测试"""
    
    @pytest.fixture
    def registry(self):
        return ResourceRegistry()
    
    @pytest.fixture
    def adapter(self, registry):
        return WorkflowAdapter(registry)
    
    def test_adapt_from_workflow_definition(self, adapter):
        """测试从工作流定义适配"""
        workflow_def = {
            "id": "wf:001",
            "name": "采购订单审批流程",
            "description": "自动审批流程",
            "type": "static",
            "steps": [
                {"name": "step1", "action": "create_po"},
                {"name": "step2", "action": "approve"}
            ]
        }
        
        resource = adapter.adapt_from_workflow_definition(workflow_def)
        
        assert resource.id == "workflow:wf:001"
        assert resource.type == ResourceType.WORKFLOW
        assert resource.workflow_type == "static"
        assert len(resource.workflow_definition["steps"]) == 2
    
    def test_adapt_from_workflow_execution(self, adapter):
        """测试从工作流执行适配"""
        execution = {
            "workflow_id": "wf:001",
            "workflow_name": "动态工作流",
            "execution_id": "exec:001",
            "status": "success",
            "steps": [
                {"name": "step1", "action": "create_po"}
            ],
            "started_at": "2025-12-15T10:00:00",
            "completed_at": "2025-12-15T10:05:00"
        }
        
        resource = adapter.adapt_from_workflow_execution(execution)
        
        assert resource is not None
        assert resource.id == "workflow:wf:001"
        assert resource.workflow_type == "dynamic"
    
    def test_register_workflows(self, adapter):
        """测试批量注册工作流"""
        workflows = [
            {
                "id": "wf:001",
                "name": "工作流1",
                "description": "测试工作流",
                "type": "static",
                "steps": []
            }
        ]
        
        count = adapter.register_workflows(workflows, source="definition")
        assert count == 1


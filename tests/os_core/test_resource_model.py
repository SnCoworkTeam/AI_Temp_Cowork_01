"""
资源模型单元测试
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加os-core到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
OS_CORE_PATH = PROJECT_ROOT / "os-core"
sys.path.insert(0, str(OS_CORE_PATH))

# 直接导入模块文件
from resource_model import (
    ResourceType,
    BusinessResource,
    SystemEndpointResource,
    KnowledgeItemResource,
    WorkflowResource,
    DataEntityResource
)


class TestBusinessResource:
    """业务资源测试"""
    
    def test_create_business_resource(self):
        """测试创建业务资源"""
        resource = BusinessResource(
            id="order:001",
            name="采购订单001",
            description="测试订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部",
            lifecycle_state="active"
        )
        
        assert resource.id == "order:001"
        assert resource.name == "采购订单001"
        assert resource.type == ResourceType.BUSINESS_OBJECT
        assert resource.business_id == "ORDER-001"
        assert resource.owner_department == "采购部"
    
    def test_get_metadata(self):
        """测试获取元数据"""
        resource = BusinessResource(
            id="order:001",
            name="采购订单001",
            description="测试订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部",
            lifecycle_state="active",
            business_metadata={"amount": 10000}
        )
        
        metadata = resource.get_metadata()
        assert metadata["id"] == "order:001"
        assert metadata["business_id"] == "ORDER-001"
        assert metadata["owner_department"] == "采购部"
        assert metadata["amount"] == 10000
    
    def test_get_capabilities(self):
        """测试获取能力列表"""
        resource = BusinessResource(
            id="order:001",
            name="采购订单001",
            description="测试订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部",
            capabilities=["query", "update", "cancel"]
        )
        
        capabilities = resource.get_capabilities()
        assert "query" in capabilities
        assert "update" in capabilities
        assert "cancel" in capabilities
    
    def test_execute_action(self):
        """测试执行操作"""
        resource = BusinessResource(
            id="order:001",
            name="采购订单001",
            description="测试订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部",
            capabilities=["query", "update"]
        )
        
        result = resource.execute("query", {"filter": "status=active"})
        assert result["status"] == "success"
        assert result["action"] == "query"
        
        # 测试不支持的操作
        with pytest.raises(ValueError):
            resource.execute("delete", {})


class TestSystemEndpointResource:
    """系统端点资源测试"""
    
    def test_create_system_endpoint(self):
        """测试创建系统端点"""
        resource = SystemEndpointResource(
            id="api:sap:create_po",
            name="SAP创建采购订单API",
            description="SAP系统创建采购订单接口",
            uri="api://sap/create_po",
            endpoint_url="https://sap.example.com/api/create_po",
            endpoint_type="api",
            protocol="https"
        )
        
        assert resource.id == "api:sap:create_po"
        assert resource.type == ResourceType.SYSTEM_ENDPOINT
        assert resource.endpoint_type == "api"
        assert resource.protocol == "https"
    
    def test_get_metadata(self):
        """测试获取元数据"""
        resource = SystemEndpointResource(
            id="mcp:file_system",
            name="文件系统MCP服务器",
            description="文件系统操作",
            uri="mcp://file_system",
            endpoint_url="mcp://file_system",
            endpoint_type="mcp",
            protocol="mcp",
            service_metadata={"tools": ["read_file", "write_file"]}
        )
        
        metadata = resource.get_metadata()
        assert metadata["endpoint_type"] == "mcp"
        assert metadata["tools"] == ["read_file", "write_file"]


class TestKnowledgeItemResource:
    """知识项资源测试"""
    
    def test_create_knowledge_item(self):
        """测试创建知识项"""
        resource = KnowledgeItemResource(
            id="kb:doc:001",
            name="采购流程文档",
            description="采购流程说明",
            uri="kb://doc:001",
            content="这是采购流程的详细说明...",
            content_type="document",
            source="knowledge_base"
        )
        
        assert resource.id == "kb:doc:001"
        assert resource.type == ResourceType.KNOWLEDGE_ITEM
        assert resource.content_type == "document"
        assert len(resource.content) > 0
    
    def test_get_metadata(self):
        """测试获取元数据"""
        resource = KnowledgeItemResource(
            id="ea:process:001",
            name="采购流程",
            description="企业架构中的采购流程",
            uri="ea://process:001",
            content="采购流程定义",
            content_type="ea_node",
            source="enterprise_architecture",
            vector_id="vec_12345"
        )
        
        metadata = resource.get_metadata()
        assert metadata["content_type"] == "ea_node"
        assert metadata["vector_id"] == "vec_12345"


class TestWorkflowResource:
    """工作流资源测试"""
    
    def test_create_workflow(self):
        """测试创建工作流"""
        workflow_def = {
            "steps": [
                {"name": "step1", "action": "create_po"},
                {"name": "step2", "action": "approve_po"}
            ]
        }
        
        resource = WorkflowResource(
            id="workflow:po_approval",
            name="采购订单审批流程",
            description="自动审批采购订单",
            uri="workflow://po_approval",
            workflow_definition=workflow_def,
            workflow_type="static"
        )
        
        assert resource.id == "workflow:po_approval"
        assert resource.type == ResourceType.WORKFLOW
        assert resource.workflow_type == "static"
        assert len(resource.workflow_definition["steps"]) == 2


class TestDataEntityResource:
    """数据实体资源测试"""
    
    def test_create_data_entity(self):
        """测试创建数据实体"""
        resource = DataEntityResource(
            id="table:orders",
            name="订单表",
            description="存储订单信息的数据表",
            uri="db://orders",
            entity_type="table",
            database_name="enterprise_db",
            schema_name="public",
            table_name="orders"
        )
        
        assert resource.id == "table:orders"
        assert resource.type == ResourceType.DATA_ENTITY
        assert resource.entity_type == "table"
        assert resource.table_name == "orders"
    
    def test_get_metadata(self):
        """测试获取元数据"""
        resource = DataEntityResource(
            id="field:orders:amount",
            name="订单金额字段",
            description="订单金额",
            uri="db://orders/amount",
            entity_type="field",
            table_name="orders",
            data_metadata={"data_type": "decimal", "nullable": False}
        )
        
        metadata = resource.get_metadata()
        assert metadata["entity_type"] == "field"
        assert metadata["data_type"] == "decimal"


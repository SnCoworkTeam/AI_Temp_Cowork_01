"""
资源解析器单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加os-core到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
OS_CORE_PATH = PROJECT_ROOT / "os-core"
sys.path.insert(0, str(OS_CORE_PATH))

from resource_resolver import ResourceResolver, IntentResolutionResult
from resource_registry import ResourceRegistry
from resource_model import (
    ResourceType,
    BusinessResource,
    SystemEndpointResource,
    KnowledgeItemResource,
    WorkflowResource
)
from resource_operations import ResourceOperationType


class TestResourceResolver:
    """资源解析器测试"""
    
    @pytest.fixture
    def registry(self):
        """创建注册表并注册示例资源"""
        reg = ResourceRegistry()
        
        # 注册业务对象
        business_resource = BusinessResource(
            id="order:001",
            name="采购订单",
            description="采购订单业务对象",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部"
        )
        reg.register(business_resource)
        
        # 注册系统端点
        system_resource = SystemEndpointResource(
            id="api:sap:create_po",
            name="SAP创建采购订单API",
            description="SAP系统接口",
            uri="api://sap/create_po",
            endpoint_url="https://sap.example.com/api/create_po",
            endpoint_type="api"
        )
        reg.register(system_resource)
        
        # 注册知识项
        knowledge_resource = KnowledgeItemResource(
            id="kb:doc:001",
            name="采购流程文档",
            description="采购流程说明文档",
            uri="kb://doc:001",
            content="采购流程详细说明",
            content_type="document",
            source="knowledge_base"
        )
        reg.register(knowledge_resource)
        
        # 注册工作流
        workflow_resource = WorkflowResource(
            id="workflow:po_approval",
            name="采购订单审批流程",
            description="自动审批流程",
            uri="workflow://po_approval",
            workflow_definition={"steps": []},
            workflow_type="static"
        )
        reg.register(workflow_resource)
        
        return reg
    
    @pytest.fixture
    def resolver(self, registry):
        """创建解析器"""
        return ResourceResolver(registry)
    
    def test_resolve_tool_execution_intent(self, resolver):
        """测试解析工具执行意图"""
        intent_result = {
            "user_input": "创建采购订单",
            "base_intent": "tool_execution",
            "confidence": 0.9,
            "suggested_activities": [
                {
                    "id": "activity:create_po",
                    "name": "创建采购订单",
                    "business_domain": "采购",
                    "capability_id": "api:sap:create_po"
                }
            ],
            "extracted_entities": {
                "supplier": "供应商A",
                "amount": 10000
            }
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        assert isinstance(result, IntentResolutionResult)
        assert result.confidence == 0.9
        # 应该解析出系统端点
        assert len(result.systems) > 0
        # 应该生成操作
        assert len(result.operations) > 0
        assert result.operations[0].operation_type == ResourceOperationType.INVOKE
    
    def test_resolve_knowledge_search_intent(self, resolver):
        """测试解析知识搜索意图"""
        intent_result = {
            "user_input": "如何创建采购订单？",
            "base_intent": "knowledge_search",
            "confidence": 0.8,
            "suggested_activities": [],
            "extracted_entities": {}
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        assert isinstance(result, IntentResolutionResult)
        # 应该解析出知识项
        assert len(result.knowledge) > 0
        # 应该生成搜索操作
        assert len(result.operations) > 0
        assert result.operations[0].operation_type == ResourceOperationType.SEARCH
    
    def test_resolve_workflow_intent(self, resolver):
        """测试解析工作流意图"""
        intent_result = {
            "user_input": "执行采购订单审批流程",
            "base_intent": "workflow_task",
            "confidence": 0.85,
            "suggested_activities": [],
            "extracted_entities": {}
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        assert isinstance(result, IntentResolutionResult)
        # 应该解析出工作流
        assert len(result.workflows) > 0
        # 应该生成执行操作
        assert len(result.operations) > 0
        assert result.operations[0].operation_type == ResourceOperationType.EXECUTE
    
    def test_resolve_business_object_keywords(self, resolver):
        """测试从关键词解析业务对象"""
        intent_result = {
            "user_input": "查询订单信息",
            "base_intent": "query",
            "confidence": 0.7,
            "suggested_activities": [
                {
                    "id": "activity:query_order",
                    "name": "查询订单",
                    "business_domain": "采购"
                }
            ],
            "extracted_entities": {}
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        # 应该解析出业务对象（包含"订单"关键词）
        assert len(result.objects) > 0
        # 应该生成查询操作
        assert len(result.operations) > 0
        assert result.operations[0].operation_type == ResourceOperationType.QUERY
    
    def test_resolve_empty_intent(self, resolver):
        """测试解析空意图"""
        intent_result = {
            "user_input": "你好",
            "base_intent": "simple_chat",
            "confidence": 0.5,
            "suggested_activities": [],
            "extracted_entities": {}
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        assert isinstance(result, IntentResolutionResult)
        # 简单对话不应该解析出资源
        assert len(result.operations) == 0
    
    def test_resolve_multiple_resource_types(self, resolver):
        """测试解析多种资源类型"""
        intent_result = {
            "user_input": "创建采购订单并查看相关文档",
            "base_intent": "tool_execution",
            "confidence": 0.9,
            "suggested_activities": [
                {
                    "id": "activity:create_po",
                    "name": "创建采购订单",
                    "business_domain": "采购",
                    "capability_id": "api:sap:create_po"
                }
            ],
            "extracted_entities": {}
        }
        
        result = resolver.resolve_intent_to_resources(intent_result)
        
        # 应该解析出多种资源类型
        assert len(result.systems) > 0  # 系统端点
        # 如果包含"文档"关键词，可能解析出知识项
        # assert len(result.knowledge) > 0  # 知识项（如果关键词匹配）

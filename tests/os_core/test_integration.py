"""
os-core集成测试
端到端测试：用户输入 → 意图识别 → 资源解析 → 操作执行
"""
import pytest
import sys
from pathlib import Path

# 添加os-core到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
OS_CORE_PATH = PROJECT_ROOT / "os-core"
sys.path.insert(0, str(OS_CORE_PATH))
sys.path.insert(0, str(OS_CORE_PATH / "adapters"))

from resource_registry import ResourceRegistry
from resource_resolver import ResourceResolver
from business_object_adapter import BusinessObjectAdapter
from system_endpoint_adapter import SystemEndpointAdapter
from knowledge_adapter import KnowledgeAdapter
from resource_model import ResourceType
from resource_operations import ResourceOperationType


class TestEndToEndIntegration:
    """端到端集成测试"""
    
    @pytest.fixture
    def setup_resources(self):
        """设置测试资源"""
        registry = ResourceRegistry()
        
        # 使用适配器注册资源
        business_adapter = BusinessObjectAdapter(registry)
        system_adapter = SystemEndpointAdapter(registry)
        knowledge_adapter = KnowledgeAdapter(registry)
        
        # 注册业务对象
        business_objects = [
            {
                "id": "order:001",
                "business_id": "ORDER-001",
                "name": "采购订单",
                "description": "采购订单业务对象",
                "owner_department": "采购部",
                "lifecycle_state": "active"
            }
        ]
        business_adapter.register_business_objects(business_objects, source="metadata")
        
        # 注册系统端点
        system_endpoints = [
            {
                "name": "sap_create_po",
                "display_name": "SAP创建采购订单API",
                "description": "SAP系统创建采购订单接口",
                "url": "https://sap.example.com/api/create_po",
                "auth_required": True
            }
        ]
        system_adapter.register_system_endpoints(system_endpoints, source="api")
        
        # 注册知识项
        knowledge_items = [
            {
                "id": "doc:procurement",
                "title": "采购流程文档",
                "description": "采购流程详细说明",
                "content": "这是采购流程的详细说明文档...",
                "category": "流程文档"
            }
        ]
        knowledge_adapter.register_knowledge_items(knowledge_items, source="kb")
        
        return registry
    
    @pytest.fixture
    def resolver(self, setup_resources):
        """创建解析器"""
        return ResourceResolver(setup_resources)
    
    def test_tool_execution_flow(self, resolver):
        """测试工具执行流程"""
        # 模拟意图识别结果
        intent_result = {
            "user_input": "创建采购订单",
            "base_intent": "tool_execution",
            "confidence": 0.9,
            "suggested_activities": [
                {
                    "id": "activity:create_po",
                    "name": "创建采购订单",
                    "business_domain": "采购",
                    "capability_id": "api:sap_create_po"
                }
            ],
            "extracted_entities": {
                "supplier": "供应商A",
                "amount": 10000
            }
        }
        
        # 解析意图到资源
        resolution = resolver.resolve_intent_to_resources(intent_result)
        
        # 验证解析结果
        assert resolution.confidence == 0.9
        assert len(resolution.systems) > 0  # 应该找到系统端点
        assert len(resolution.operations) > 0  # 应该生成操作
        
        # 验证操作类型
        operation = resolution.operations[0]
        assert operation.operation_type == ResourceOperationType.INVOKE
        assert operation.resource_type == ResourceType.SYSTEM_ENDPOINT.value
        assert "supplier" in operation.parameters
    
    def test_knowledge_search_flow(self, resolver):
        """测试知识搜索流程"""
        intent_result = {
            "user_input": "如何创建采购订单？",
            "base_intent": "knowledge_search",
            "confidence": 0.8,
            "suggested_activities": [],
            "extracted_entities": {}
        }
        
        resolution = resolver.resolve_intent_to_resources(intent_result)
        
        # 验证解析结果
        assert len(resolution.knowledge) > 0  # 应该找到知识项
        assert len(resolution.operations) > 0  # 应该生成搜索操作
        
        operation = resolution.operations[0]
        assert operation.operation_type == ResourceOperationType.SEARCH
        assert operation.resource_type == ResourceType.KNOWLEDGE_ITEM.value
    
    def test_query_business_object_flow(self, resolver):
        """测试查询业务对象流程"""
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
        
        resolution = resolver.resolve_intent_to_resources(intent_result)
        
        # 验证解析结果
        assert len(resolution.objects) > 0  # 应该找到业务对象
        assert len(resolution.operations) > 0  # 应该生成查询操作
        
        operation = resolution.operations[0]
        assert operation.operation_type == ResourceOperationType.QUERY
        assert operation.resource_type == ResourceType.BUSINESS_OBJECT.value
    
    def test_multi_resource_resolution(self, resolver):
        """测试多资源类型解析"""
        intent_result = {
            "user_input": "创建采购订单并查看相关文档",
            "base_intent": "tool_execution",
            "confidence": 0.9,
            "suggested_activities": [
                {
                    "id": "activity:create_po",
                    "name": "创建采购订单",
                    "business_domain": "采购",
                    "capability_id": "api:sap_create_po"
                }
            ],
            "extracted_entities": {}
        }
        
        resolution = resolver.resolve_intent_to_resources(intent_result)
        
        # 应该解析出多种资源类型
        assert len(resolution.systems) > 0  # 系统端点
        # 如果包含"文档"关键词，可能解析出知识项
        # 注意：这取决于关键词匹配逻辑


class TestResourceLifecycle:
    """资源生命周期测试"""
    
    def test_resource_registration_and_discovery(self):
        """测试资源注册和发现"""
        registry = ResourceRegistry()
        adapter = BusinessObjectAdapter(registry)
        
        # 注册资源
        objects = [
            {
                "id": "order:001",
                "business_id": "ORDER-001",
                "name": "采购订单001",
                "description": "测试订单",
                "owner_department": "采购部"
            }
        ]
        adapter.register_business_objects(objects, source="metadata")
        
        # 发现资源
        results = registry.discover("订单", limit=10)
        assert len(results) > 0
        
        # 通过ID获取
        resource = registry.get_by_id("order:001")
        assert resource is not None
        assert resource.name == "采购订单001"
        
        # 注销资源
        registry.unregister("order:001")
        resource = registry.get_by_id("order:001")
        assert resource is None


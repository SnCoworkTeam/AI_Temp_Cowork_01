"""
资源注册表单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加os-core到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
OS_CORE_PATH = PROJECT_ROOT / "os-core"
sys.path.insert(0, str(OS_CORE_PATH))

from resource_registry import ResourceRegistry
from resource_model import (
    ResourceType,
    BusinessResource,
    SystemEndpointResource,
    KnowledgeItemResource
)


class TestResourceRegistry:
    """资源注册表测试"""
    
    @pytest.fixture
    def registry(self):
        """创建注册表实例"""
        return ResourceRegistry()
    
    @pytest.fixture
    def sample_business_resource(self):
        """示例业务资源"""
        return BusinessResource(
            id="order:001",
            name="采购订单001",
            description="测试订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部"
        )
    
    @pytest.fixture
    def sample_system_resource(self):
        """示例系统端点资源"""
        return SystemEndpointResource(
            id="api:sap:create_po",
            name="SAP创建采购订单API",
            description="SAP系统创建采购订单接口",
            uri="api://sap/create_po",
            endpoint_url="https://sap.example.com/api/create_po",
            endpoint_type="api"
        )
    
    def test_register_resource(self, registry, sample_business_resource):
        """测试注册资源"""
        result = registry.register(sample_business_resource)
        assert result is True
        assert registry.count() == 1
    
    def test_get_by_id(self, registry, sample_business_resource):
        """测试根据ID获取资源"""
        registry.register(sample_business_resource)
        
        resource = registry.get_by_id("order:001")
        assert resource is not None
        assert resource.id == "order:001"
        assert resource.name == "采购订单001"
    
    def test_resolve_uri(self, registry, sample_business_resource):
        """测试URI解析"""
        registry.register(sample_business_resource)
        
        resource = registry.resolve("business://order:001")
        assert resource is not None
        assert resource.id == "order:001"
    
    def test_get_by_type(self, registry, sample_business_resource, sample_system_resource):
        """测试按类型查询"""
        registry.register(sample_business_resource)
        registry.register(sample_system_resource)
        
        business_resources = registry.get_by_type(ResourceType.BUSINESS_OBJECT)
        assert len(business_resources) == 1
        assert business_resources[0].id == "order:001"
        
        system_resources = registry.get_by_type(ResourceType.SYSTEM_ENDPOINT)
        assert len(system_resources) == 1
        assert system_resources[0].id == "api:sap:create_po"
    
    def test_discover_resources(self, registry, sample_business_resource):
        """测试资源发现（语义搜索）"""
        registry.register(sample_business_resource)
        
        # 搜索"订单"
        results = registry.discover("订单", limit=10)
        assert len(results) > 0
        assert any(r.id == "order:001" for r in results)
        
        # 搜索"采购"
        results = registry.discover("采购", limit=10)
        assert len(results) > 0
    
    def test_discover_with_type_filter(self, registry, sample_business_resource, sample_system_resource):
        """测试带类型过滤的资源发现"""
        registry.register(sample_business_resource)
        registry.register(sample_system_resource)
        
        # 只搜索业务对象
        results = registry.discover(
            "订单",
            resource_type=ResourceType.BUSINESS_OBJECT,
            limit=10
        )
        assert len(results) == 1
        assert results[0].type == ResourceType.BUSINESS_OBJECT
    
    def test_unregister_resource(self, registry, sample_business_resource):
        """测试注销资源"""
        registry.register(sample_business_resource)
        assert registry.count() == 1
        
        result = registry.unregister("order:001")
        assert result is True
        assert registry.count() == 0
        
        # 再次获取应该返回None
        resource = registry.get_by_id("order:001")
        assert resource is None
    
    def test_get_relationships(self, registry, sample_business_resource):
        """测试获取关联关系"""
        # 创建关联资源
        related_resource = BusinessResource(
            id="order:002",
            name="采购订单002",
            description="关联订单",
            uri="business://order:002",
            business_id="ORDER-002",
            owner_department="采购部"
        )
        registry.register(related_resource)
        
        # 设置关联关系（通过资源的get_relationships方法）
        # 注意：这里需要资源支持关联关系，简化测试
        relationships = registry.get_relationships("order:001")
        # 如果没有关联关系，应该返回空字典
        assert isinstance(relationships, dict)
    
    def test_count_by_type(self, registry, sample_business_resource, sample_system_resource):
        """测试按类型统计"""
        registry.register(sample_business_resource)
        registry.register(sample_system_resource)
        
        counts = registry.count_by_type()
        assert counts[ResourceType.BUSINESS_OBJECT] == 1
        assert counts[ResourceType.SYSTEM_ENDPOINT] == 1
    
    def test_register_duplicate(self, registry, sample_business_resource):
        """测试注册重复资源（应该更新）"""
        registry.register(sample_business_resource)
        assert registry.count() == 1
        
        # 注册相同ID的资源（更新）
        updated_resource = BusinessResource(
            id="order:001",
            name="采购订单001（已更新）",
            description="更新后的订单",
            uri="business://order:001",
            business_id="ORDER-001",
            owner_department="采购部"
        )
        registry.register(updated_resource)
        
        # 数量应该还是1
        assert registry.count() == 1
        # 但内容应该已更新
        resource = registry.get_by_id("order:001")
        assert "已更新" in resource.name
    
    def test_get_all(self, registry, sample_business_resource, sample_system_resource):
        """测试获取所有资源"""
        registry.register(sample_business_resource)
        registry.register(sample_system_resource)
        
        all_resources = registry.get_all()
        assert len(all_resources) == 2
        assert registry.count() == 2

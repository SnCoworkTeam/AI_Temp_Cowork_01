"""
性能测试
测试关键功能的性能指标
"""
import pytest
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "os-core"))

from os_core.resource_registry import ResourceRegistry
from os_core.resource_model import BusinessResource, ResourceType


class TestPerformance:
    """性能测试类"""
    
    def test_resource_discovery_performance(self):
        """测试资源发现性能（目标: <500ms）"""
        registry = ResourceRegistry()
        
        # 注册100个资源
        for i in range(100):
            resource = BusinessResource(
                id=f"business:order:{i:03d}",
                name=f"订单{i:03d}",
                description=f"订单描述{i}",
                uri=f"business://order/{i:03d}",
                business_id=f"order_{i:03d}"
            )
            registry.register(resource)
        
        # 测试发现性能
        start_time = time.time()
        results = registry.discover("订单", limit=10)
        duration_ms = (time.time() - start_time) * 1000
        
        assert len(results) > 0, "应该找到资源"
        assert duration_ms < 500, f"资源发现耗时 {duration_ms}ms，超过目标500ms"
        
        print(f"✅ 资源发现性能: {duration_ms:.2f}ms (目标: <500ms)")
    
    def test_resource_registry_cache(self):
        """测试资源注册表缓存效果"""
        registry = ResourceRegistry()
        
        # 注册资源
        for i in range(50):
            resource = BusinessResource(
                id=f"business:order:{i:03d}",
                name=f"订单{i:03d}",
                description=f"订单描述{i}",
                uri=f"business://order/{i:03d}",
                business_id=f"order_{i:03d}"
            )
            registry.register(resource)
        
        # 第一次查询（无缓存）
        start_time = time.time()
        results1 = registry.discover("订单", limit=10)
        duration1 = (time.time() - start_time) * 1000
        
        # 第二次查询（有缓存）
        start_time = time.time()
        results2 = registry.discover("订单", limit=10)
        duration2 = (time.time() - start_time) * 1000
        
        assert len(results1) == len(results2), "缓存结果应该一致"
        assert duration2 < duration1, "缓存查询应该更快"
        
        print(f"✅ 缓存效果: 首次 {duration1:.2f}ms, 缓存 {duration2:.2f}ms, 提升 {((duration1 - duration2) / duration1 * 100):.1f}%")
    
    def test_resource_registry_scale(self):
        """测试资源注册表扩展性"""
        registry = ResourceRegistry()
        
        # 测试不同规模的性能
        scales = [10, 100, 1000]
        results = {}
        
        for scale in scales:
            # 注册资源
            for i in range(scale):
                resource = BusinessResource(
                    id=f"business:order:{i:06d}",
                    name=f"订单{i:06d}",
                    description=f"订单描述{i}",
                    uri=f"business://order/{i:06d}",
                    business_id=f"order_{i:06d}"
                )
                registry.register(resource)
            
            # 测试查询性能
            start_time = time.time()
            results_query = registry.discover("订单", limit=10)
            duration_ms = (time.time() - start_time) * 1000
            
            results[scale] = duration_ms
            print(f"  规模 {scale}: {duration_ms:.2f}ms")
        
        # 验证性能增长是合理的（不应该线性增长）
        assert results[100] < results[10] * 20, "性能增长应该合理"
        assert results[1000] < results[100] * 15, "大规模下性能应该可接受"
        
        print(f"✅ 扩展性测试通过")


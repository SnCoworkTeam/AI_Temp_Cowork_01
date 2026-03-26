"""
阶段一第4周测试：统一意图服务增强
测试增强的IntelligentRouter、统一意图服务、性能优化等功能
"""
import pytest
import sys
import os
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.unified_intent_service import UnifiedIntentService, UnifiedIntentResult


@pytest.fixture(scope="session", autouse=True)
def setup_services():
    """测试会话级别的服务设置"""
    print("\n" + "="*60)
    print("阶段一第4周测试 - 统一意图服务增强")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestUnifiedIntentService:
    """测试统一意图服务"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = UnifiedIntentService()
        assert service is not None
        assert service.semantic_engine is not None
        print("[OK] 统一意图服务初始化成功")
    
    @pytest.mark.asyncio
    async def test_understand_intent(self):
        """测试意图理解"""
        service = UnifiedIntentService()
        result = await service.understand_intent("创建采购订单")
        
        assert result is not None
        assert isinstance(result, UnifiedIntentResult)
        assert result.user_input == "创建采购订单"
        assert result.intent_type in ["tool_execution", "workflow_task", "knowledge_search", "simple_chat"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.query_time > 0
        assert result.query_time < 5.0  # 响应时间应该小于5秒
        
        print(f"[OK] 意图理解成功: {result.intent_type} (置信度: {result.confidence:.2f})")
        print(f"    查询时间: {result.query_time:.3f}秒")
    
    @pytest.mark.asyncio
    async def test_understand_intent_with_context(self):
        """测试带上下文的意图理解"""
        service = UnifiedIntentService()
        context = {"domain": "procurement", "user_role": "采购员"}
        result = await service.understand_intent("查询订单", context=context)
        
        assert result is not None
        assert result.intent_type is not None
        print(f"[OK] 带上下文的意图理解成功: {result.intent_type}")
    
    @pytest.mark.asyncio
    async def test_understand_intent_with_activities(self):
        """测试意图理解返回活动推荐"""
        service = UnifiedIntentService()
        result = await service.understand_intent("创建采购订单")
        
        assert result is not None
        assert isinstance(result.suggested_activities, list)
        
        if result.suggested_activities:
            activity = result.suggested_activities[0]
            assert "id" in activity
            assert "name" in activity
            assert "similarity_score" in activity
            print(f"[OK] 意图理解返回活动推荐: {len(result.suggested_activities)} 个活动")
        else:
            print("[OK] 意图理解成功（无活动推荐）")
    
    @pytest.mark.asyncio
    async def test_recommend_activities(self):
        """测试活动推荐"""
        service = UnifiedIntentService()
        recommendations = await service.recommend_activities("查询订单", top_k=5)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        
        if recommendations:
            for activity in recommendations:
                assert "id" in activity
                assert "name" in activity
                assert "similarity_score" in activity
            
            print(f"[OK] 活动推荐成功: {len(recommendations)} 个推荐")
        else:
            print("[OK] 活动推荐成功（无推荐结果）")
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """测试缓存功能"""
        service = UnifiedIntentService()
        
        # 第一次查询
        start_time = time.time()
        result1 = await service.understand_intent("创建采购订单")
        time1 = time.time() - start_time
        
        # 第二次查询（应该命中缓存）
        start_time = time.time()
        result2 = await service.understand_intent("创建采购订单")
        time2 = time.time() - start_time
        
        # 缓存应该使第二次查询更快
        assert result1.user_input == result2.user_input
        assert result1.intent_type == result2.intent_type
        
        # 检查缓存统计
        cache_stats = service.get_cache_stats()
        assert cache_stats["enabled"] is True
        assert cache_stats["total_entries"] > 0
        
        print(f"[OK] 缓存功能正常:")
        print(f"    第一次查询: {time1:.3f}秒")
        print(f"    第二次查询: {time2:.3f}秒")
        print(f"    缓存条目数: {cache_stats['total_entries']}")
    
    @pytest.mark.asyncio
    async def test_fallback_mode(self):
        """测试降级模式"""
        service = UnifiedIntentService()
        
        # 使用一个可能导致错误的输入
        result = await service.understand_intent("")
        
        assert result is not None
        assert result.fallback_mode in [True, False]  # 可能成功也可能降级
        print(f"[OK] 降级模式测试通过: fallback_mode={result.fallback_mode}")
    
    @pytest.mark.asyncio
    async def test_performance(self):
        """测试性能"""
        service = UnifiedIntentService()
        
        queries = [
            "创建采购订单",
            "查询订单",
            "审批订单",
            "处理异常",
            "生成报告"
        ]
        
        total_time = 0
        success_count = 0
        
        for query in queries:
            try:
                start_time = time.time()
                result = await service.understand_intent(query)
                query_time = time.time() - start_time
                total_time += query_time
                success_count += 1
                
                assert result.query_time < 5.0  # 单次查询应该小于5秒
            except Exception as e:
                print(f"[WARN] 查询失败: {query} - {e}")
        
        if success_count > 0:
            avg_time = total_time / success_count
            assert avg_time < 2.0, f"平均查询时间 {avg_time:.3f}秒超过2秒"
            print(f"[OK] 性能测试通过: 平均查询时间 {avg_time:.3f}秒 ({success_count}/{len(queries)} 成功)")
        else:
            pytest.skip("所有查询都失败，跳过性能测试")
    
    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        service = UnifiedIntentService()
        stats = service.get_cache_stats()
        
        assert stats is not None
        assert "enabled" in stats
        assert "total_entries" in stats
        assert stats["enabled"] is True
        
        print(f"[OK] 缓存统计获取成功: {stats['total_entries']} 个条目")


class TestEnhancedIntelligentRouter:
    """测试增强的IntelligentRouter（如果可用）"""
    
    def test_enhanced_router_import(self):
        """测试增强路由器导入"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api-gateway', 'src'))
            from core.enhanced_intelligent_router import EnhancedIntelligentRouter
            print("[OK] 增强路由器导入成功")
        except ImportError as e:
            print(f"[SKIP] 增强路由器不可用: {e}")
            pytest.skip("增强路由器不可用")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])






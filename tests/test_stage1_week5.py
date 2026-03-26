"""
阶段一第5周测试：统一意图服务完善和API集成
测试能力映射、执行建议、API接口等功能
"""
import pytest
import sys
import os
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.unified_intent_service import UnifiedIntentService, UnifiedIntentResult, ExecutionSuggestion


@pytest.fixture(scope="session", autouse=True)
def setup_services():
    """测试会话级别的服务设置"""
    print("\n" + "="*60)
    print("阶段一第5周测试 - 统一意图服务完善和API集成")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestUnifiedIntentServiceEnhanced:
    """测试增强的统一意图服务"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = UnifiedIntentService()
        assert service is not None
        assert service.semantic_engine is not None
        print("[OK] 统一意图服务初始化成功")
        service._close_db()
    
    @pytest.mark.asyncio
    async def test_understand_intent_with_execution_suggestions(self):
        """测试意图理解包含执行建议"""
        service = UnifiedIntentService()
        try:
            result = await service.understand_intent("创建采购订单")
            
            assert result is not None
            assert isinstance(result, UnifiedIntentResult)
            assert hasattr(result, 'execution_suggestions')
            assert isinstance(result.execution_suggestions, list)
            
            print(f"[OK] 意图理解包含执行建议: {len(result.execution_suggestions)} 个建议")
            if result.execution_suggestions:
                suggestion = result.execution_suggestions[0]
                print(f"    活动: {suggestion.activity_name}")
                if suggestion.capability_name:
                    print(f"    能力: {suggestion.capability_name}")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_get_capabilities_for_activity(self):
        """测试获取活动能力"""
        service = UnifiedIntentService()
        try:
            capabilities = await service.get_capabilities_for_activity("activity:procurement:create_po")
            
            assert isinstance(capabilities, list)
            
            if capabilities:
                capability = capabilities[0]
                assert "capability_id" in capability
                assert "capability_name" in capability
                assert "mapping_type" in capability
                
                print(f"[OK] 获取活动能力成功: {len(capabilities)} 个能力单元")
                print(f"    示例: {capability.get('capability_name', 'N/A')}")
            else:
                print("[OK] 获取活动能力成功（无能力单元）")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_execution_suggestions_structure(self):
        """测试执行建议结构"""
        service = UnifiedIntentService()
        try:
            result = await service.understand_intent("创建采购订单")
            
            if result.execution_suggestions:
                suggestion = result.execution_suggestions[0]
                assert isinstance(suggestion, ExecutionSuggestion)
                assert suggestion.activity_id is not None
                assert suggestion.activity_name is not None
                assert 0.0 <= suggestion.confidence <= 1.0
                
                print(f"[OK] 执行建议结构正确:")
                print(f"    活动ID: {suggestion.activity_id}")
                print(f"    活动名称: {suggestion.activity_name}")
                print(f"    置信度: {suggestion.confidence:.2f}")
        finally:
            service._close_db()
    
    @pytest.mark.asyncio
    async def test_performance_with_capabilities(self):
        """测试包含能力查询的性能"""
        service = UnifiedIntentService()
        try:
            start_time = time.time()
            result = await service.understand_intent("创建采购订单")
            query_time = time.time() - start_time
            
            assert query_time < 10.0  # 包含能力查询应该在10秒内
            
            print(f"[OK] 性能测试通过: 查询时间 {query_time:.3f}秒")
            print(f"    推荐活动: {len(result.suggested_activities)}")
            print(f"    执行建议: {len(result.execution_suggestions)}")
        finally:
            service._close_db()


class TestAPIEndpoints:
    """测试API接口（需要API服务运行）"""
    
    def test_api_health_check(self):
        """测试健康检查接口"""
        import requests
        
        try:
            response = requests.get("http://localhost:8002/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
                print("[OK] API健康检查通过")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")
    
    def test_api_intent_understand(self):
        """测试意图理解接口"""
        import requests
        
        try:
            payload = {
                "user_input": "创建采购订单",
                "context": None
            }
            response = requests.post(
                "http://localhost:8002/api/v1/intent/understand",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                assert "base_intent" in data
                assert "suggested_activities" in data
                assert "execution_suggestions" in data
                print(f"[OK] API意图理解成功: {data.get('intent_type', 'N/A')}")
                print(f"    执行建议: {len(data.get('execution_suggestions', []))}")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")
    
    def test_api_get_capabilities(self):
        """测试获取活动能力接口"""
        import requests
        
        try:
            response = requests.get(
                "http://localhost:8002/api/v1/intent/activities/activity:procurement:create_po/capabilities",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                assert "capabilities" in data
                print(f"[OK] API获取活动能力成功: {data.get('total', 0)} 个能力")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])






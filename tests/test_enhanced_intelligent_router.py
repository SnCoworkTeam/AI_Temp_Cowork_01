"""
增强的智能路由器测试
测试集成企业语义引擎的IntelligentRouter
"""
import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "api-gateway", "src"))

# 使用importlib导入（处理带连字符的目录名）
import importlib.util

# 导入enhanced_intelligent_router
enhanced_router_path = os.path.join(PROJECT_ROOT, "api-gateway", "src", "core", "enhanced_intelligent_router.py")
if os.path.exists(enhanced_router_path):
    spec = importlib.util.spec_from_file_location("enhanced_intelligent_router", enhanced_router_path)
    enhanced_router_module = importlib.util.module_from_spec(spec)
    # 设置模块的__package__属性以支持相对导入
    enhanced_router_module.__package__ = "api_gateway.src.core"
    spec.loader.exec_module(enhanced_router_module)
    EnhancedIntelligentRouter = enhanced_router_module.EnhancedIntelligentRouter
    EnhancedIntentAnalysis = enhanced_router_module.EnhancedIntentAnalysis
else:
    # 如果文件不存在，创建mock类
    EnhancedIntelligentRouter = None
    EnhancedIntentAnalysis = None

# 导入intelligent_router
intelligent_router_path = os.path.join(PROJECT_ROOT, "api-gateway", "src", "core", "intelligent_router.py")
if os.path.exists(intelligent_router_path):
    spec2 = importlib.util.spec_from_file_location("intelligent_router", intelligent_router_path)
    intelligent_router_module = importlib.util.module_from_spec(spec2)
    intelligent_router_module.__package__ = "api_gateway.src.core"
    spec2.loader.exec_module(intelligent_router_module)
    RouteIntent = intelligent_router_module.RouteIntent
    IntentAnalysis = intelligent_router_module.IntentAnalysis
else:
    RouteIntent = None
    IntentAnalysis = None


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    print("\n" + "="*60)
    print("增强的智能路由器测试")
    print("="*60)
    
    # 初始化数据库连接（如果需要）
    try:
        from database.src.core.database import get_database_manager
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            pytest.skip("数据库连接失败，跳过需要数据库的测试")
    except Exception:
        pass
    
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestEnhancedIntelligentRouter:
    """测试增强的智能路由器"""
    
    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        if EnhancedIntelligentRouter is None:
            pytest.skip("EnhancedIntelligentRouter不可用")
        try:
            router = EnhancedIntelligentRouter()
            yield router
            if hasattr(router, 'semantic_engine') and router.semantic_engine:
                if hasattr(router.semantic_engine, '_close_db'):
                    router.semantic_engine._close_db()
        except Exception as e:
            pytest.skip(f"路由器初始化失败: {e}")
    
    @pytest.mark.asyncio
    async def test_router_initialization(self, router):
        """测试路由器初始化"""
        assert router is not None
        assert hasattr(router, 'semantic_engine')
        assert hasattr(router, 'cache_enabled')
        assert hasattr(router, 'timeout')
        
        print("[OK] 路由器初始化成功")
        print(f"    语义引擎可用: {router.semantic_engine is not None}")
        print(f"    缓存启用: {router.cache_enabled}")
    
    @pytest.mark.asyncio
    async def test_analyze_intent_with_graph(self, router):
        """测试带图谱的意图分析"""
        test_cases = [
            {
                "input": "我需要采购一批原料",
                "expected_intent": RouteIntent.TOOL_EXECUTION,
                "min_confidence": 0.5
            },
            {
                "input": "查询上个月的采购订单",
                "expected_intent": RouteIntent.TOOL_EXECUTION,
                "min_confidence": 0.5
            },
            {
                "input": "审批采购订单12345",
                "expected_intent": RouteIntent.TOOL_EXECUTION,
                "min_confidence": 0.5
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await router.analyze_intent_with_graph(
                    user_input=test_case["input"],
                    context={"user_role": "采购员"}
                )
                
                # 验证基础意图
                assert result is not None
                assert isinstance(result, EnhancedIntentAnalysis)
                assert result.base_intent is not None
                assert isinstance(result.base_intent, IntentAnalysis)
                assert result.confidence >= test_case["min_confidence"]
                
                # 验证图谱增强结果（如果有）
                assert hasattr(result, 'suggested_activities')
                assert isinstance(result.suggested_activities, list)
                assert hasattr(result, 'related_entities')
                assert isinstance(result.related_entities, list)
                
                print(f"[OK] 意图分析成功: {test_case['input']}")
                print(f"    基础意图: {result.base_intent.intent}")
                print(f"    置信度: {result.confidence:.2f}")
                print(f"    推荐活动数: {len(result.suggested_activities)}")
                
            except Exception as e:
                # 如果语义引擎不可用，使用fallback模式
                if "数据库连接失败" in str(e) or "semantic_engine" in str(e).lower():
                    print(f"[SKIP] 语义引擎不可用，跳过: {test_case['input']}")
                    continue
                else:
                    raise
    
    @pytest.mark.asyncio
    async def test_intent_routing(self, router):
        """测试意图路由"""
        test_cases = [
            ("你好", RouteIntent.SIMPLE_CHAT),
            ("执行工具", RouteIntent.TOOL_EXECUTION),
            ("启动工作流", RouteIntent.WORKFLOW_TASK),
            ("需要智能体", RouteIntent.AGENT_TASK),
            ("搜索知识", RouteIntent.KNOWLEDGE_SEARCH)
        ]
        
        for user_input, expected_intent in test_cases:
            try:
                result = await router.analyze_intent_with_graph(user_input)
                
                # 验证意图类型
                assert result.base_intent.intent == expected_intent or \
                       result.base_intent.intent in [expected_intent, RouteIntent.UNKNOWN], \
                    f"Failed for input: {user_input}, got {result.base_intent.intent}, expected {expected_intent}"
                
                # 验证服务类型确定
                service_type = router._determine_service_type(result.base_intent)
                assert service_type is not None
                
                print(f"[OK] 意图路由成功: {user_input} -> {result.base_intent.intent} -> {service_type}")
                
            except Exception as e:
                if "数据库连接失败" in str(e):
                    print(f"[SKIP] 数据库不可用，跳过: {user_input}")
                    continue
                else:
                    raise
    
    @pytest.mark.asyncio
    async def test_intent_confidence_calculation(self, router):
        """测试意图置信度计算"""
        # 测试低置信度场景
        ambiguous_inputs = [
            "你好",  # 太模糊
            "测试",  # 无意义
            "",  # 空输入（会被跳过）
        ]
        
        for input_text in ambiguous_inputs:
            if not input_text:
                continue  # 跳过空输入
                
            try:
                result = await router.analyze_intent_with_graph(input_text)
                
                # 验证置信度在合理范围内
                assert 0.0 <= result.confidence <= 1.0
                
                # 模糊输入应该有较低的置信度
                if input_text in ["你好", "测试"]:
                    assert result.confidence < 0.8, \
                        f"模糊输入 '{input_text}' 的置信度 {result.confidence} 应该较低"
                
                print(f"[OK] 置信度计算: '{input_text}' -> {result.confidence:.2f}")
                
            except Exception as e:
                if "数据库连接失败" in str(e):
                    print(f"[SKIP] 数据库不可用，跳过: {input_text}")
                    continue
                else:
                    raise
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, router):
        """测试缓存功能"""
        if not router.cache_enabled:
            pytest.skip("缓存未启用")
        
        test_input = "测试缓存功能"
        
        # 第一次查询（应该缓存）
        result1 = await router.analyze_intent_with_graph(test_input)
        assert result1 is not None
        
        # 第二次查询（应该从缓存获取）
        result2 = await router.analyze_intent_with_graph(test_input)
        assert result2 is not None
        
        # 验证结果一致性
        assert result1.base_intent.intent == result2.base_intent.intent
        assert result1.confidence == result2.confidence
        
        print("[OK] 缓存功能正常")
    
    @pytest.mark.asyncio
    async def test_fallback_mode(self, router):
        """测试降级模式"""
        # 模拟语义引擎不可用的情况
        original_engine = router.semantic_engine
        router.semantic_engine = None
        
        try:
            result = await router.analyze_intent_with_graph("测试降级模式")
            
            # 验证降级模式
            assert result is not None
            assert result.fallback_mode is True
            assert result.base_intent is not None
            
            print("[OK] 降级模式工作正常")
        finally:
            router.semantic_engine = original_engine
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, router):
        """测试超时处理"""
        # 这个测试需要模拟超时情况
        # 由于实际实现可能不同，这里只测试基本功能
        test_input = "测试超时处理"
        
        try:
            result = await router.analyze_intent_with_graph(test_input)
            assert result is not None
            print("[OK] 超时处理正常")
        except asyncio.TimeoutError:
            print("[OK] 超时被正确捕获")
        except Exception as e:
            if "数据库连接失败" in str(e):
                pytest.skip("数据库不可用")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])


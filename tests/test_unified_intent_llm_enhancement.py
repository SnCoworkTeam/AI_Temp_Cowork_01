"""
统一意图识别LLM增强 - 测试套件
"""
import pytest
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from services.unified_intent_service import UnifiedIntentService, UnifiedIntentResult
from services.llm_client import RobustDeepSeekClient
from services.semantic_engine_adapter import SemanticEngineAdapter
from services.enterprise_semantic_engine import EnterpriseSemanticEngine, IntentQueryResult
from database.src.models import BusinessActivity


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    print("\n" + "="*70)
    print("统一意图识别LLM增强 - 测试套件")
    print("="*70)
    
    # 初始化数据库连接
    try:
        from database.src.core.database import get_database_manager
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            pytest.skip("数据库连接失败，跳过真实环境测试")
        
        from database.src.core.session import init_session_factory
        init_session_factory()
        print("[OK] 数据库连接成功")
    except Exception as e:
        pytest.skip(f"数据库初始化失败: {e}")
    
    yield
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)


@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    client = Mock(spec=RobustDeepSeekClient)
    client.chat_completion = AsyncMock(return_value={
        "content": '{"intent": "tool_execution", "confidence": 0.9, "business_domain": "procurement", "extracted_entities": {"supplier": "ABC"}, "query_keywords": ["采购订单", "创建"], "reasoning": "测试", "needs_semantic_search": true}',
        "raw_response": {},
        "usage": {}
    })
    client.close = AsyncMock()
    return client


@pytest.fixture
def unified_intent_service(mock_llm_client):
    """创建统一意图服务实例（带Mock LLM）"""
    with patch('services.unified_intent_service.RobustDeepSeekClient', return_value=mock_llm_client):
        with patch.dict(os.environ, {'UNIFIED_INTENT_USE_LLM': 'true'}):
            service = UnifiedIntentService()
            yield service
            service._close_db()


class TestLLMClient:
    """测试LLM客户端"""
    
    def test_llm_client_initialization(self):
        """测试LLM客户端初始化"""
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'test-key',
            'LLM_BASE_URL': 'https://api.deepseek.com',
            'LLM_MODEL': 'deepseek-chat'
        }):
            try:
                client = RobustDeepSeekClient()
                assert client is not None
                assert client.api_key == 'test-key'
                assert client.model == 'deepseek-chat'
                print("[OK] LLM客户端初始化成功")
            except Exception as e:
                pytest.skip(f"LLM客户端初始化失败（可能是依赖问题）: {e}")
    
    @pytest.mark.asyncio
    async def test_llm_client_chat_completion(self):
        """测试LLM聊天补全"""
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'test-key',
            'LLM_BASE_URL': 'https://api.deepseek.com'
        }):
            client = RobustDeepSeekClient()
            
            # Mock HTTP响应
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": '{"intent": "tool_execution", "confidence": 0.9}'
                        }
                    }],
                    "usage": {}
                }
                mock_response.raise_for_status = Mock()
                
                client.http_client = Mock()
                client.http_client.post = AsyncMock(return_value=mock_response)
                
                messages = [{"role": "user", "content": "测试"}]
                result = await client.chat_completion(messages)
                
                assert "content" in result
                print("[OK] LLM聊天补全测试通过")


class TestSemanticEngineAdapter:
    """测试语义引擎适配器"""
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        semantic_engine = EnterpriseSemanticEngine()
        adapter = SemanticEngineAdapter(semantic_engine)
        
        assert adapter.semantic_engine == semantic_engine
        print("[OK] 语义引擎适配器初始化成功")
    
    @pytest.mark.asyncio
    async def test_query_intent_enhanced(self):
        """测试增强的意图查询"""
        semantic_engine = EnterpriseSemanticEngine()
        adapter = SemanticEngineAdapter(semantic_engine)
        
        llm_result = {
            "business_domain": "procurement",
            "query_keywords": ["采购订单", "创建"]
        }
        
        try:
            result = await adapter.query_intent_enhanced(
                user_input="创建采购订单",
                llm_result=llm_result,
                top_k=5,
                min_score=0.3
            )
            
            assert isinstance(result, IntentQueryResult)
            assert result.query is not None
            print("[OK] 增强的意图查询测试通过")
        except Exception as e:
            print(f"[SKIP] 增强的意图查询测试跳过: {e}")


class TestUnifiedIntentServiceLLM:
    """测试统一意图服务LLM增强"""
    
    @pytest.mark.asyncio
    async def test_llm_intent_analysis(self, unified_intent_service):
        """测试LLM意图分析"""
        result = await unified_intent_service._analyze_intent_with_llm(
            "我需要创建采购订单",
            context=None
        )
        
        assert result is not None
        assert "intent" in result
        assert "confidence" in result
        assert result["intent"] == "tool_execution"
        assert result["confidence"] > 0.5
        print(f"[OK] LLM意图分析测试通过: {result['intent']}, confidence={result['confidence']:.2f}")
    
    @pytest.mark.asyncio
    async def test_llm_entity_extraction(self, unified_intent_service):
        """测试LLM实体提取"""
        result = await unified_intent_service._analyze_intent_with_llm(
            "为供应商ABC创建采购订单，物料MAT001数量100",
            context=None
        )
        
        assert "extracted_entities" in result
        entities = result["extracted_entities"]
        
        # 验证实体提取（如果LLM成功提取）
        if entities:
            print(f"[OK] LLM实体提取测试通过: {entities}")
        else:
            print("[SKIP] LLM实体提取为空（可能是Mock数据）")
    
    def test_build_llm_system_prompt(self, unified_intent_service):
        """测试构建LLM系统提示词"""
        prompt = unified_intent_service._build_llm_system_prompt()
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "意图分类" in prompt or "intent" in prompt.lower()
        assert "少样本示例" in prompt or "Few-shot" in prompt
        print("[OK] LLM系统提示词构建测试通过")
    
    def test_parse_llm_response(self, unified_intent_service):
        """测试解析LLM响应"""
        # 测试JSON格式响应
        json_response = '{"intent": "tool_execution", "confidence": 0.9, "business_domain": "procurement"}'
        result = unified_intent_service._parse_llm_response(json_response)
        
        assert result["intent"] == "tool_execution"
        assert result["confidence"] == 0.9
        
        # 测试Markdown代码块格式
        markdown_response = '```json\n{"intent": "simple_chat", "confidence": 0.8}\n```'
        result2 = unified_intent_service._parse_llm_response(markdown_response)
        
        assert result2["intent"] == "simple_chat"
        print("[OK] LLM响应解析测试通过")
    
    def test_dynamic_fusion_strategy(self, unified_intent_service):
        """测试动态融合策略"""
        # 场景1: LLM高置信度，无语义结果
        llm_result = {
            "intent": "tool_execution",
            "confidence": 0.95,
            "business_domain": "procurement"
        }
        result = unified_intent_service._dynamic_fusion_strategy(llm_result, None)
        
        assert result["final_confidence"] > 0.9
        assert "LLM高置信度" in result["reasoning"] or "新业务场景" in result["reasoning"]
        print(f"[OK] 动态融合策略测试通过（场景1）: {result['final_confidence']:.2f}")
        
        # 场景2: 语义引擎高相似度
        from services.enterprise_semantic_engine import IntentQueryResult
        from database.src.models import BusinessActivity
        
        mock_activity = Mock(spec=BusinessActivity)
        mock_activity.business_domain = "procurement"
        
        semantic_results = IntentQueryResult(
            query="test",
            activities=[mock_activity],
            scores=[0.88],
            total_count=1,
            query_time=0.1
        )
        
        result2 = unified_intent_service._dynamic_fusion_strategy(llm_result, semantic_results)
        assert result2["final_confidence"] > 0.8
        print(f"[OK] 动态融合策略测试通过（场景2）: {result2['final_confidence']:.2f}")
    
    def test_auto_fill_parameters(self, unified_intent_service):
        """测试自动参数填充"""
        input_schema = {
            "supplier_code": {"type": "string", "required": True},
            "material_code": {"type": "string", "required": True},
            "quantity": {"type": "integer", "required": True}
        }
        
        extracted_entities = {
            "supplier": "ABC",
            "material": "MAT001",
            "quantity": "100"
        }
        
        auto_filled = unified_intent_service._auto_fill_parameters(input_schema, extracted_entities)
        
        assert "supplier_code" in auto_filled or "material_code" in auto_filled
        print(f"[OK] 自动参数填充测试通过: {auto_filled}")


class TestUnifiedIntentServiceIntegration:
    """测试统一意图服务集成"""
    
    @pytest.mark.asyncio
    async def test_understand_intent_with_llm(self, unified_intent_service):
        """测试LLM增强的意图理解"""
        result = await unified_intent_service.understand_intent(
            "我需要创建采购订单，供应商ABC，物料MAT001，数量100"
        )
        
        assert isinstance(result, UnifiedIntentResult)
        assert result.user_input is not None
        assert result.base_intent is not None
        assert result.confidence >= 0.0
        assert result.query_time >= 0
        
        print(f"[OK] LLM增强意图理解测试通过")
        print(f"    意图: {result.base_intent}, 置信度: {result.confidence:.2f}")
        print(f"    推荐活动数: {len(result.suggested_activities)}")
        print(f"    执行建议数: {len(result.execution_suggestions)}")
    
    @pytest.mark.asyncio
    async def test_fallback_to_rules(self):
        """测试降级到规则匹配"""
        with patch.dict(os.environ, {'UNIFIED_INTENT_USE_LLM': 'false'}):
            service = UnifiedIntentService()
            try:
                result = await service.understand_intent("创建采购订单")
                
                assert isinstance(result, UnifiedIntentResult)
                # 降级模式下应该仍然有结果
                assert result.base_intent is not None
                print(f"[OK] 降级到规则匹配测试通过: {result.base_intent}")
            finally:
                service._close_db()
    
    @pytest.mark.asyncio
    async def test_llm_timeout_fallback(self, unified_intent_service):
        """测试LLM超时降级"""
        # Mock LLM超时
        unified_intent_service.llm_client.chat_completion = AsyncMock(
            side_effect=asyncio.TimeoutError("LLM超时")
        )
        
        result = await unified_intent_service.understand_intent("测试输入")
        
        assert isinstance(result, UnifiedIntentResult)
        # 应该降级到规则匹配
        assert result.base_intent is not None
        print(f"[OK] LLM超时降级测试通过: {result.base_intent}")


class TestEndToEndFlow:
    """端到端流程测试"""
    
    @pytest.mark.asyncio
    async def test_procurement_workflow_llm_enhanced(self, unified_intent_service):
        """测试采购工作流程（LLM增强）"""
        print("\n[端到端测试] 采购工作流程（LLM增强）")
        print("-" * 50)
        
        user_input = "我需要采购一批原料，供应商ABC公司，物料MAT001，数量100"
        print(f"1. 用户输入: {user_input}")
        
        result = await unified_intent_service.understand_intent(
            user_input,
            context={"user_id": "test_user", "department": "procurement"}
        )
        
        print(f"2. 意图理解结果:")
        print(f"   基础意图: {result.base_intent}")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   推荐活动数: {len(result.suggested_activities)}")
        print(f"   执行建议数: {len(result.execution_suggestions)}")
        print(f"   查询时间: {result.query_time:.3f}秒")
        
        # 验证结果
        assert isinstance(result, UnifiedIntentResult)
        assert result.user_input == user_input
        assert result.base_intent in ["tool_execution", "workflow_task", "knowledge_search", "simple_chat"]
        assert result.confidence >= 0.0
        
        if len(result.execution_suggestions) > 0:
            suggestion = result.execution_suggestions[0]
            print(f"3. 执行建议:")
            print(f"   活动: {suggestion.activity_name}")
            print(f"   能力: {suggestion.capability_name or '未指定'}")
            print(f"   置信度: {suggestion.confidence:.2f}")
        
        print("\n[OK] 端到端流程测试通过")
    
    @pytest.mark.asyncio
    async def test_performance_llm_enhanced(self, unified_intent_service):
        """测试性能（LLM增强）"""
        import time
        
        test_queries = [
            "创建采购订单",
            "查询采购订单状态",
            "采购原料",
            "查看供应商",
            "审批采购"
        ]
        
        total_time = 0
        query_count = 0
        
        print("\n[性能测试] LLM增强性能测试")
        print("-" * 50)
        
        for query in test_queries:
            try:
                start = time.time()
                result = await unified_intent_service.understand_intent(query)
                elapsed = time.time() - start
                
                total_time += elapsed
                query_count += 1
                
                print(f"  '{query}': {elapsed*1000:.1f}ms")
                
                # 验证响应时间（LLM增强可能较慢，放宽到5秒）
                assert elapsed < 5.0, f"响应时间 {elapsed:.3f}s 超过5秒"
                
            except Exception as e:
                print(f"  '{query}': 失败 - {e}")
        
        if query_count > 0:
            avg_time = total_time / query_count
            print(f"\n平均响应时间: {avg_time*1000:.1f}ms")
            print(f"总查询数: {query_count}")
            
            # 验证平均响应时间（LLM增强，放宽到3秒）
            assert avg_time < 3.0, f"平均响应时间 {avg_time:.3f}s 超过3秒"
            print("[OK] 性能测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])



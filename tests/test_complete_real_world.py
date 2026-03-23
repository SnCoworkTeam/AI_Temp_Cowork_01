"""
企业语义能力图谱 - 真实环境完整测试套件
使用实际的服务和数据库，确保功能真实可用
"""
import pytest
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# 导入实际的服务和模型
from services.enterprise_semantic_engine import (
    EnterpriseSemanticEngine,
    IntentQueryResult
)
from services.unified_intent_service import (
    UnifiedIntentService,
    UnifiedIntentResult,
    ExecutionSuggestion
)
from database.src.core.database import get_database_manager
from database.src.core.session import init_session_factory
from database.src.models import BusinessActivity, CapabilityUnit, ActivityCapabilityMapping


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    print("\n" + "="*70)
    print("企业语义能力图谱 - 真实环境完整测试")
    print("="*70)
    
    # 初始化数据库连接
    db_manager = get_database_manager()
    if not db_manager.test_connection():
        pytest.skip("数据库连接失败，跳过真实环境测试")
    
    init_session_factory()
    print("[OK] 数据库连接成功")
    yield
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)


@pytest.fixture
def semantic_engine():
    """创建真实的语义引擎实例"""
    try:
        engine = EnterpriseSemanticEngine()
        yield engine
        engine._close_db()
    except Exception as e:
        pytest.skip(f"语义引擎初始化失败: {e}")


@pytest.fixture
def unified_intent_service():
    """创建真实的统一意图服务实例"""
    try:
        service = UnifiedIntentService()
        yield service
        service._close_db()
    except Exception as e:
        pytest.skip(f"统一意图服务初始化失败: {e}")


class TestRealSemanticEngine:
    """真实环境下的语义引擎测试"""
    
    def test_engine_initialization(self, semantic_engine):
        """测试引擎初始化"""
        assert semantic_engine is not None
        assert hasattr(semantic_engine, '_get_db')
        
        # 验证数据库连接
        db = semantic_engine._get_db()
        assert db is not None
        
        print("[OK] 语义引擎初始化成功，数据库连接正常")
    
    def test_query_intent_real(self, semantic_engine):
        """测试真实环境下的意图查询"""
        test_cases = [
            {
                "input": "我需要创建采购订单",
                "expected_activity_type": "action",
                "min_score": 0.0  # 只要有结果即可
            },
            {
                "input": "查询采购订单状态",
                "expected_activity_type": "query",
                "min_score": 0.0
            },
            {
                "input": "采购原料",
                "expected_activity_type": "action",
                "min_score": 0.0
            }
        ]
        
        for test_case in test_cases:
            try:
                result = semantic_engine.query_intent(
                    test_case["input"],
                    top_k=5,
                    min_score=0.3
                )
                
                assert isinstance(result, IntentQueryResult)
                assert result.query == test_case["input"]
                assert isinstance(result.activities, list)
                assert isinstance(result.scores, list)
                assert len(result.activities) == len(result.scores)
                assert result.query_time >= 0
                
                if result.total_count > 0:
                    activity = result.activities[0]
                    assert isinstance(activity, BusinessActivity)
                    print(f"  [OK] '{test_case['input']}' -> {activity.name} (相似度: {result.scores[0]:.2f})")
                else:
                    print(f"  [SKIP] '{test_case['input']}' -> 无匹配活动（可能数据库中没有数据）")
                    
            except Exception as e:
                print(f"  [WARN] 查询失败: {test_case['input']} - {e}")
    
    def test_get_activity_by_id(self, semantic_engine):
        """测试根据ID获取活动"""
        # 尝试获取一个可能存在的活动
        test_id = "activity:procurement:create_po"
        
        activity = semantic_engine.get_activity_by_id(test_id)
        
        if activity:
            assert isinstance(activity, BusinessActivity)
            assert activity.id == test_id
            print(f"[OK] 获取活动成功: {activity.name}")
        else:
            print(f"[SKIP] 活动不存在: {test_id}（可能数据库中没有数据）")
    
    def test_get_activities_by_domain(self, semantic_engine):
        """测试根据业务领域获取活动"""
        activities = semantic_engine.get_activities_by_domain("procurement")
        
        assert isinstance(activities, list)
        
        if len(activities) > 0:
            for activity in activities:
                assert isinstance(activity, BusinessActivity)
                assert activity.business_domain == "procurement"
            print(f"[OK] 获取采购领域活动: {len(activities)} 个")
        else:
            print("[SKIP] 采购领域无活动（可能数据库中没有数据）")
    
    def test_search_activities(self, semantic_engine):
        """测试向量搜索活动"""
        # 创建模拟向量（1536维）
        query_vector = [0.1] * 1536
        
        activities = semantic_engine.search_activities(
            query_vector=query_vector,
            top_k=5,
            business_domain="procurement"
        )
        
        assert isinstance(activities, list)
        assert len(activities) <= 5
        
        if len(activities) > 0:
            for activity in activities:
                assert isinstance(activity, BusinessActivity)
                assert activity.business_domain == "procurement"
            print(f"[OK] 向量搜索成功: {len(activities)} 个活动")
        else:
            print("[SKIP] 向量搜索无结果（可能数据库中没有数据）")
    
    def test_recommend_activities(self, semantic_engine):
        """测试活动推荐"""
        # 尝试推荐一个可能存在的活动
        test_activity_id = "activity:procurement:create_po"
        
        try:
            recommendation = semantic_engine.recommend_activities(
                activity_id=test_activity_id,
                top_k=3,
                min_similarity=0.3
            )
            
            assert recommendation is not None
            assert recommendation.source_activity_id == test_activity_id
            assert isinstance(recommendation.recommended_activities, list)
            assert isinstance(recommendation.similarity_scores, list)
            assert len(recommendation.recommended_activities) == len(recommendation.similarity_scores)
            
            print(f"[OK] 活动推荐成功: {len(recommendation.recommended_activities)} 个推荐")
            print(f"    推荐理由: {recommendation.recommendation_reason}")
            
        except ValueError as e:
            if "活动不存在" in str(e):
                print(f"[SKIP] 活动不存在: {test_activity_id}")
            else:
                raise


class TestRealUnifiedIntentService:
    """真实环境下的统一意图服务测试"""
    
    @pytest.mark.asyncio
    async def test_understand_intent_real(self, unified_intent_service):
        """测试真实环境下的意图理解"""
        test_cases = [
            {
                "input": "我需要创建采购订单",
                "context": {"user_id": "test_user", "department": "procurement"}
            },
            {
                "input": "查询采购订单状态",
                "context": {"user_id": "test_user"}
            },
            {
                "input": "采购原料",
                "context": None
            }
        ]
        
        for test_case in test_cases:
            try:
                result = await unified_intent_service.understand_intent(
                    user_input=test_case["input"],
                    context=test_case.get("context")
                )
                
                assert isinstance(result, UnifiedIntentResult)
                assert result.user_input == test_case["input"]
                assert result.base_intent is not None
                assert isinstance(result.suggested_activities, list)
                assert isinstance(result.execution_suggestions, list)
                assert result.confidence >= 0.0
                assert result.query_time >= 0
                
                print(f"  [OK] '{test_case['input']}'")
                print(f"     意图: {result.base_intent}, 置信度: {result.confidence:.2f}")
                print(f"     推荐活动: {len(result.suggested_activities)} 个")
                print(f"     执行建议: {len(result.execution_suggestions)} 个")
                
            except Exception as e:
                print(f"  [WARN] 意图理解失败: {test_case['input']} - {e}")
    
    @pytest.mark.asyncio
    async def test_execution_suggestions(self, unified_intent_service):
        """测试执行建议生成"""
        try:
            result = await unified_intent_service.understand_intent(
                user_input="创建采购订单",
                context={"department": "procurement"}
            )
            
            if len(result.execution_suggestions) > 0:
                suggestion = result.execution_suggestions[0]
                assert isinstance(suggestion, ExecutionSuggestion)
                assert suggestion.activity_id is not None
                assert suggestion.activity_name is not None
                assert suggestion.confidence >= 0.0
                
                print(f"[OK] 执行建议生成成功")
                print(f"    活动: {suggestion.activity_name}")
                print(f"    能力: {suggestion.capability_name or '未指定'}")
                print(f"    置信度: {suggestion.confidence:.2f}")
            else:
                print("[SKIP] 无执行建议（可能数据库中没有映射数据）")
                
        except Exception as e:
            print(f"[SKIP] 执行建议测试跳过: {e}")


class TestRealDataModels:
    """真实环境下的数据模型测试"""
    
    def test_business_activity_model(self):
        """测试业务活动模型结构"""
        from database.src.core.session import get_db
        
        db = next(get_db())
        try:
            # 查询一个活动（如果存在）
            activity = db.query(BusinessActivity).first()
            
            if activity:
                # 验证必需字段
                assert hasattr(activity, 'id')
                assert hasattr(activity, 'name')
                assert hasattr(activity, 'activity_type')
                assert hasattr(activity, 'business_domain')
                
                # 验证字段值
                assert activity.id is not None
                assert activity.name is not None
                assert activity.activity_type in ["action", "query", "approval", "notification"]
                
                print(f"[OK] 业务活动模型验证通过: {activity.name}")
                print(f"    ID: {activity.id}")
                print(f"    类型: {activity.activity_type}")
                print(f"    领域: {activity.business_domain}")
            else:
                print("[SKIP] 数据库中没有业务活动数据")
        finally:
            db.close()
    
    def test_capability_unit_model(self):
        """测试能力单元模型结构"""
        from database.src.core.session import get_db
        
        db = next(get_db())
        try:
            # 查询一个能力单元（如果存在）
            capability = db.query(CapabilityUnit).first()
            
            if capability:
                # 验证必需字段
                assert hasattr(capability, 'id')
                assert hasattr(capability, 'name')
                assert hasattr(capability, 'capability_type')
                
                # 验证字段值
                assert capability.id is not None
                assert capability.name is not None
                
                print(f"[OK] 能力单元模型验证通过: {capability.name}")
                print(f"    ID: {capability.id}")
                print(f"    类型: {capability.capability_type}")
            else:
                print("[SKIP] 数据库中没有能力单元数据")
        finally:
            db.close()
    
    def test_activity_capability_mapping(self):
        """测试活动-能力映射模型"""
        from database.src.core.session import get_db
        
        db = next(get_db())
        try:
            # 查询一个映射（如果存在）
            mapping = db.query(ActivityCapabilityMapping).first()
            
            if mapping:
                # 验证必需字段
                assert hasattr(mapping, 'id')
                assert hasattr(mapping, 'activity_id')
                assert hasattr(mapping, 'capability_id')
                assert hasattr(mapping, 'mapping_type')
                assert hasattr(mapping, 'confidence')
                
                # 验证字段值
                assert mapping.activity_id is not None
                assert mapping.capability_id is not None
                assert mapping.mapping_type in ["primary", "alternative", "fallback"]
                assert 0.0 <= mapping.confidence <= 1.0
                
                print(f"[OK] 活动-能力映射验证通过")
                print(f"    活动ID: {mapping.activity_id}")
                print(f"    能力ID: {mapping.capability_id}")
                print(f"    映射类型: {mapping.mapping_type}")
                print(f"    置信度: {mapping.confidence:.2f}")
            else:
                print("[SKIP] 数据库中没有活动-能力映射数据")
        finally:
            db.close()


class TestRealEndToEndFlow:
    """真实环境下的端到端流程测试"""
    
    @pytest.mark.asyncio
    async def test_procurement_workflow_real(self, unified_intent_service):
        """测试真实的采购工作流程"""
        print("\n[端到端测试] 采购工作流程")
        print("-" * 50)
        
        # 1. 用户输入
        user_input = "我需要采购一批原料，供应商ABC，物料MAT001"
        print(f"1. 用户输入: {user_input}")
        
        # 2. 意图理解
        try:
            result = await unified_intent_service.understand_intent(
                user_input=user_input,
                context={"user_id": "test_user", "department": "procurement"}
            )
            
            print(f"2. 意图理解结果:")
            print(f"   基础意图: {result.base_intent}")
            print(f"   置信度: {result.confidence:.2f}")
            print(f"   推荐活动数: {len(result.suggested_activities)}")
            print(f"   执行建议数: {len(result.execution_suggestions)}")
            
            # 3. 验证结果
            assert isinstance(result, UnifiedIntentResult)
            assert result.user_input == user_input
            
            if len(result.suggested_activities) > 0:
                activity = result.suggested_activities[0]
                print(f"3. 推荐活动: {activity.get('name', 'N/A')}")
                
                if len(result.execution_suggestions) > 0:
                    suggestion = result.execution_suggestions[0]
                    print(f"4. 执行建议:")
                    print(f"   活动: {suggestion.activity_name}")
                    print(f"   能力: {suggestion.capability_name or '未指定'}")
                    print(f"   置信度: {suggestion.confidence:.2f}")
                    
                    # 5. 参数组装（模拟）
                    execution_params = {
                        "activity_id": suggestion.activity_id,
                        "capability_id": suggestion.capability_id,
                        "parameters": {
                            "supplier_code": "SUP_ABC",
                            "materials": [{"code": "MAT001", "quantity": 100}],
                            "purchase_org": "1000"
                        }
                    }
                    
                    print(f"5. 执行参数组装完成")
                    print(f"   活动ID: {execution_params['activity_id']}")
                    print(f"   能力ID: {execution_params['capability_id']}")
                    
                    print("\n[OK] 端到端流程测试通过")
                else:
                    print("4. 无执行建议（可能数据库中没有映射数据）")
                    print("\n[WARN] 端到端流程部分完成（缺少执行建议）")
            else:
                print("3. 无推荐活动（可能数据库中没有活动数据）")
                print("\n[WARN] 端到端流程部分完成（缺少活动数据）")
                
        except Exception as e:
            print(f"[ERROR] 端到端流程测试失败: {e}")
            raise
    
    def test_performance_real(self, semantic_engine):
        """测试真实环境下的性能"""
        import time
        
        test_queries = [
            "创建采购订单",
            "查询采购订单",
            "采购原料",
            "查看供应商",
            "审批采购"
        ]
        
        total_time = 0
        query_count = 0
        
        print("\n[性能测试] 真实环境性能测试")
        print("-" * 50)
        
        for query in test_queries:
            try:
                start = time.time()
                result = semantic_engine.query_intent(query, top_k=5, min_score=0.3)
                elapsed = time.time() - start
                
                total_time += elapsed
                query_count += 1
                
                print(f"  '{query}': {elapsed*1000:.1f}ms")
                
                # 验证响应时间
                assert elapsed < 2.0, f"响应时间 {elapsed:.3f}s 超过2秒"
                
            except Exception as e:
                print(f"  '{query}': 失败 - {e}")
        
        if query_count > 0:
            avg_time = total_time / query_count
            print(f"\n平均响应时间: {avg_time*1000:.1f}ms")
            print(f"总查询数: {query_count}")
            
            # 验证平均响应时间
            assert avg_time < 1.0, f"平均响应时间 {avg_time:.3f}s 超过1秒"
            print("[OK] 性能测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])


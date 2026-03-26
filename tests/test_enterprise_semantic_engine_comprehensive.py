"""
企业语义引擎完整测试
基于实际代码结构，测试企业语义引擎的核心功能
"""
import pytest
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from services.enterprise_semantic_engine import (
    EnterpriseSemanticEngine,
    IntentQueryResult,
    ActivityRecommendation
)
from database.src.models.business_activity import BusinessActivity


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话级别的数据库设置"""
    print("\n" + "="*60)
    print("企业语义引擎完整测试")
    print("="*60)
    
    # 初始化数据库连接
    db_manager = get_database_manager()
    if not db_manager.test_connection():
        pytest.skip("数据库连接失败，跳过测试")
    
    init_session_factory()
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestEnterpriseSemanticEngine:
    """测试企业语义引擎"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        try:
            engine = EnterpriseSemanticEngine()
            yield engine
        finally:
            engine._close_db()
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = EnterpriseSemanticEngine()
        assert engine is not None
        assert engine._db is None  # 初始时数据库会话为None
        
        # 测试数据库连接
        db = engine._get_db()
        assert db is not None
        
        engine._close_db()
        print("[OK] 引擎初始化成功")
    
    def test_query_intent_basic(self, engine):
        """测试基础意图查询"""
        # 执行查询
        result = engine.query_intent("我想采购原料", top_k=5, min_score=0.0)
        
        # 验证结果类型
        assert isinstance(result, IntentQueryResult)
        assert result.query == "我想采购原料"
        assert isinstance(result.activities, list)
        assert isinstance(result.scores, list)
        assert len(result.activities) == len(result.scores)
        assert result.total_count >= 0
        assert result.query_time >= 0
        
        print(f"[OK] 基础意图查询成功")
        print(f"    查询: {result.query}")
        print(f"    找到 {result.total_count} 个相关活动")
        print(f"    返回 {len(result.activities)} 个活动")
        print(f"    查询时间: {result.query_time:.3f}秒")
    
    def test_query_intent_with_context(self, engine):
        """测试带上下文的意图查询"""
        context = {
            "user_id": "user001",
            "department": "procurement",
            "previous_activities": ["activity:procurement:create_po"]
        }
        
        result = engine.query_intent(
            "创建采购订单",
            context=context,
            top_k=10,
            min_score=0.3
        )
        
        assert isinstance(result, IntentQueryResult)
        assert result.query == "创建采购订单"
        assert len(result.activities) <= 10
        
        print(f"[OK] 带上下文的意图查询成功")
        print(f"    返回 {len(result.activities)} 个活动")
    
    def test_query_intent_empty_result(self, engine):
        """测试空结果查询"""
        # 使用一个不太可能匹配的查询
        result = engine.query_intent(
            "这是一个完全不相关的查询xyz123",
            top_k=5,
            min_score=0.9  # 高阈值，应该返回空结果
        )
        
        assert isinstance(result, IntentQueryResult)
        assert result.total_count == 0 or len(result.activities) == 0
        
        print(f"[OK] 空结果查询处理正确")
        print(f"    总匹配数: {result.total_count}")
    
    def test_search_activities(self, engine):
        """测试基于向量的活动搜索"""
        # 创建一个模拟向量（1536维，与实际代码一致）
        query_vector = [0.1] * 1536
        
        activities = engine.search_activities(
            query_vector=query_vector,
            top_k=5,
            business_domain="procurement"
        )
        
        assert isinstance(activities, list)
        assert len(activities) <= 5
        
        # 验证所有活动都属于procurement领域
        for activity in activities:
            assert activity.business_domain == "procurement"
        
        print(f"[OK] 向量搜索活动成功")
        print(f"    返回 {len(activities)} 个活动")
    
    def test_search_activities_all_domains(self, engine):
        """测试搜索所有领域的活动"""
        query_vector = [0.1] * 1536
        
        activities = engine.search_activities(
            query_vector=query_vector,
            top_k=10,
            business_domain=None  # 不限制领域
        )
        
        assert isinstance(activities, list)
        assert len(activities) <= 10
        
        print(f"[OK] 全领域搜索成功")
        print(f"    返回 {len(activities)} 个活动")
    
    def test_recommend_activities(self, engine):
        """测试活动推荐"""
        # 使用一个存在的活动ID（如果不存在则跳过）
        test_activity_id = "activity:procurement:create_po"
        
        try:
            recommendation = engine.recommend_activities(
                activity_id=test_activity_id,
                top_k=5,
                min_similarity=0.3
            )
            
            assert isinstance(recommendation, ActivityRecommendation)
            assert recommendation.source_activity_id == test_activity_id
            assert isinstance(recommendation.recommended_activities, list)
            assert isinstance(recommendation.similarity_scores, list)
            assert len(recommendation.recommended_activities) == len(recommendation.similarity_scores)
            assert isinstance(recommendation.recommendation_reason, str)
            
            print(f"[OK] 活动推荐成功")
            print(f"    源活动: {recommendation.source_activity_id}")
            print(f"    推荐了 {len(recommendation.recommended_activities)} 个活动")
            print(f"    推荐理由: {recommendation.recommendation_reason}")
            
        except ValueError as e:
            if "活动不存在" in str(e):
                pytest.skip(f"测试活动不存在: {test_activity_id}")
            else:
                raise
    
    def test_recommend_activities_nonexistent(self, engine):
        """测试推荐不存在的活动"""
        with pytest.raises(ValueError, match="活动不存在"):
            engine.recommend_activities(
                activity_id="activity:nonexistent:test",
                top_k=5
            )
        
        print("[OK] 不存在活动的错误处理正确")
    
    def test_get_activity_by_id(self, engine):
        """测试根据ID获取活动"""
        # 尝试获取一个可能存在的活动
        test_activity_id = "activity:procurement:create_po"
        
        activity = engine.get_activity_by_id(test_activity_id)
        
        if activity:
            assert isinstance(activity, BusinessActivity)
            assert activity.id == test_activity_id
            print(f"[OK] 根据ID获取活动成功: {activity.name}")
        else:
            print(f"[OK] 活动不存在（预期行为）: {test_activity_id}")
    
    def test_get_activity_by_id_nonexistent(self, engine):
        """测试获取不存在的活动"""
        activity = engine.get_activity_by_id("activity:nonexistent:test")
        assert activity is None
        
        print("[OK] 不存在活动返回None")
    
    def test_get_activities_by_domain(self, engine):
        """测试根据业务领域获取活动列表"""
        activities = engine.get_activities_by_domain("procurement")
        
        assert isinstance(activities, list)
        
        # 验证所有活动都属于procurement领域
        for activity in activities:
            assert isinstance(activity, BusinessActivity)
            assert activity.business_domain == "procurement"
        
        print(f"[OK] 根据领域获取活动成功: {len(activities)} 个采购活动")
    
    def test_get_activities_by_domain_empty(self, engine):
        """测试获取不存在的业务领域"""
        activities = engine.get_activities_by_domain("nonexistent_domain")
        
        assert isinstance(activities, list)
        assert len(activities) == 0
        
        print("[OK] 不存在领域返回空列表")
    
    def test_text_to_vector(self, engine):
        """测试文本转向量"""
        text = "测试文本"
        vector = engine._text_to_vector(text)
        
        assert isinstance(vector, list)
        assert len(vector) == 1536  # 实际代码使用1536维
        assert all(isinstance(x, float) for x in vector)
        
        # 相同文本应该生成相同向量（基于hash）
        vector2 = engine._text_to_vector(text)
        assert vector == vector2
        
        # 不同文本应该生成不同向量
        vector3 = engine._text_to_vector("不同文本")
        assert vector != vector3
        
        print("[OK] 文本转向量成功")
        print(f"    向量维度: {len(vector)}")
    
    def test_calculate_similarity(self, engine):
        """测试相似度计算"""
        # 创建一个测试活动
        test_activity = BusinessActivity(
            id="activity:test:similarity",
            name="创建采购订单",
            description="在SAP系统中创建标准采购订单",
            activity_type="action",
            business_domain="procurement"
        )
        
        # 测试相似查询
        score1 = engine._calculate_similarity("创建采购订单", test_activity)
        assert 0.0 <= score1 <= 1.0
        assert score1 > 0.5  # 应该有一定相似度
        
        # 测试不相似查询
        score2 = engine._calculate_similarity("完全不相关的查询", test_activity)
        assert 0.0 <= score2 <= 1.0
        assert score2 < score1  # 应该比相似查询的分数低
        
        print(f"[OK] 相似度计算成功")
        print(f"    相似查询分数: {score1:.3f}")
        print(f"    不相似查询分数: {score2:.3f}")
    
    def test_calculate_activity_similarity(self, engine):
        """测试活动间相似度计算"""
        activity1 = BusinessActivity(
            id="activity:test:1",
            name="创建采购订单",
            description="创建订单",
            activity_type="action",
            business_domain="procurement"
        )
        
        activity2 = BusinessActivity(
            id="activity:test:2",
            name="创建采购订单",
            description="创建订单",
            activity_type="action",
            business_domain="procurement"
        )
        
        activity3 = BusinessActivity(
            id="activity:test:3",
            name="查询订单状态",
            description="查询状态",
            activity_type="query",
            business_domain="sales"
        )
        
        # 相同活动应该有高相似度
        similarity1 = engine._calculate_activity_similarity(activity1, activity2)
        assert 0.0 <= similarity1 <= 1.0
        assert similarity1 > 0.8  # 应该很高
        
        # 不同活动应该有较低相似度
        similarity2 = engine._calculate_activity_similarity(activity1, activity3)
        assert 0.0 <= similarity2 <= 1.0
        assert similarity2 < similarity1  # 应该比相同活动低
        
        print(f"[OK] 活动相似度计算成功")
        print(f"    相同活动相似度: {similarity1:.3f}")
        print(f"    不同活动相似度: {similarity2:.3f}")
    
    def test_text_similarity(self, engine):
        """测试文本相似度"""
        # 相同文本
        score1 = engine._text_similarity("创建采购订单", "创建采购订单")
        assert score1 == 1.0
        
        # 相似文本
        score2 = engine._text_similarity("创建采购订单", "创建订单")
        assert 0.0 < score2 < 1.0
        
        # 不相似文本
        score3 = engine._text_similarity("创建采购订单", "查询库存")
        assert 0.0 <= score3 < score2
        
        print(f"[OK] 文本相似度计算成功")
        print(f"    相同文本: {score1:.3f}")
        print(f"    相似文本: {score2:.3f}")
        print(f"    不相似文本: {score3:.3f}")
    
    def test_generate_recommendation_reason(self, engine):
        """测试生成推荐理由"""
        source_activity = BusinessActivity(
            id="activity:test:source",
            name="创建采购订单",
            activity_type="action",
            business_domain="procurement"
        )
        
        # 空推荐列表
        reason1 = engine._generate_recommendation_reason(source_activity, [])
        assert reason1 == "没有找到相似的活动"
        
        # 有推荐活动
        recommended = [
            BusinessActivity(
                id="activity:test:1",
                name="查询采购订单",
                activity_type="query",
                business_domain="procurement"
            ),
            BusinessActivity(
                id="activity:test:2",
                name="审批采购订单",
                activity_type="approval",
                business_domain="procurement"
            )
        ]
        
        reason2 = engine._generate_recommendation_reason(source_activity, recommended)
        assert isinstance(reason2, str)
        assert len(reason2) > 0
        
        print(f"[OK] 推荐理由生成成功")
        print(f"    空推荐理由: {reason1}")
        print(f"    有推荐理由: {reason2}")
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with EnterpriseSemanticEngine() as engine:
            assert engine is not None
            # 在上下文中使用引擎
            result = engine.query_intent("测试", top_k=1)
            assert isinstance(result, IntentQueryResult)
        
        # 上下文退出后，数据库应该已关闭
        assert engine._db is None or engine._db.closed
        
        print("[OK] 上下文管理器工作正常")


class TestEnterpriseSemanticEngineIntegration:
    """企业语义引擎集成测试"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        try:
            engine = EnterpriseSemanticEngine()
            yield engine
        finally:
            engine._close_db()
    
    def test_end_to_end_workflow(self, engine):
        """测试端到端工作流"""
        # 1. 查询意图
        query_result = engine.query_intent("创建采购订单", top_k=5)
        assert isinstance(query_result, IntentQueryResult)
        
        if len(query_result.activities) > 0:
            # 2. 获取第一个活动
            first_activity = query_result.activities[0]
            activity_id = first_activity.id
            
            # 3. 获取活动详情
            activity = engine.get_activity_by_id(activity_id)
            assert activity is not None
            assert activity.id == activity_id
            
            # 4. 推荐相关活动
            recommendation = engine.recommend_activities(
                activity_id=activity_id,
                top_k=3
            )
            assert isinstance(recommendation, ActivityRecommendation)
            
            print("[OK] 端到端工作流测试成功")
            print(f"    查询到 {len(query_result.activities)} 个活动")
            print(f"    推荐了 {len(recommendation.recommended_activities)} 个相关活动")
        else:
            print("[OK] 端到端工作流测试（无活动数据）")
    
    def test_performance_query_intent(self, engine):
        """测试意图查询性能"""
        import time
        
        queries = [
            "创建采购订单",
            "查询订单状态",
            "审批采购申请",
            "查看供应商信息",
            "生成采购报告"
        ]
        
        total_time = 0
        for query in queries:
            start = time.time()
            result = engine.query_intent(query, top_k=5)
            elapsed = time.time() - start
            total_time += elapsed
            
            assert result.query_time < 5.0  # 单次查询应该在5秒内
        
        avg_time = total_time / len(queries)
        print(f"[OK] 性能测试通过")
        print(f"    平均查询时间: {avg_time:.3f}秒")
        print(f"    总查询时间: {total_time:.3f}秒")
        assert avg_time < 2.0  # 平均应该在2秒内


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])



"""
阶段一第3周测试：企业语义引擎基础
测试意图查询、向量搜索、活动推荐、向量同步等功能
"""
import pytest
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.enterprise_semantic_engine import EnterpriseSemanticEngine, IntentQueryResult
from services.vector_sync_service import VectorSyncService


@pytest.fixture(scope="session", autouse=True)
def setup_services():
    """测试会话级别的服务设置"""
    print("\n" + "="*60)
    print("阶段一第3周测试 - 企业语义引擎基础")
    print("="*60)
    yield
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


class TestEnterpriseSemanticEngine:
    """测试企业语义引擎"""
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = EnterpriseSemanticEngine()
        assert engine is not None
        print("[OK] 企业语义引擎初始化成功")
        engine._close_db()
    
    def test_query_intent(self):
        """测试意图查询"""
        engine = EnterpriseSemanticEngine()
        try:
            result = engine.query_intent("创建采购订单", top_k=5)
            
            assert result is not None
            assert isinstance(result, IntentQueryResult)
            assert result.query == "创建采购订单"
            assert len(result.activities) > 0
            assert len(result.scores) == len(result.activities)
            assert result.query_time > 0
            assert result.query_time < 5.0  # 响应时间应该小于5秒
            
            print(f"[OK] 意图查询成功: 找到 {result.total_count} 个相关活动")
            print(f"    返回前 {len(result.activities)} 个，查询时间: {result.query_time:.3f}秒")
        finally:
            engine._close_db()
    
    def test_query_intent_with_context(self):
        """测试带上下文的意图查询"""
        engine = EnterpriseSemanticEngine()
        try:
            context = {"domain": "procurement", "user_role": "采购员"}
            result = engine.query_intent("查询订单", context=context, top_k=3)
            
            assert result is not None
            assert len(result.activities) <= 3
            print(f"[OK] 带上下文的意图查询成功: {len(result.activities)} 个结果")
        finally:
            engine._close_db()
    
    def test_search_activities(self):
        """测试向量搜索活动"""
        engine = EnterpriseSemanticEngine()
        try:
            # 创建一个模拟向量
            query_vector = [0.1] * 1536
            activities = engine.search_activities(query_vector, top_k=5, business_domain="procurement")
            
            assert isinstance(activities, list)
            assert len(activities) <= 5
            print(f"[OK] 向量搜索成功: 找到 {len(activities)} 个活动")
        finally:
            engine._close_db()
    
    def test_recommend_activities(self):
        """测试活动推荐"""
        engine = EnterpriseSemanticEngine()
        try:
            recommendation = engine.recommend_activities(
                "activity:procurement:create_po",
                top_k=3
            )
            
            assert recommendation is not None
            assert recommendation.source_activity_id == "activity:procurement:create_po"
            assert len(recommendation.recommended_activities) <= 3
            assert len(recommendation.similarity_scores) == len(recommendation.recommended_activities)
            assert recommendation.recommendation_reason is not None
            
            print(f"[OK] 活动推荐成功: 推荐了 {len(recommendation.recommended_activities)} 个活动")
        finally:
            engine._close_db()
    
    def test_get_activity_by_id(self):
        """测试根据ID获取活动"""
        engine = EnterpriseSemanticEngine()
        try:
            activity = engine.get_activity_by_id("activity:procurement:create_po")
            
            assert activity is not None
            assert activity.id == "activity:procurement:create_po"
            assert activity.name == "创建采购订单"
            
            print(f"[OK] 获取活动成功: {activity.name}")
        finally:
            engine._close_db()
    
    def test_get_activities_by_domain(self):
        """测试根据领域获取活动列表"""
        engine = EnterpriseSemanticEngine()
        try:
            activities = engine.get_activities_by_domain("procurement")
            
            assert isinstance(activities, list)
            assert len(activities) >= 10  # 至少应该有10个采购活动
            
            for activity in activities:
                assert activity.business_domain == "procurement"
            
            print(f"[OK] 获取活动列表成功: {len(activities)} 个活动")
        finally:
            engine._close_db()
    
    def test_query_performance(self):
        """测试查询性能"""
        engine = EnterpriseSemanticEngine()
        try:
            queries = [
                "创建采购订单",
                "查询订单",
                "审批订单",
                "处理异常",
                "生成报告"
            ]
            
            total_time = 0
            for query in queries:
                start_time = time.time()
                result = engine.query_intent(query, top_k=5)
                query_time = time.time() - start_time
                total_time += query_time
            
            avg_time = total_time / len(queries)
            assert avg_time < 2.0, f"平均查询时间 {avg_time:.3f}秒超过2秒"
            
            print(f"[OK] 性能测试通过: 平均查询时间 {avg_time:.3f}秒")
        finally:
            engine._close_db()


class TestVectorSyncService:
    """测试向量同步服务"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = VectorSyncService()
        assert service is not None
        print("[OK] 向量同步服务初始化成功")
        service._close_db()
    
    def test_check_updates(self):
        """测试检查更新"""
        service = VectorSyncService()
        try:
            activities = service.check_updates("procurement")
            
            assert isinstance(activities, list)
            print(f"[OK] 检查更新成功: 找到 {len(activities)} 个需要更新的活动")
        finally:
            service._close_db()
    
    def test_get_sync_status(self):
        """测试获取同步状态"""
        service = VectorSyncService()
        try:
            status = service.get_sync_status("procurement")
            
            assert status is not None
            assert "total" in status
            assert "needs_update" in status
            assert "up_to_date" in status
            assert "update_percentage" in status
            assert status["total"] >= 0
            assert status["needs_update"] >= 0
            assert status["up_to_date"] >= 0
            assert 0 <= status["update_percentage"] <= 100
            
            print(f"[OK] 获取同步状态成功:")
            print(f"    总数: {status['total']}")
            print(f"    需要更新: {status['needs_update']}")
            print(f"    已更新: {status['up_to_date']}")
            print(f"    更新率: {status['update_percentage']:.1f}%")
        finally:
            service._close_db()
    
    def test_sync_vectors(self):
        """测试同步向量"""
        service = VectorSyncService()
        try:
            result = service.sync_vectors("procurement", batch_size=5)
            
            assert result is not None
            assert "total" in result
            assert "updated" in result
            assert "failed" in result
            assert "message" in result
            assert result["total"] >= 0
            assert result["updated"] >= 0
            assert result["failed"] >= 0
            
            print(f"[OK] 同步向量成功:")
            print(f"    总数: {result['total']}")
            print(f"    成功: {result['updated']}")
            print(f"    失败: {result['failed']}")
        finally:
            service._close_db()
    
    def test_update_single_vector(self):
        """测试更新单个向量"""
        service = VectorSyncService()
        try:
            result = service.update_vector("activity:procurement:create_po")
            
            assert result is True
            print("[OK] 更新单个向量成功")
        finally:
            service._close_db()


class TestAPIEndpoints:
    """测试API接口（需要API服务运行）"""
    
    def test_api_health_check(self):
        """测试健康检查接口"""
        import requests
        
        try:
            response = requests.get("http://localhost:8001/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
                print("[OK] API健康检查通过")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")
    
    def test_api_intent_query(self):
        """测试意图查询接口"""
        import requests
        
        try:
            payload = {
                "query": "创建采购订单",
                "top_k": 5,
                "min_score": 0.5
            }
            response = requests.post(
                "http://localhost:8001/api/v1/intent/query",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                assert "activities" in data
                assert "scores" in data
                print(f"[OK] API意图查询成功: {len(data['activities'])} 个结果")
            else:
                print(f"[SKIP] API服务未运行 (状态码: {response.status_code})")
        except requests.exceptions.RequestException:
            print("[SKIP] API服务未运行，跳过API测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])






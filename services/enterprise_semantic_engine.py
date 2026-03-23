"""
企业语义引擎服务
提供意图查询、向量搜索、活动推荐等核心功能
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import hashlib
from dataclasses import dataclass

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.src.core.session import get_db, init_session_factory
from database.src.core.database import get_database_manager
from database.src.models import (
    BusinessActivity,
    CapabilityUnit,
    ActivityCapabilityMapping
)

# EA相关导入
try:
    from metadata_service.src.services.ea_vectorization_service import EAVectorizationService
    from metadata_service.src.services.ea_knowledge_graph import EAKnowledgeGraph
    from metadata_service.src.services.ea_hybrid_query import EAHybridQuery
    from database.src.models.enterprise_architecture_models import (
        BusinessProcess, ApplicationSystem, DataEntity
    )
    EA_SERVICES_AVAILABLE = True
except ImportError as e:
    EA_SERVICES_AVAILABLE = False
    logger.warning(f"EA服务未找到，EA增强功能将不可用: {e}")


@dataclass
class IntentQueryResult:
    """意图查询结果"""
    query: str
    activities: List[BusinessActivity]
    scores: List[float]
    total_count: int
    query_time: float


@dataclass
class ActivityRecommendation:
    """活动推荐结果"""
    source_activity_id: str
    recommended_activities: List[BusinessActivity]
    similarity_scores: List[float]
    recommendation_reason: str


class EnterpriseSemanticEngine:
    """企业语义引擎"""
    
    def __init__(self):
        """初始化企业语义引擎"""
        # 初始化数据库连接
        db_manager = get_database_manager()
        if not db_manager.test_connection():
            raise RuntimeError("数据库连接失败")
        
        init_session_factory()
        self._db = None
        
        # EA服务初始化（如果可用）
        self.ea_vector_service = None
        self.ea_graph_service = None
        self.ea_hybrid_query = None
        if EA_SERVICES_AVAILABLE:
            try:
                db = self._get_db()
                self.ea_vector_service = EAVectorizationService(db)
                self.ea_graph_service = EAKnowledgeGraph(db)
                self.ea_hybrid_query = EAHybridQuery(db, self.ea_graph_service, self.ea_vector_service)
                logger.info("EA服务初始化成功")
            except Exception as e:
                logger.warning(f"EA服务初始化失败: {e}，EA增强功能将不可用")
    
    def _get_db(self):
        """获取数据库会话"""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    def _close_db(self):
        """关闭数据库会话"""
        if self._db:
            self._db.close()
            self._db = None
    
    def query_intent(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> IntentQueryResult:
        """
        查询意图，返回相关业务活动
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息
            top_k: 返回前k个结果
            min_score: 最小相似度分数
        
        Returns:
            IntentQueryResult: 查询结果
        """
        import time
        start_time = time.time()
        
        try:
            db = self._get_db()
            
            # 1. 向量化用户输入（这里使用简单的文本匹配，实际应该使用向量）
            # TODO: 集成真实的向量化服务
            query_vector = self._text_to_vector(user_input)
            
            # 2. 在数据库中搜索相似活动
            activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == "procurement"
            ).all()
            
            # 3. 计算相似度（这里使用简单的文本匹配，实际应该使用向量相似度）
            scored_activities = []
            for activity in activities:
                score = self._calculate_similarity(user_input, activity)
                if score >= min_score:
                    scored_activities.append((activity, score))
            
            # 4. 按分数排序
            scored_activities.sort(key=lambda x: x[1], reverse=True)
            
            # 5. 取前k个
            top_activities = scored_activities[:top_k]
            
            activities_list = [act for act, _ in top_activities]
            scores_list = [score for _, score in top_activities]
            
            query_time = time.time() - start_time
            
            return IntentQueryResult(
                query=user_input,
                activities=activities_list,
                scores=scores_list,
                total_count=len(scored_activities),
                query_time=query_time
            )
        
        except Exception as e:
            raise RuntimeError(f"意图查询失败: {e}")
    
    def search_activities(
        self,
        query_vector: List[float],
        top_k: int = 10,
        business_domain: Optional[str] = None
    ) -> List[BusinessActivity]:
        """
        基于向量搜索业务活动
        
        Args:
            query_vector: 查询向量
            top_k: 返回前k个结果
            business_domain: 业务领域过滤
        
        Returns:
            List[BusinessActivity]: 相关业务活动列表
        """
        try:
            db = self._get_db()
            
            # 查询活动
            query = db.query(BusinessActivity)
            if business_domain:
                query = query.filter(BusinessActivity.business_domain == business_domain)
            
            activities = query.all()
            
            # TODO: 使用真实的向量相似度计算
            # 这里暂时返回所有活动
            return activities[:top_k]
        
        except Exception as e:
            raise RuntimeError(f"向量搜索失败: {e}")
    
    def recommend_activities(
        self,
        activity_id: str,
        top_k: int = 5,
        min_similarity: float = 0.6
    ) -> ActivityRecommendation:
        """
        推荐相关业务活动
        
        Args:
            activity_id: 源活动ID
            top_k: 返回前k个推荐
            min_similarity: 最小相似度
        
        Returns:
            ActivityRecommendation: 推荐结果
        """
        try:
            db = self._get_db()
            
            # 1. 获取源活动
            source_activity = db.query(BusinessActivity).filter_by(id=activity_id).first()
            if not source_activity:
                raise ValueError(f"活动不存在: {activity_id}")
            
            # 2. 获取同领域的其他活动
            other_activities = db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == source_activity.business_domain,
                BusinessActivity.id != activity_id
            ).all()
            
            # 3. 计算相似度
            scored_activities = []
            for activity in other_activities:
                similarity = self._calculate_activity_similarity(source_activity, activity)
                if similarity >= min_similarity:
                    scored_activities.append((activity, similarity))
            
            # 4. 按相似度排序
            scored_activities.sort(key=lambda x: x[1], reverse=True)
            
            # 5. 取前k个
            top_recommendations = scored_activities[:top_k]
            
            recommended_activities = [act for act, _ in top_recommendations]
            similarity_scores = [score for _, score in top_recommendations]
            
            # 6. 生成推荐理由
            reason = self._generate_recommendation_reason(source_activity, recommended_activities)
            
            return ActivityRecommendation(
                source_activity_id=activity_id,
                recommended_activities=recommended_activities,
                similarity_scores=similarity_scores,
                recommendation_reason=reason
            )
        
        except Exception as e:
            raise RuntimeError(f"活动推荐失败: {e}")
    
    def get_activity_by_id(self, activity_id: str) -> Optional[BusinessActivity]:
        """根据ID获取业务活动"""
        try:
            db = self._get_db()
            return db.query(BusinessActivity).filter_by(id=activity_id).first()
        except Exception as e:
            raise RuntimeError(f"获取活动失败: {e}")
    
    def get_activities_by_domain(self, domain: str) -> List[BusinessActivity]:
        """根据业务领域获取活动列表"""
        try:
            db = self._get_db()
            return db.query(BusinessActivity).filter(
                BusinessActivity.business_domain == domain
            ).all()
        except Exception as e:
            raise RuntimeError(f"获取活动列表失败: {e}")
    
    def _text_to_vector(self, text: str) -> List[float]:
        """将文本转换为向量（模拟实现）"""
        # TODO: 集成真实的向量化服务
        # 这里返回一个模拟向量
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        return [random.gauss(0, 0.1) for _ in range(1536)]
    
    def _calculate_similarity(self, query: str, activity: BusinessActivity) -> float:
        """计算查询文本与活动的相似度（简单实现）"""
        query_lower = query.lower()
        activity_text = f"{activity.name} {activity.description or ''}".lower()
        
        # 简单的关键词匹配
        query_words = set(query_lower.split())
        activity_words = set(activity_text.split())
        
        if not query_words:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = len(query_words & activity_words)
        union = len(query_words | activity_words)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _calculate_activity_similarity(
        self,
        activity1: BusinessActivity,
        activity2: BusinessActivity
    ) -> float:
        """计算两个活动的相似度"""
        # 基于活动类型和业务领域
        similarity = 0.0
        
        # 活动类型相同
        if activity1.activity_type == activity2.activity_type:
            similarity += 0.3
        
        # 业务领域相同
        if activity1.business_domain == activity2.business_domain:
            similarity += 0.3
        
        # 名称相似度
        name_similarity = self._text_similarity(activity1.name, activity2.name)
        similarity += name_similarity * 0.4
        
        return min(similarity, 1.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_recommendation_reason(
        self,
        source_activity: BusinessActivity,
        recommended_activities: List[BusinessActivity]
    ) -> str:
        """生成推荐理由"""
        if not recommended_activities:
            return "没有找到相似的活动"
        
        reasons = []
        for activity in recommended_activities[:3]:
            if activity.activity_type == source_activity.activity_type:
                reasons.append(f"同类型活动: {activity.name}")
            elif activity.business_domain == source_activity.business_domain:
                reasons.append(f"同领域活动: {activity.name}")
        
        if reasons:
            return "；".join(reasons)
        else:
            return f"基于相似度推荐了 {len(recommended_activities)} 个活动"
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._close_db()
    
    # ========== EA增强查询方法 ==========
    
    def query_business_processes(
        self,
        user_input: str,
        top_k: int = 10
    ) -> List[BusinessProcess]:
        """
        查询相关业务流程
        
        Args:
            user_input: 用户输入
            top_k: 返回前k个结果
            
        Returns:
            List[BusinessProcess]: 相关业务流程列表
        """
        if not EA_SERVICES_AVAILABLE or not self.ea_hybrid_query:
            logger.warning("EA服务不可用，返回空结果")
            return []
        
        try:
            db = self._get_db()
            # 使用混合查询引擎查询业务流程（异步调用）
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中，使用run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.ea_hybrid_query.query(
                            user_input=user_input,
                            query_type="hybrid",
                            entity_type="BusinessProcess",
                            top_k=top_k
                        ))
                    )
                    results = future.result()
            else:
                results = loop.run_until_complete(
                    self.ea_hybrid_query.query(
                        user_input=user_input,
                        query_type="hybrid",
                        entity_type="BusinessProcess",
                        top_k=top_k
                    )
                )
            
            # 从向量结果中提取实体ID
            entity_ids = []
            for result in results.get("vector_results", []):
                entity_id = result.get("entity_id")
                if entity_id:
                    entity_ids.append(entity_id)
            
            # 从数据库加载业务流程对象
            if entity_ids:
                processes = db.query(BusinessProcess).filter(
                    BusinessProcess.id.in_(entity_ids)
                ).all()
                return processes
            
            return []
        except Exception as e:
            logger.error(f"查询业务流程失败: {e}")
            return []
    
    def query_applications_and_entities(
        self,
        user_input: str,
        top_k: int = 10
    ) -> Dict[str, List]:
        """
        查询相关应用系统和数据实体
        
        Args:
            user_input: 用户输入
            top_k: 返回前k个结果
            
        Returns:
            Dict: {"applications": [...], "entities": [...]}
        """
        if not EA_SERVICES_AVAILABLE or not self.ea_hybrid_query:
            logger.warning("EA服务不可用，返回空结果")
            return {"applications": [], "entities": []}
        
        try:
            db = self._get_db()
            
            # 查询应用系统（异步调用）
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.ea_hybrid_query.query(
                            user_input=user_input,
                            query_type="hybrid",
                            entity_type="ApplicationSystem",
                            top_k=top_k
                        ))
                    )
                    app_results = future.result()
            else:
                app_results = loop.run_until_complete(
                    self.ea_hybrid_query.query(
                        user_input=user_input,
                        query_type="hybrid",
                        entity_type="ApplicationSystem",
                        top_k=top_k
                    )
                )
            
            app_ids = [r.get("entity_id") for r in app_results.get("vector_results", []) if r.get("entity_id")]
            applications = []
            if app_ids:
                applications = db.query(ApplicationSystem).filter(
                    ApplicationSystem.id.in_(app_ids)
                ).all()
            
            # 查询数据实体（异步调用）
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.ea_hybrid_query.query(
                            user_input=user_input,
                            query_type="hybrid",
                            entity_type="DataEntity",
                            top_k=top_k
                        ))
                    )
                    entity_results = future.result()
            else:
                entity_results = loop.run_until_complete(
                    self.ea_hybrid_query.query(
                        user_input=user_input,
                        query_type="hybrid",
                        entity_type="DataEntity",
                        top_k=top_k
                    )
                )
            
            entity_ids = [r.get("entity_id") for r in entity_results.get("vector_results", []) if r.get("entity_id")]
            entities = []
            if entity_ids:
                entities = db.query(DataEntity).filter(
                    DataEntity.id.in_(entity_ids)
                ).all()
            
            return {
                "applications": applications,
                "entities": entities
            }
        except Exception as e:
            logger.error(f"查询应用系统和数据实体失败: {e}")
            return {"applications": [], "entities": []}
    
    def query_ea_with_relationships(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        查询EA实体及其关系（使用图谱）
        
        Args:
            entity_id: 实体ID
            relation_types: 关系类型列表
            
        Returns:
            Dict: 包含实体信息和相关实体的字典
        """
        if not EA_SERVICES_AVAILABLE or not self.ea_graph_service:
            logger.warning("EA图谱服务不可用，返回空结果")
            return {"entity": None, "relationships": {}}
        
        try:
            # 查询相关实体（异步调用）
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.ea_graph_service.query_related_entities(
                            entity_id=entity_id,
                            relation_types=relation_types,
                            max_depth=2
                        ))
                    )
                    related_entities = future.result()
            else:
                related_entities = loop.run_until_complete(
                    self.ea_graph_service.query_related_entities(
                        entity_id=entity_id,
                        relation_types=relation_types,
                        max_depth=2
                    )
                )
            
            # 获取所有关系（同步方法）
            all_relationships = self.ea_graph_service.get_entity_relationships(entity_id)
            
            return {
                "entity_id": entity_id,
                "related_entities": related_entities,
                "relationships": all_relationships
            }
        except Exception as e:
            logger.error(f"查询EA实体关系失败: {e}")
            return {"entity_id": entity_id, "related_entities": [], "relationships": {}}


def main():
    """测试函数"""
    print("=" * 60)
    print("企业语义引擎测试")
    print("=" * 60)
    print()
    
    try:
        engine = EnterpriseSemanticEngine()
        
        # 测试1: 意图查询
        print("[TEST] 测试意图查询...")
        result = engine.query_intent("创建采购订单", top_k=5)
        print(f"  查询: {result.query}")
        print(f"  找到 {result.total_count} 个相关活动")
        print(f"  返回前 {len(result.activities)} 个:")
        for i, (activity, score) in enumerate(zip(result.activities, result.scores), 1):
            print(f"    {i}. {activity.name} (相似度: {score:.2f})")
        print(f"  查询时间: {result.query_time:.3f}秒")
        print()
        
        # 测试2: 活动推荐
        print("[TEST] 测试活动推荐...")
        recommendation = engine.recommend_activities(
            "activity:procurement:create_po",
            top_k=3
        )
        print(f"  源活动: {recommendation.source_activity_id}")
        print(f"  推荐了 {len(recommendation.recommended_activities)} 个活动:")
        for i, (activity, score) in enumerate(
            zip(recommendation.recommended_activities, recommendation.similarity_scores),
            1
        ):
            print(f"    {i}. {activity.name} (相似度: {score:.2f})")
        print(f"  推荐理由: {recommendation.recommendation_reason}")
        print()
        
        # 测试3: 获取活动列表
        print("[TEST] 测试获取活动列表...")
        activities = engine.get_activities_by_domain("procurement")
        print(f"  采购领域共有 {len(activities)} 个活动")
        print()
        
        print("=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())


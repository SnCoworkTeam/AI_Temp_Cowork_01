"""
语义引擎适配器
处理现有接口与新需求的适配
支持流式查询（阶段2）
"""
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime

from services.enterprise_semantic_engine import EnterpriseSemanticEngine, IntentQueryResult

logger = logging.getLogger(__name__)


class SemanticEngineAdapter:
    """
    语义引擎适配器
    处理现有接口与新需求的适配
    """
    
    def __init__(self, semantic_engine: EnterpriseSemanticEngine):
        self.semantic_engine = semantic_engine
    
    async def query_intent_enhanced(
        self,
        user_input: str,
        llm_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> IntentQueryResult:
        """
        增强的意图查询（适配现有接口）
        
        Args:
            user_input: 原始用户输入
            llm_result: LLM分析结果
            context: 上下文信息
            top_k: 返回前k个结果
            min_score: 最小相似度
        
        Returns:
            IntentQueryResult: 查询结果
        """
        # 1. 构建增强的查询（使用LLM生成的关键词）
        enhanced_query = self._build_enhanced_query(user_input, llm_result)
        
        # 2. 调用现有接口（保持兼容）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.semantic_engine.query_intent,
            enhanced_query,  # 使用增强的查询
            context,
            top_k,
            min_score
        )
        
        # 3. 业务领域过滤（如果LLM识别了业务领域）
        business_domain = llm_result.get("business_domain")
        if business_domain and result.activities:
            filtered_activities = []
            filtered_scores = []
            
            for activity, score in zip(result.activities, result.scores):
                if activity.business_domain == business_domain:
                    filtered_activities.append(activity)
                    filtered_scores.append(score)
            
            # 如果过滤后还有结果，使用过滤后的
            if filtered_activities:
                result.activities = filtered_activities[:top_k]
                result.scores = filtered_scores[:top_k]
                result.total_count = len(filtered_activities)
                logger.debug(f"业务领域过滤: {business_domain}，保留{len(filtered_activities)}个活动")
        
        return result
    
    async def query_intent_enhanced_stream(
        self,
        user_input: str,
        llm_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        增强的意图查询（流式版本）- 阶段2
        
        Args:
            user_input: 原始用户输入
            llm_result: LLM分析结果
            context: 上下文信息
            top_k: 返回前k个结果
            min_score: 最小相似度
        
        Yields:
            流式查询结果
        """
        try:
            # 1. 构建增强的查询
            yield {
                "stage": "preparing",
                "status": "preparing",
                "progress": 5,
                "message": "正在准备查询...",
                "timestamp": datetime.now().isoformat()
            }
            
            enhanced_query = self._build_enhanced_query(user_input, llm_result)
            
            # 2. 向量化（流式返回进度）
            yield {
                "stage": "vectorizing",
                "status": "processing",
                "progress": 10,
                "message": "正在向量化查询...",
                "timestamp": datetime.now().isoformat()
            }
            
            # 模拟向量化过程（实际应该调用向量化服务）
            await asyncio.sleep(0.1)  # 模拟处理时间
            
            yield {
                "stage": "vectorized",
                "status": "complete",
                "progress": 30,
                "message": "向量化完成",
                "timestamp": datetime.now().isoformat()
            }
            
            # 3. 搜索（流式返回进度）
            yield {
                "stage": "searching",
                "status": "processing",
                "progress": 40,
                "message": "正在搜索相关活动...",
                "timestamp": datetime.now().isoformat()
            }
            
            # 调用现有接口（在线程池中执行，避免阻塞）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.semantic_engine.query_intent,
                enhanced_query,
                context,
                top_k,
                min_score
            )
            
            # 4. 业务领域过滤（如果LLM识别了业务领域）
            business_domain = llm_result.get("business_domain")
            if business_domain and result.activities:
                yield {
                    "stage": "filtering",
                    "status": "processing",
                    "progress": 70,
                    "message": f"正在按业务领域过滤: {business_domain}...",
                    "timestamp": datetime.now().isoformat()
                }
                
                filtered_activities = []
                filtered_scores = []
                
                for activity, score in zip(result.activities, result.scores):
                    if activity.business_domain == business_domain:
                        filtered_activities.append(activity)
                        filtered_scores.append(score)
                
                # 如果过滤后还有结果，使用过滤后的
                if filtered_activities:
                    result.activities = filtered_activities[:top_k]
                    result.scores = filtered_scores[:top_k]
                    result.total_count = len(filtered_activities)
                    logger.debug(f"业务领域过滤: {business_domain}，保留{len(filtered_activities)}个活动")
            
            # 5. 分批返回结果（流式）
            if result.activities:
                yield {
                    "stage": "results",
                    "status": "processing",
                    "progress": 85,
                    "message": f"找到 {len(result.activities)} 个相关活动",
                    "activities_count": len(result.activities),
                    "timestamp": datetime.now().isoformat()
                }
                
                # 可以分批返回活动详情
                batch_size = 3
                for i in range(0, len(result.activities), batch_size):
                    batch = result.activities[i:i+batch_size]
                    batch_scores = result.scores[i:i+batch_size]
                    
                    yield {
                        "stage": "results",
                        "status": "processing",
                        "progress": 85 + (i / len(result.activities)) * 10,
                        "activities_batch": [
                            {
                                "id": act.id,
                                "name": act.name,
                                "description": act.description,
                                "similarity_score": score
                            }
                            for act, score in zip(batch, batch_scores)
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 6. 完成
            yield {
                "stage": "complete",
                "status": "success",
                "progress": 100,
                "result": result,
                "message": "语义引擎查询完成",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"语义引擎流式查询失败: {e}", exc_info=True)
            yield {
                "stage": "error",
                "status": "error",
                "error": str(e),
                "message": "语义引擎查询失败",
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_enhanced_query(
        self,
        user_input: str,
        llm_result: Dict[str, Any]
    ) -> str:
        """构建增强的查询字符串"""
        query_keywords = llm_result.get("query_keywords", [])
        
        if query_keywords:
            # 使用LLM生成的关键词
            enhanced_query = " ".join(query_keywords)
            logger.debug(f"使用LLM生成的关键词: {enhanced_query}")
            return enhanced_query
        else:
            # 使用原始输入
            return user_input

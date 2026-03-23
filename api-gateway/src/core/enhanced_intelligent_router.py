"""
增强的智能路由器
集成企业语义引擎，提供基于图谱的意图增强
"""
import logging
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .intelligent_router import IntelligentRouter, RouteIntent, IntentAnalysis

# 导入企业语义引擎
import logging
import re

logger = logging.getLogger(__name__)

try:
    from services.enterprise_semantic_engine import EnterpriseSemanticEngine, IntentQueryResult
    SEMANTIC_ENGINE_AVAILABLE = True
except ImportError:
    SEMANTIC_ENGINE_AVAILABLE = False
    logger.warning("企业语义引擎不可用，将使用基础路由")


@dataclass
class EnhancedIntentAnalysis:
    """增强的意图分析结果"""
    base_intent: IntentAnalysis
    suggested_activities: List[Dict[str, Any]]
    related_entities: List[Dict[str, Any]]
    available_capabilities: List[Dict[str, Any]]
    confidence: float
    fallback_mode: bool = False
    query_time: float = 0.0


class EnhancedIntelligentRouter(IntelligentRouter):
    """增强的智能路由器（集成企业语义引擎）"""
    
    def __init__(self):
        """初始化增强的路由器"""
        super().__init__()
        
        # 初始化企业语义引擎
        self.semantic_engine = None
        if SEMANTIC_ENGINE_AVAILABLE:
            try:
                self.semantic_engine = EnterpriseSemanticEngine()
                logger.info("企业语义引擎已集成")
            except Exception as e:
                logger.warning(f"企业语义引擎初始化失败: {e}")
                self.semantic_engine = None
        
        # 缓存配置
        self.cache_enabled = os.getenv("INTENT_CACHE_ENABLED", "true").lower() == "true"
        self.cache = {}  # 简单的内存缓存
        self.cache_ttl = 3600  # 缓存TTL（秒）
        
        # 超时配置
        self.timeout = float(os.getenv("INTENT_QUERY_TIMEOUT", "2.0"))
    
    def _generate_cache_key(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{user_input}:{str(context)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[EnhancedIntentAnalysis]:
        """从缓存获取结果"""
        if not self.cache_enabled:
            return None
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            # 检查是否过期
            if datetime.now() - cached_item["timestamp"] < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for key: {cache_key[:20]}...")
                return cached_item["result"]
            else:
                # 过期，删除
                del self.cache[cache_key]
        
        return None
    
    def _set_to_cache(self, cache_key: str, result: EnhancedIntentAnalysis):
        """设置缓存"""
        if not self.cache_enabled:
            return
        
        self.cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now()
        }
        
        # 限制缓存大小（简单策略：保留最近1000个）
        if len(self.cache) > 1000:
            # 删除最旧的
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
    
    async def analyze_intent_with_graph(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedIntentAnalysis:
        """
        基于图谱的意图分析（增强版）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
        
        Returns:
            EnhancedIntentAnalysis: 增强的意图分析结果
        """
        import time
        start_time = time.time()
        
        # 1. 检查缓存
        cache_key = self._generate_cache_key(user_input, context)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for intent query: {user_input[:50]}...")
            return cached_result
        
        try:
            # 2. 基础意图识别（使用父类方法）
            base_intent = await self._analyze_intent_base(user_input, context)
            
            # 3. 查询企业语义引擎（如果可用）
            graph_results = None
            if self.semantic_engine:
                try:
                    # 使用超时控制
                    graph_results = await asyncio.wait_for(
                        self._query_semantic_engine(user_input, context),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"语义引擎查询超时: {user_input[:50]}...")
                    graph_results = None
                except Exception as e:
                    logger.error(f"语义引擎查询失败: {e}")
                    graph_results = None
            
            # 4. 合并结果
            if graph_results:
                enhanced_intent = self._merge_intent_results(base_intent, graph_results)
            else:
                # 降级到快速模式
                enhanced_intent = self._fast_analysis(base_intent, user_input, context)
            
            enhanced_intent.query_time = time.time() - start_time
            
            # 5. 缓存结果
            self._set_to_cache(cache_key, enhanced_intent)
            
            return enhanced_intent
        
        except Exception as e:
            logger.error(f"意图分析失败: {e}")
            # 返回基础意图分析
            base_intent = await self._analyze_intent_base(user_input, context)
            return self._fast_analysis(base_intent, user_input, context)
    
    async def _analyze_intent_base(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentAnalysis:
        """基础意图分析（使用规则匹配）"""
        # 使用关键词匹配
        user_lower = user_input.lower()
        
        # 检查各种意图类型
        if any(re.search(pattern, user_lower) for pattern in [
            r"执行|调用|运行|使用.*工具",
            r"tool|execute|run|call.*api"
        ]):
            return IntentAnalysis(
                intent=RouteIntent.TOOL_EXECUTION,
                confidence=0.7,
                requires_tools=True,
                reasoning="检测到工具执行意图"
            )
        elif any(re.search(pattern, user_lower) for pattern in [
            r"工作流|流程|workflow",
            r"创建.*流程|设计.*工作流"
        ]):
            return IntentAnalysis(
                intent=RouteIntent.WORKFLOW_TASK,
                confidence=0.7,
                is_workflow_task=True,
                reasoning="检测到工作流任务意图"
            )
        elif any(re.search(pattern, user_lower) for pattern in [
            r"搜索|查找|查询.*知识",
            r"search|find|knowledge"
        ]):
            return IntentAnalysis(
                intent=RouteIntent.KNOWLEDGE_SEARCH,
                confidence=0.7,
                needs_knowledge_search=True,
                reasoning="检测到知识搜索意图"
            )
        else:
            return IntentAnalysis(
                intent=RouteIntent.SIMPLE_CHAT,
                confidence=0.5,
                is_simple_chat=True,
                reasoning="默认简单对话意图"
            )
    
    async def _query_semantic_engine(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[IntentQueryResult]:
        """查询企业语义引擎"""
        if not self.semantic_engine:
            return None
        
        try:
            # 在线程池中运行同步方法
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.semantic_engine.query_intent,
                user_input,
                context,
                10,  # top_k
                0.5  # min_score
            )
            return result
        except Exception as e:
            logger.error(f"查询语义引擎失败: {e}")
            return None
    
    def _merge_intent_results(
        self,
        base_intent: IntentAnalysis,
        graph_results: IntentQueryResult
    ) -> EnhancedIntentAnalysis:
        """合并基础意图和图谱结果"""
        # 转换活动为字典格式
        suggested_activities = []
        for activity in graph_results.activities:
            suggested_activities.append({
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "activity_type": activity.activity_type,
                "business_domain": activity.business_domain,
                "vector_entity_uri": activity.vector_entity_uri
            })
        
        # 计算综合置信度
        combined_confidence = base_intent.confidence * 0.6 + min(graph_results.scores[0] if graph_results.scores else 0.5, 1.0) * 0.4
        
        return EnhancedIntentAnalysis(
            base_intent=base_intent,
            suggested_activities=suggested_activities,
            related_entities=[],  # TODO: 从图谱中提取实体
            available_capabilities=[],  # TODO: 从映射中提取能力
            confidence=combined_confidence,
            fallback_mode=False,
            query_time=graph_results.query_time
        )
    
    def _fast_analysis(
        self,
        base_intent: IntentAnalysis,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedIntentAnalysis:
        """快速分析模式（降级策略）"""
        return EnhancedIntentAnalysis(
            base_intent=base_intent,
            suggested_activities=[],
            related_entities=[],
            available_capabilities=[],
            confidence=base_intent.confidence * 0.8,  # 降低置信度
            fallback_mode=True,
            query_time=0.0
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.cache_enabled:
            return {"enabled": False}
        
        total_size = len(self.cache)
        valid_size = sum(
            1 for item in self.cache.values()
            if datetime.now() - item["timestamp"] < timedelta(seconds=self.cache_ttl)
        )
        
        return {
            "enabled": True,
            "total_entries": total_size,
            "valid_entries": valid_size,
            "cache_ttl": self.cache_ttl
        }


# 全局增强路由器实例
enhanced_router = EnhancedIntelligentRouter()






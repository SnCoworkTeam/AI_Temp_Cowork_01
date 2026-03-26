"""
实时元数据查询引擎
并行查询多种元数据源并聚合结果
"""
import logging
import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..services.metadata_catalog import MetadataCatalogService
from ..services.search_service import SearchService
from ..core.database import get_async_redis
from .semantic_service_discovery import semantic_service_discovery
from .metadata_graph import get_metadata_graph
from .user_pattern_analyzer import get_user_pattern_analyzer

logger = logging.getLogger(__name__)


class ExecutionMetadata:
    """执行元数据 - 聚合的元数据结果"""
    
    def __init__(
        self,
        data_assets: List[Dict[str, Any]] = None,
        ai_models: List[Dict[str, Any]] = None,
        business_entities: List[Dict[str, Any]] = None,
        workflows: List[Dict[str, Any]] = None,
        semantic_services: List[Dict[str, Any]] = None,
        user_patterns: Optional[Dict[str, Any]] = None,
        business_context: Optional[Dict[str, Any]] = None,
        query_time: float = 0.0
    ):
        self.data_assets = data_assets or []
        self.ai_models = ai_models or []
        self.business_entities = business_entities or []
        self.workflows = workflows or []
        self.semantic_services = semantic_services or []
        self.user_patterns = user_patterns
        self.business_context = business_context
        self.query_time = query_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data_assets": self.data_assets,
            "ai_models": self.ai_models,
            "business_entities": self.business_entities,
            "workflows": self.workflows,
            "semantic_services": self.semantic_services,
            "user_patterns": self.user_patterns,
            "business_context": self.business_context,
            "query_time": self.query_time,
            "total_count": (
                len(self.data_assets) +
                len(self.ai_models) +
                len(self.business_entities) +
                len(self.workflows) +
                len(self.semantic_services)
            )
        }


class RealtimeMetadataEngine:
    """实时元数据查询引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metadata_catalog = MetadataCatalogService(db)
        self.search_service = SearchService(db)
        self.cache_ttl = 300  # 5分钟缓存
        self.query_timeout = 3.0  # 3秒超时
        self._redis_client = None
    
    async def _get_redis(self):
        """获取Redis客户端（延迟初始化）"""
        if self._redis_client is None:
            try:
                self._redis_client = await get_async_redis()
            except Exception as e:
                logger.warning(f"Failed to get Redis client: {e}, caching disabled")
        return self._redis_client
    
    def _generate_cache_key(self, user_input: str, context: Dict[str, Any]) -> str:
        """生成缓存键"""
        cache_data = {
            "user_input": user_input,
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id")
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"metadata:realtime:{hashlib.md5(cache_str.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取"""
        try:
            redis = await self._get_redis()
            if redis:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
        return None
    
    async def _set_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """设置缓存"""
        try:
            redis = await self._get_redis()
            if redis:
                await redis.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(data)
                )
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")
    
    async def _query_data_assets(self, user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询数据资产"""
        try:
            # 在线程池中运行同步查询
            loop = asyncio.get_event_loop()
            assets = await loop.run_in_executor(
                None,
                lambda: self.metadata_catalog.list_data_assets(
                    search=user_input,
                    limit=limit,
                    skip=0
                )
            )
            return [asset.model_dump() if hasattr(asset, 'model_dump') else dict(asset) for asset in assets]
        except Exception as e:
            logger.error(f"Failed to query data assets: {e}")
            return []
    
    async def _query_ai_models(self, user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询AI模型"""
        try:
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                None,
                lambda: self.metadata_catalog.list_ai_models(
                    search=user_input,
                    limit=limit,
                    skip=0
                )
            )
            return [model.model_dump() if hasattr(model, 'model_dump') else dict(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to query AI models: {e}")
            return []
    
    async def _query_business_entities(self, user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询业务实体"""
        try:
            loop = asyncio.get_event_loop()
            entities = await loop.run_in_executor(
                None,
                lambda: self.metadata_catalog.list_business_entities(
                    search=user_input,
                    limit=limit,
                    skip=0
                )
            )
            return [entity.model_dump() if hasattr(entity, 'model_dump') else dict(entity) for entity in entities]
        except Exception as e:
            logger.error(f"Failed to query business entities: {e}")
            return []
    
    async def _query_workflows(self, user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询工作流"""
        try:
            loop = asyncio.get_event_loop()
            workflows = await loop.run_in_executor(
                None,
                lambda: self.metadata_catalog.list_workflow_metadata(
                    search=user_input,
                    limit=limit,
                    skip=0
                )
            )
            return [wf.model_dump() if hasattr(wf, 'model_dump') else dict(wf) for wf in workflows]
        except Exception as e:
            logger.error(f"Failed to query workflows: {e}")
            return []
    
    async def _query_semantic_services(self, user_input: str, limit: int = 5) -> List[Dict[str, Any]]:
        """查询语义服务"""
        try:
            matches = await semantic_service_discovery.find_semantic_services(
                user_input=user_input,
                limit=limit,
                min_score=0.3
            )
            return [match.to_dict() for match in matches]
        except Exception as e:
            logger.error(f"Failed to query semantic services: {e}")
            return []  # 降级：返回空列表
    
    async def _get_user_patterns(self, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """获取用户行为模式"""
        if not user_id:
            return None
        
        try:
            # 在线程池中运行同步查询
            loop = asyncio.get_event_loop()
            analyzer = await loop.run_in_executor(
                None,
                lambda: get_user_pattern_analyzer(self.db)
            )
            
            patterns = await analyzer.analyze_user_patterns(user_id, days=30, limit=100)
            
            if patterns:
                return patterns.to_dict()
        except Exception as e:
            logger.debug(f"Failed to get user patterns: {e}")
        
        return None
    
    async def _get_business_context(self, user_input: str) -> Optional[Dict[str, Any]]:
        """获取业务上下文"""
        try:
            # 从业务实体中提取相关上下文
            entities = await self._query_business_entities(user_input, limit=3)
            
            # 尝试从知识图谱获取相关服务（阶段3）
            related_services = []
            try:
                metadata_graph = get_metadata_graph(self.db)
                # 提取关键词作为意图
                keywords = user_input.split()[:3]  # 取前3个词
                for keyword in keywords:
                    related = metadata_graph.find_services_by_tags([keyword], limit=2)
                    related_services.extend(related)
            except Exception as e:
                logger.debug(f"Graph query failed: {e}")
            
            if entities or related_services:
                return {
                    "related_entities": entities[:3] if entities else [],
                    "related_services": related_services[:5],
                    "entity_count": len(entities) if entities else 0
                }
        except Exception as e:
            logger.debug(f"Failed to get business context: {e}")
        return None
    
    async def get_execution_metadata(
        self,
        user_input: str,
        context: Dict[str, Any],
        use_cache: bool = True,
        limit_per_type: int = 5
    ) -> ExecutionMetadata:
        """
        获取执行元数据
        
        Args:
            user_input: 用户输入
            context: 上下文信息（包含user_id, session_id等）
            use_cache: 是否使用缓存
            limit_per_type: 每种类型的返回数量限制
            
        Returns:
            执行元数据
        """
        start_time = datetime.now()
        
        # 检查缓存
        cache_key = self._generate_cache_key(user_input, context)
        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Using cached metadata for query: {user_input[:50]}")
                return ExecutionMetadata(**cached)
        
        # 并行查询多种元数据源
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    self._query_data_assets(user_input, limit_per_type),
                    self._query_ai_models(user_input, limit_per_type),
                    self._query_business_entities(user_input, limit_per_type),
                    self._query_workflows(user_input, limit_per_type),
                    self._query_semantic_services(user_input, limit_per_type),
                    return_exceptions=True
                ),
                timeout=self.query_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Metadata query timeout for: {user_input[:50]}")
            results = [[], [], [], [], []]
        
        # 处理结果（忽略异常）
        data_assets = results[0] if not isinstance(results[0], Exception) else []
        ai_models = results[1] if not isinstance(results[1], Exception) else []
        business_entities = results[2] if not isinstance(results[2], Exception) else []
        workflows = results[3] if not isinstance(results[3], Exception) else []
        semantic_services = results[4] if not isinstance(results[4], Exception) else []
        
        # 获取用户模式和业务上下文（异步，不阻塞）
        user_patterns_task = asyncio.create_task(
            self._get_user_patterns(context.get("user_id"))
        )
        business_context_task = asyncio.create_task(
            self._get_business_context(user_input)
        )
        
        # 等待上下文查询（设置较短的超时）
        try:
            user_patterns, business_context = await asyncio.wait_for(
                asyncio.gather(
                    user_patterns_task,
                    business_context_task,
                    return_exceptions=True
                ),
                timeout=1.0
            )
            user_patterns = user_patterns if not isinstance(user_patterns, Exception) else None
            business_context = business_context if not isinstance(business_context, Exception) else None
        except asyncio.TimeoutError:
            user_patterns = None
            business_context = None
        
        # 计算查询时间
        query_time = (datetime.now() - start_time).total_seconds()
        
        # 构建执行元数据
        metadata = ExecutionMetadata(
            data_assets=data_assets,
            ai_models=ai_models,
            business_entities=business_entities,
            workflows=workflows,
            semantic_services=semantic_services,
            user_patterns=user_patterns,
            business_context=business_context,
            query_time=query_time
        )
        
        # 缓存结果
        if use_cache:
            await self._set_to_cache(cache_key, metadata.to_dict())
        
        logger.info(
            f"Metadata query completed: {len(data_assets)} assets, "
            f"{len(ai_models)} models, {len(business_entities)} entities, "
            f"{len(workflows)} workflows, time={query_time:.3f}s"
        )
        
        return metadata


"""
统一搜索服务
整合knowledge-base和metadata-service的搜索结果
包含超时控制、服务降级策略和错误处理
支持向量协调服务集成（可选）
"""
import httpx
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# 可选：向量协调服务客户端
try:
    from .vector_coordinator_client import VectorCoordinatorClient
    VECTOR_COORDINATOR_AVAILABLE = True
except ImportError:
    VECTOR_COORDINATOR_AVAILABLE = False
    VectorCoordinatorClient = None

try:
    from .knowledge_graph_search import KnowledgeGraphSearchService
    KNOWLEDGE_GRAPH_SEARCH_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GRAPH_SEARCH_AVAILABLE = False
    KnowledgeGraphSearchService = None

# 可选：统一搜索缓存
try:
    from .unified_search_cache import UnifiedSearchCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    UnifiedSearchCache = None

logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """统一搜索服务"""
    
    def __init__(self, use_vector_coordinator: bool = True):
        """
        初始化统一搜索服务
        
        Args:
            use_vector_coordinator: 是否使用向量协调服务（如果可用）
        """
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL", 
            "http://knowledge-base:8004"
        )
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        
        # 独立超时配置
        self.kb_timeout = float(os.getenv("KB_SEARCH_TIMEOUT", "2.0"))  # knowledge-base 2秒超时
        self.ms_timeout = float(os.getenv("MS_SEARCH_TIMEOUT", "1.5"))  # metadata-service 1.5秒超时
        
        # HTTP客户端配置
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # 向量协调服务客户端（可选）
        self.use_vector_coordinator = use_vector_coordinator and VECTOR_COORDINATOR_AVAILABLE
        self.vector_coordinator_client = None
        if self.use_vector_coordinator:
            try:
                self.vector_coordinator_client = VectorCoordinatorClient()
                logger.info("Vector coordinator client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize vector coordinator client: {e}")
                self.use_vector_coordinator = False
        
        # 统一搜索缓存（性能优化）
        self.cache_enabled = CACHE_AVAILABLE
        self.cache = None
        if self.cache_enabled:
            try:
                redis_host = os.getenv("REDIS_HOST", "redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                self.cache = UnifiedSearchCache(
                    redis_host=redis_host,
                    redis_port=redis_port,
                    default_ttl=300  # 5分钟
                )
                logger.info("Unified search cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize unified search cache: {e}")
                self.cache_enabled = False
    
    async def unified_search(
        self,
        query: str,
        types: List[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        统一搜索（带缓存优化）
        
        Args:
            query: 搜索查询
            types: 搜索类型列表（document, metadata, entity），默认为["document", "metadata"]
            limit: 返回结果数量限制
            filters: 过滤条件
        
        Returns:
            统一格式的搜索结果
        
        一致性模型: 最终一致性（Eventual Consistency）
        - 实体映射关系可能延迟更新（通常<5分钟）
        - 新创建的实体需要等待自动映射任务执行
        - 搜索结果可能不包含最新的映射关系
        """
        if types is None:
            types = ["document", "metadata"]
        
        start_time = datetime.now()
        
        # 检查缓存
        if use_cache and self.cache_enabled and self.cache:
            cached_result = self.cache.get(query, types, limit, filters)
            if cached_result is not None:
                logger.info(f"Cache hit for query: {query}")
                # 更新搜索时间（使用缓存时间）
                cached_result["search_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
                cached_result["cached"] = True
                return cached_result
        
        results = {
            "documents": [],
            "metadata": [],
            "entities": [],
            "total": 0
        }
        
        # 使用服务降级策略：即使部分服务失败，也返回可用结果
        # 并行执行多个搜索任务（性能优化）
        search_tasks = []
        
        # 准备knowledge-base搜索任务
        if "document" in types:
            search_tasks.append(("kb", self._search_knowledge_base(query, limit)))
        
        # 准备metadata-service搜索任务
        if "metadata" in types or "entity" in types:
            search_tasks.append(("ms", self._search_metadata_service(query, limit)))
        
        # 并行执行搜索任务
        if search_tasks:
            # 使用gather并行执行，设置独立超时
            async def safe_search(task_name, coro):
                try:
                    timeout = self.kb_timeout if task_name == "kb" else self.ms_timeout
                    result = await asyncio.wait_for(coro, timeout=timeout)
                    return (task_name, result, None)
                except asyncio.TimeoutError:
                    logger.warning(f"{task_name} search timeout")
                    return (task_name, None, "timeout")
                except Exception as e:
                    logger.warning(f"{task_name} search failed: {e}")
                    return (task_name, None, str(e))
            
            # 并行执行所有搜索任务
            search_results = await asyncio.gather(
                *[safe_search(name, coro) for name, coro in search_tasks],
                return_exceptions=True
            )
            
            # 处理搜索结果
            for task_result in search_results:
                if isinstance(task_result, Exception):
                    continue
                
                task_name, result, error = task_result
                
                if task_name == "kb" and result:
                    results["documents"] = self._normalize_kb_results(result)
                    logger.info(f"Knowledge-base search succeeded: {len(results['documents'])} results")
                elif task_name == "ms" and result:
                    normalized = self._normalize_metadata_results(result)
                    results["metadata"].extend(normalized.get("assets", []))
                    results["entities"].extend(normalized.get("entities", []))
                    logger.info(
                        f"Metadata-service search succeeded: "
                        f"{len(results['metadata'])} assets, {len(results['entities'])} entities"
                    )
        
        # 可选：使用向量协调服务进行向量搜索
        vector_results = []
        if self.use_vector_coordinator and self.vector_coordinator_client:
            try:
                # 确定要搜索的模态
                search_modalities = []
                if "document" in types:
                    search_modalities.append("knowledge")
                if "metadata" in types or "entity" in types:
                    search_modalities.append("metadata")
                
                if search_modalities:
                    vector_results = await asyncio.wait_for(
                        self.vector_coordinator_client.find_similar_vectors(
                            query=query,
                            modalities=search_modalities,
                            limit=limit
                        ),
                        timeout=1.0  # 向量搜索1秒超时
                    )
                    logger.info(f"Vector coordinator search returned {len(vector_results)} results")
            except asyncio.TimeoutError:
                logger.warning("Vector coordinator search timeout, continuing with regular results")
            except Exception as e:
                logger.warning(f"Vector coordinator search failed: {e}, continuing with regular results")
        
        # 可选：使用知识图谱搜索
        kg_results = []
        if self.kg_search_enabled and KNOWLEDGE_GRAPH_SEARCH_AVAILABLE and KnowledgeGraphSearchService:
            try:
                kg_search_service = KnowledgeGraphSearchService()
                kg_results = await asyncio.wait_for(
                    kg_search_service.search(query, limit=limit),
                    timeout=1.0  # 知识图谱搜索1秒超时
                )
                logger.info(f"Knowledge graph search returned {len(kg_results)} results")
            except asyncio.TimeoutError:
                logger.warning("Knowledge graph search timeout, continuing with regular results")
            except Exception as e:
                logger.warning(f"Knowledge graph search failed: {e}, continuing with regular results")
        
        # 融合和排序结果（包括向量搜索结果和知识图谱结果）
        merged_results = self._merge_and_rank_results(results, query, vector_results, kg_results)
        
        # 计算总时间
        search_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        final_result = {
            "results": merged_results,
            "total": len(merged_results),
            "search_time_ms": search_time_ms,
            "query": query,
            "partial_results": len(results["documents"]) == 0 or (
                len(results["metadata"]) == 0 and len(results["entities"]) == 0
            ),
            "vector_search_enabled": self.use_vector_coordinator and len(vector_results) > 0,
            "knowledge_graph_search_enabled": self.kg_search_enabled and len(kg_results) > 0,
            "cached": False
        }
        
        # 缓存结果
        if use_cache and self.cache_enabled and self.cache:
            self.cache.set(query, types, limit, final_result, filters)
        
        return final_result
    
    async def _search_knowledge_base(
        self,
        query: str,
        limit: int
    ) -> Dict[str, Any]:
        """搜索knowledge-base"""
        try:
            response = await self.http_client.post(
                f"{self.knowledge_base_url}/api/search/semantic",
                json={
                    "query": query,
                    "top_k": limit
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Knowledge-base HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to search knowledge-base: {e}")
            raise
    
    async def _search_metadata_service(
        self,
        query: str,
        limit: int
    ) -> Dict[str, Any]:
        """搜索metadata-service"""
        try:
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/search",
                params={
                    "query": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Metadata-service HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to search metadata-service: {e}")
            raise
    
    def _normalize_kb_results(self, kb_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """标准化knowledge-base结果（增强溯源）"""
        normalized = []
        results = kb_result.get("results", [])
        
        for result in results:
            normalized.append({
                "type": "document",
                "id": result.get("document_id") or result.get("id"),
                "title": result.get("title") or result.get("content", "")[:100],
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "source": "knowledge-base",
                # 答案溯源增强字段
                "source_document": result.get("document_id") or result.get("id"),
                "source_document_name": result.get("title") or result.get("document_name", ""),
                "confidence_score": result.get("score", 0.0),  # 使用相似度分数作为置信度
                "extraction_method": "semantic_search",  # 语义搜索
                "metadata": {
                    "document_id": result.get("document_id"),
                    "chunk_id": result.get("chunk_id"),
                    "knowledge_base_id": result.get("knowledge_base_id")
                }
            })
        
        return normalized
    
    def _normalize_metadata_results(self, ms_result: Dict[str, Any]) -> Dict[str, Any]:
        """标准化metadata-service结果"""
        normalized = {
            "assets": [],
            "entities": []
        }
        
        # 处理数据资产
        assets = ms_result.get("data_assets", [])
        if not assets and isinstance(ms_result, list):
            # 如果返回的是列表，尝试解析
            assets = ms_result
        
        for asset in assets:
            if isinstance(asset, dict):
                score = self._calculate_relevance_score(asset, "")
                normalized["assets"].append({
                    "type": "data_asset",
                    "id": asset.get("id"),
                    "title": asset.get("name") or asset.get("display_name"),
                    "description": asset.get("description", ""),
                    "score": score,
                    "source": "metadata-service",
                    # 答案溯源增强字段
                    "source_entity": str(asset.get("id", "")),
                    "source_entity_name": asset.get("name") or asset.get("display_name", ""),
                    "confidence_score": score,
                    "extraction_method": "metadata_search",  # 元数据搜索
                    "metadata": {
                        "asset_type": asset.get("asset_type"),
                        "source_system": asset.get("source_system"),
                        "sap_table_name": asset.get("sap_table_name")
                    }
                })
        
        # 处理业务实体
        entities = ms_result.get("business_entities", [])
        for entity in entities:
            if isinstance(entity, dict):
                score = self._calculate_relevance_score(entity, "")
                normalized["entities"].append({
                    "type": "business_entity",
                    "id": entity.get("id"),
                    "title": entity.get("name") or entity.get("display_name"),
                    "description": entity.get("description", ""),
                    "score": score,
                    "source": "metadata-service",
                    # 答案溯源增强字段
                    "source_entity": str(entity.get("id", "")),
                    "source_entity_name": entity.get("name") or entity.get("display_name", ""),
                    "confidence_score": score,
                    "extraction_method": "metadata_search",  # 元数据搜索
                    "metadata": {
                        "entity_type": entity.get("entity_type"),
                        "source_system": entity.get("metadata", {}).get("source_system") if isinstance(entity.get("metadata"), dict) else None
                    }
                })
        
        return normalized
    
    def _calculate_relevance_score(
        self,
        item: Dict[str, Any],
        query: str
    ) -> float:
        """计算相关性分数（简单实现）"""
        if not query:
            return 0.5  # 默认分数
        
        query_lower = query.lower()
        score = 0.0
        
        # 名称匹配
        name = (item.get("name") or item.get("display_name") or "").lower()
        if query_lower in name:
            score += 0.5
        if name in query_lower:
            score += 0.3
        
        # 描述匹配
        description = (item.get("description") or "").lower()
        if query_lower in description:
            score += 0.2
        
        return min(score, 1.0)
    
    def _merge_and_rank_results(
        self,
        results: Dict[str, Any],
        query: str,
        vector_results: Optional[List[Dict[str, Any]]] = None,
        kg_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        融合和排序结果
        
        Args:
            results: 常规搜索结果
            query: 查询文本
            vector_results: 向量搜索结果（可选）
        """
        all_results = []
        
        # 收集所有常规结果
        all_results.extend(results.get("documents", []))
        all_results.extend(results.get("metadata", []))
        all_results.extend(results.get("entities", []))
        
        # 添加向量搜索结果（如果可用）
        if vector_results:
            for vec_result in vector_results:
                # 转换向量搜索结果格式
                all_results.append({
                    "type": "vector_match",
                    "entity_uri": vec_result.get("entity_uri"),
                    "modality": vec_result.get("modality"),
                    "score": vec_result.get("similarity", 0.0),
                    "source": "vector-coordinator",
                    "metadata": vec_result.get("metadata", {})
                })
        
        # 去重：基于entity_uri或id
        seen = set()
        unique_results = []
        for result in all_results:
            # 生成唯一标识
            identifier = result.get("entity_uri") or result.get("id") or result.get("document_id")
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_results.append(result)
            elif not identifier:
                # 如果没有唯一标识，直接添加
                unique_results.append(result)
        
        # 按分数排序
        unique_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return unique_results
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
        if self.vector_coordinator_client:
            await self.vector_coordinator_client.close()
        if self.kg_search:
            await self.kg_search.close()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if self.cache_enabled and self.cache:
            return self.cache.get_stats()
        return {"enabled": False}



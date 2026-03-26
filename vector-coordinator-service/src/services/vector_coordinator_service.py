"""
向量协调服务
统一管理向量注册、融合和相似度计算
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.embedding_manager import get_unified_embedding_manager
from ..core.vector_fusion import VectorFusionService
from ..core.similarity_service import SimilarityService
from ..core.config import settings

# 可选：Qdrant集成
try:
    from ..core.qdrant_client import QdrantVectorStore
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantVectorStore = None

# 可选：多级缓存
try:
    from ..core.cache_manager import MultiLevelCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    MultiLevelCache = None

# 可选：批量写入
try:
    from ..core.batch_writer import BatchWriter
    BATCH_WRITER_AVAILABLE = True
except ImportError:
    BATCH_WRITER_AVAILABLE = False
    BatchWriter = None

logger = logging.getLogger(__name__)


class VectorCoordinatorService:
    """向量协调服务"""
    
    def __init__(self, use_qdrant: Optional[bool] = None):
        """
        初始化向量协调服务
        
        Args:
            use_qdrant: 是否使用Qdrant（如果可用）
        """
        self.embedding_manager = get_unified_embedding_manager()
        self.fusion_service = VectorFusionService(
            strategy=settings.FUSION_STRATEGY,
            default_weights=settings.DEFAULT_WEIGHTS
        )
        self.similarity_service = SimilarityService(
            metric=settings.SIMILARITY_METRIC
        )
        
        # 向量存储：优先使用Qdrant，否则使用内存
        use_qdrant_setting = use_qdrant if use_qdrant is not None else settings.USE_QDRANT
        self.use_qdrant = use_qdrant_setting and QDRANT_AVAILABLE
        if self.use_qdrant:
            try:
                self.qdrant_store = QdrantVectorStore(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    collection_name=settings.QDRANT_COLLECTION,
                    vector_size=settings.EMBEDDING_DIMENSION,
                    index_type=settings.QDRANT_INDEX_TYPE
                )
                logger.info("Using Qdrant for vector storage")
            except Exception as e:
                logger.warning(f"Failed to initialize Qdrant, using memory storage: {e}")
                self.use_qdrant = False
                self.qdrant_store = None
        
        # 内存存储（降级方案）
        if not self.use_qdrant:
            self._vector_registry: Dict[str, Dict[str, Any]] = {}
            logger.info("Using memory for vector storage")
        
        # 多级缓存（性能优化）
        self.cache_enabled = settings.CACHE_ENABLED and CACHE_AVAILABLE
        self.cache = None
        if self.cache_enabled:
            try:
                self.cache = MultiLevelCache(
                    l1_max_size=settings.CACHE_L1_MAX_SIZE,
                    l1_ttl=settings.CACHE_L1_TTL,
                    redis_host=settings.REDIS_HOST,
                    redis_port=settings.REDIS_PORT,
                    l2_ttl=settings.CACHE_L2_TTL
                )
                logger.info("Multi-level cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
                self.cache_enabled = False
        
        # 批量写入管理器（持久化优化）
        self.batch_writer = None
        if BATCH_WRITER_AVAILABLE and settings.PERSISTENCE_MODE in ["batch", "hybrid"]:
            try:
                self.batch_writer = BatchWriter(
                    write_interval=settings.BATCH_WRITE_INTERVAL,
                    batch_size=settings.BATCH_WRITE_SIZE,
                    write_callback=self._batch_write_callback
                )
                logger.info("Batch writer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize batch writer: {e}")
    
    async def _batch_write_callback(self, items: List[Dict[str, Any]]) -> bool:
        """批量写入回调函数"""
        if not self.use_qdrant or not self.qdrant_store:
            return False
        
        try:
            # 批量写入到Qdrant
            success_count = 0
            for item in items:
                success = self.qdrant_store.store_vector(
                    entity_uri=item.get("entity_uri"),
                    modality=item.get("modality"),
                    vector=item.get("vector"),
                    metadata=item.get("metadata")
                )
                if success:
                    success_count += 1
            
            return success_count == len(items)
        except Exception as e:
            logger.error(f"Batch write callback error: {e}", exc_info=True)
            return False
    
    async def register_vector(
        self,
        entity_uri: str,
        modality: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "normal"  # realtime, normal, batch
    ) -> bool:
        """
        注册向量（支持实时+批量策略）
        
        Args:
            entity_uri: 实体URI（entity://domain/type/id）
            modality: 模态（metadata, knowledge, permission等）
            vector: 向量
            metadata: 元数据
            priority: 优先级（realtime: 立即写入, normal/batch: 批量写入）
        
        Returns:
            是否注册成功
        """
        try:
            # 确定数据重要性
            # 元数据实体和知识图谱节点：实时写入
            # 文档向量：批量写入
            if priority == "auto":
                if modality in ["metadata", "knowledge"] and "entity" in entity_uri:
                    priority = "realtime"
                else:
                    priority = "batch"
            
            # 如果使用批量写入且不是实时优先级
            if self.batch_writer and priority != "realtime":
                await self.batch_writer.add_item({
                    "entity_uri": entity_uri,
                    "modality": modality,
                    "vector": vector,
                    "metadata": metadata
                }, priority=priority)
                logger.debug(f"Vector added to batch queue: {entity_uri}:{modality}")
                return True
            
            # 实时写入或没有批量写入器
            if self.use_qdrant and self.qdrant_store:
                # 使用Qdrant存储
                return self.qdrant_store.store_vector(
                    entity_uri=entity_uri,
                    modality=modality,
                    vector=vector,
                    metadata=metadata
                )
            else:
                # 使用内存存储
                key = f"{entity_uri}:{modality}"
                self._vector_registry[key] = {
                    "entity_uri": entity_uri,
                    "modality": modality,
                    "vector": vector,
                    "metadata": metadata or {},
                    "registered_at": datetime.now().isoformat()
                }
                logger.info(f"Vector registered (memory): {key}")
                return True
        except Exception as e:
            logger.error(f"Failed to register vector: {e}", exc_info=True)
            return False
    
    def fuse_vectors(
        self,
        vectors: Dict[str, List[float]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[float]:
        """
        融合多个模态的向量
        
        Args:
            vectors: 向量字典，key为模态名称
            weights: 权重字典（可选）
        
        Returns:
            融合后的向量
        """
        try:
            return self.fusion_service.fuse(vectors, weights)
        except Exception as e:
            logger.error(f"Failed to fuse vectors: {e}", exc_info=True)
            raise
    
    async def find_similar_vectors(
        self,
        query: str,
        modalities: Optional[List[str]] = None,
        limit: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        查找相似向量（带缓存优化）
        
        Args:
            query: 查询文本
            modalities: 模态列表（可选，如果为None则搜索所有模态）
            limit: 返回数量限制
            threshold: 相似度阈值（可选，使用配置中的默认值）
        
        Returns:
            相似向量列表
        """
        try:
            # 检查缓存
            if self.cache_enabled and self.cache:
                cache_key_parts = ["similar", query, str(modalities), str(limit), str(threshold)]
                cached_result = await self.cache.get("vector_search", *cache_key_parts)
                if cached_result is not None:
                    logger.debug(f"Cache hit for query: {query}")
                    return cached_result
            
            # 将查询文本编码为向量
            query_vector = self.embedding_manager.encode_single(query)
            threshold_value = threshold or settings.SIMILARITY_THRESHOLD
            
            if self.use_qdrant and self.qdrant_store:
                # 使用Qdrant搜索
                # 如果指定了多个模态，需要分别搜索然后合并
                if modalities and len(modalities) == 1:
                    results = self.qdrant_store.search_vectors(
                        query_vector=query_vector,
                        limit=limit,
                        modality=modalities[0],
                        threshold=threshold_value
                    )
                else:
                    # 多个模态或未指定，搜索所有然后过滤
                    results = self.qdrant_store.search_vectors(
                        query_vector=query_vector,
                        limit=limit * 2,  # 多取一些以便过滤
                        modality=None,
                        threshold=threshold_value
                    )
                    # 过滤模态
                    if modalities:
                        results = [r for r in results if r.get("modality") in modalities]
                    results = results[:limit]
            else:
                # 使用内存搜索
                candidates = []
                for key, data in self._vector_registry.items():
                    if modalities is None or data["modality"] in modalities:
                        candidates.append({
                            "vector": data["vector"],
                            "entity_uri": data["entity_uri"],
                            "modality": data["modality"],
                            "metadata": data["metadata"]
                        })
                
                results = self.similarity_service.find_similar(
                    query_vector,
                    candidates,
                    limit=limit,
                    threshold=threshold_value
                )
            
            # 缓存结果
            if self.cache_enabled and self.cache:
                cache_key_parts = ["similar", query, str(modalities), str(limit), str(threshold)]
                await self.cache.set("vector_search", results, *cache_key_parts, ttl=settings.CACHE_L1_TTL)
            
            return results
        except Exception as e:
            logger.error(f"Failed to find similar vectors: {e}", exc_info=True)
            raise
    
    def get_vector_info(self, entity_uri: str, modality: str) -> Optional[Dict[str, Any]]:
        """获取向量信息"""
        if self.use_qdrant and self.qdrant_store:
            return self.qdrant_store.get_vector(entity_uri, modality)
        else:
            key = f"{entity_uri}:{modality}"
            return self._vector_registry.get(key)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取向量注册表统计信息"""
        stats = {}
        
        if self.use_qdrant and self.qdrant_store:
            qdrant_stats = self.qdrant_store.get_collection_stats()
            stats = {
                "storage_type": "qdrant",
                "qdrant_stats": qdrant_stats,
                "total_vectors": qdrant_stats.get("points_count", 0),
                "by_modality": {},  # Qdrant中需要额外查询才能获取
            }
        else:
            total = len(self._vector_registry)
            by_modality = {}
            for data in self._vector_registry.values():
                modality = data["modality"]
                by_modality[modality] = by_modality.get(modality, 0) + 1
            
            stats = {
                "storage_type": "memory",
                "total_vectors": total,
                "by_modality": by_modality,
            }
        
        # 添加缓存统计
        if self.cache_enabled and self.cache:
            stats["cache_stats"] = self.cache.get_stats()
        
        # 添加其他信息
        stats.update({
            "model_info": self.embedding_manager.get_model_info(),
            "fusion_info": self.fusion_service.get_fusion_info(),
            "similarity_info": self.similarity_service.get_metric_info()
        })
        
        return stats



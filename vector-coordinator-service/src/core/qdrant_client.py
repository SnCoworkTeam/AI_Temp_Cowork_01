"""
Qdrant向量数据库客户端
用于持久化存储向量数据
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入Qdrant客户端
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue,
        HnswConfig
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    HnswConfig = None
    logger.warning("qdrant-client not available, Qdrant features will be disabled")


class QdrantVectorStore:
    """Qdrant向量存储"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "unified_vectors",
        vector_size: int = 384,
        index_type: str = "hnsw"
    ):
        """
        初始化Qdrant客户端
        
        Args:
            host: Qdrant服务器地址
            port: Qdrant服务器端口
            collection_name: 集合名称
            vector_size: 向量维度
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.index_type = index_type
        self.client = None
        
        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(host=host, port=port)
                self._ensure_collection(index_type)
                logger.info(f"Qdrant client initialized: {host}:{port} with {index_type} index")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant client: {e}")
                self.client = None
        else:
            logger.warning("Qdrant client not available, using mock storage")
    
    def _ensure_collection(self, index_type: str = "hnsw"):
        """
        确保集合存在
        
        Args:
            index_type: 索引类型（hnsw, ivf, flat）
        """
        if not self.client:
            return
        
        try:
            # 检查集合是否存在
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # 配置向量参数
                # HNSW配置
                hnsw_config = None
                if index_type == "hnsw" and HnswConfig:
                    from ..core.config import settings
                    hnsw_config = HnswConfig(
                        m=settings.QDRANT_HNSW_M,
                        ef_construct=settings.QDRANT_HNSW_EF_CONSTRUCT
                    )
                
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                        hnsw_config=hnsw_config
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name} with {index_type} index")
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
    
    def store_vector(
        self,
        entity_uri: str,
        modality: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        存储向量
        
        Args:
            entity_uri: 实体URI
            modality: 模态
            vector: 向量
            metadata: 元数据
        
        Returns:
            是否成功
        """
        if not self.client:
            logger.warning("Qdrant client not available, vector not stored")
            return False
        
        try:
            # 生成点ID（使用entity_uri和modality的组合）
            point_id = self._generate_point_id(entity_uri, modality)
            
            # 准备元数据
            payload = {
                "entity_uri": entity_uri,
                "modality": modality,
                "stored_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # 创建点
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            # 插入点
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Stored vector: {entity_uri}:{modality}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store vector: {e}", exc_info=True)
            return False
    
    def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        modality: Optional[str] = None,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            limit: 返回数量限制
            modality: 模态过滤（可选）
            threshold: 相似度阈值
        
        Returns:
            相似向量列表
        """
        if not self.client:
            logger.warning("Qdrant client not available, returning empty results")
            return []
        
        try:
            # 构建过滤条件
            filter_condition = None
            if modality:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="modality",
                            match=MatchValue(value=modality)
                        )
                    ]
                )
            
            # 搜索
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_condition,
                score_threshold=threshold
            )
            
            # 格式化结果
            results = []
            for result in search_results:
                results.append({
                    "entity_uri": result.payload.get("entity_uri"),
                    "modality": result.payload.get("modality"),
                    "similarity": float(result.score),
                    "metadata": {k: v for k, v in result.payload.items() 
                                if k not in ["entity_uri", "modality", "stored_at"]}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}", exc_info=True)
            return []
    
    def get_vector(
        self,
        entity_uri: str,
        modality: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定实体的向量
        
        Args:
            entity_uri: 实体URI
            modality: 模态
        
        Returns:
            向量信息（如果存在）
        """
        if not self.client:
            return None
        
        try:
            point_id = self._generate_point_id(entity_uri, modality)
            
            # 检索点
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if not points:
                return None
            
            point = points[0]
            return {
                "entity_uri": point.payload.get("entity_uri"),
                "modality": point.payload.get("modality"),
                "vector": point.vector,
                "metadata": {k: v for k, v in point.payload.items() 
                            if k not in ["entity_uri", "modality", "stored_at"]}
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector: {e}", exc_info=True)
            return None
    
    def delete_vector(
        self,
        entity_uri: str,
        modality: str
    ) -> bool:
        """删除向量"""
        if not self.client:
            return False
        
        try:
            point_id = self._generate_point_id(entity_uri, modality)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector: {e}", exc_info=True)
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self.client:
            return {"available": False}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "available": True,
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}", exc_info=True)
            return {"available": False, "error": str(e)}
    
    def _generate_point_id(self, entity_uri: str, modality: str) -> int:
        """生成点ID（使用哈希）"""
        import hashlib
        key = f"{entity_uri}:{modality}"
        hash_obj = hashlib.md5(key.encode())
        # 使用哈希值的前8位作为ID（转换为整数）
        return int(hash_obj.hexdigest()[:8], 16)


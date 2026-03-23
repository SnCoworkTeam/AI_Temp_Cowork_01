"""
向量存储管理
支持Chroma和Weaviate
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# 尝试导入Chroma
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not available")

# 尝试导入Weaviate
try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError:
    try:
        # 尝试从 weaviate-client 导入
        from weaviate import Client
        WEAVIATE_AVAILABLE = True
    except ImportError:
        WEAVIATE_AVAILABLE = False
        logger.warning("weaviate-client not available, Weaviate features will be disabled")


class VectorStore:
    """向量存储抽象基类"""
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档向量
        
        Args:
            texts: 文本列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列表
            ids: ID列表（可选）
        
        Returns:
            文档ID列表
        """
        raise NotImplementedError
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件
        
        Returns:
            搜索结果列表
        """
        raise NotImplementedError
    
    def delete(self, ids: List[str]) -> bool:
        """
        删除文档
        
        Args:
            ids: 文档ID列表
        
        Returns:
            是否成功
        """
        raise NotImplementedError
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据ID获取文档
        
        Args:
            ids: 文档ID列表
        
        Returns:
            文档列表
        """
        raise NotImplementedError


class ChromaVectorStore(VectorStore):
    """Chroma向量存储实现"""
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents"):
        """
        初始化Chroma向量存储
        
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb is not installed")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Chroma vector store initialized: {persist_directory}")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档向量"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # 转换元数据为Chroma格式
        chroma_metadatas = []
        for meta in metadatas:
            chroma_meta = {}
            for key, value in meta.items():
                # Chroma只支持特定类型
                if isinstance(value, (str, int, float, bool)):
                    chroma_meta[key] = value
                else:
                    chroma_meta[key] = str(value)
            chroma_metadatas.append(chroma_meta)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=chroma_metadatas
        )
        
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """相似度搜索"""
        # 构建查询条件
        where = None
        if filters:
            where = {}
            for key, value in filters.items():
                where[key] = value
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        # 格式化结果
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'score': 1 - results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def delete(self, ids: List[str]) -> bool:
        """删除文档"""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """根据ID获取文档"""
        results = self.collection.get(ids=ids)
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'])):
                formatted_results.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
        
        return formatted_results


class MockVectorStore(VectorStore):
    """模拟向量存储（用于开发环境）"""
    
    def __init__(self):
        """初始化模拟向量存储"""
        self.documents: Dict[str, Dict[str, Any]] = {}
        logger.warning("Using mock vector store")
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档向量"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        for i, doc_id in enumerate(ids):
            self.documents[doc_id] = {
                'id': doc_id,
                'content': texts[i],
                'embedding': embeddings[i],
                'metadata': metadatas[i]
            }
        
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """相似度搜索（简单实现）"""
        import numpy as np
        
        results = []
        for doc_id, doc in self.documents.items():
            # 应用过滤条件
            if filters:
                match = True
                for key, value in filters.items():
                    if key not in doc['metadata'] or doc['metadata'][key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            # 计算余弦相似度
            embedding = np.array(doc['embedding'])
            query = np.array(query_embedding)
            similarity = np.dot(embedding, query) / (np.linalg.norm(embedding) * np.linalg.norm(query))
            
            results.append({
                'id': doc_id,
                'content': doc['content'],
                'metadata': doc['metadata'],
                'score': float(similarity),
                'distance': 1 - float(similarity)
            })
        
        # 按相似度排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def delete(self, ids: List[str]) -> bool:
        """删除文档"""
        for doc_id in ids:
            if doc_id in self.documents:
                del self.documents[doc_id]
        return True
    
    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """根据ID获取文档"""
        results = []
        for doc_id in ids:
            if doc_id in self.documents:
                doc = self.documents[doc_id].copy()
                doc.pop('embedding', None)  # 移除嵌入向量以节省空间
                results.append(doc)
        return results


def create_vector_store(store_type: str = "chroma", **kwargs) -> VectorStore:
    """
    创建向量存储实例
    
    Args:
        store_type: 存储类型（chroma/weaviate/mock）
        **kwargs: 额外参数
    
    Returns:
        向量存储实例
    """
    if store_type == "chroma":
        if CHROMA_AVAILABLE:
            persist_dir = kwargs.get('persist_directory', './chroma_db')
            collection_name = kwargs.get('collection_name', 'documents')
            return ChromaVectorStore(persist_directory=persist_dir, collection_name=collection_name)
        else:
            logger.warning("Chroma not available, using mock vector store")
            return MockVectorStore()
    elif store_type == "weaviate":
        # TODO: 实现Weaviate支持
        logger.warning("Weaviate not yet implemented, using mock vector store")
        return MockVectorStore()
    else:
        logger.warning(f"Unknown vector store type: {store_type}, using mock")
        return MockVectorStore()


# 全局向量存储实例
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    
    if _vector_store is None:
        from ..config import settings
        _vector_store = create_vector_store(
            store_type=settings.VECTOR_STORE_TYPE,
            persist_directory=settings.CHROMA_PERSIST_DIR
        )
    
    return _vector_store








"""
向量Repository
向量索引元数据管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.knowledge_models import (
    DocumentChunk as DBDocumentChunk
)

logger = logging.getLogger(__name__)


class VectorRepository:
    """向量Repository（管理向量索引元数据）"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_vector_metadata(
        self,
        chunk_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取向量元数据
        
        Args:
            chunk_id: 块ID
        
        Returns:
            向量元数据字典（包含embedding, embedding_model等）
        """
        try:
            from .chunk_repository import ChunkRepository
            
            chunk_repo = ChunkRepository(self.session)
            chunk = chunk_repo.get_by_id(chunk_id)
            
            if chunk and chunk.embedding:
                embedding_data = chunk.embedding
                if isinstance(embedding_data, dict):
                    vector = embedding_data.get("vector")
                else:
                    vector = embedding_data
                
                return {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "vector": vector,
                    "embedding_model": chunk.embedding_model,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content[:100] if chunk.content else ""  # 前100字符
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting vector metadata: {str(e)}")
            return None
    
    def list_vectors_by_document(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """列出文档的所有向量元数据"""
        try:
            from .chunk_repository import ChunkRepository
            
            chunk_repo = ChunkRepository(self.session)
            chunks = chunk_repo.get_chunks_with_embeddings(document_id)
            
            vectors = []
            for chunk in chunks:
                embedding_data = chunk.embedding
                if isinstance(embedding_data, dict):
                    vector = embedding_data.get("vector")
                else:
                    vector = embedding_data
                
                vectors.append({
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "vector": vector,
                    "embedding_model": chunk.embedding_model,
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.content[:100] if chunk.content else ""
                })
            
            return vectors
            
        except Exception as e:
            logger.error(f"Error listing vectors by document: {str(e)}")
            return []
    
    def get_vector_index_stats(
        self,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取向量索引统计信息"""
        try:
            from .chunk_repository import ChunkRepository
            
            chunk_repo = ChunkRepository(self.session)
            
            if document_id:
                chunks = chunk_repo.get_chunks_with_embeddings(document_id)
                total_chunks = len(chunk_repo.get_by_document_id(document_id))
            else:
                # 获取所有文档块
                from database.src.models.knowledge_models import DocumentChunk
                all_chunks = self.session.query(DocumentChunk).all()
                chunks = [c for c in all_chunks if c.embedding is not None]
                total_chunks = len(all_chunks)
            
            # 统计不同模型的数量
            model_counts = {}
            for chunk in chunks:
                model = chunk.embedding_model or "unknown"
                model_counts[model] = model_counts.get(model, 0) + 1
            
            return {
                "total_chunks": total_chunks,
                "indexed_chunks": len(chunks),
                "indexing_rate": len(chunks) / total_chunks if total_chunks > 0 else 0.0,
                "embedding_models": model_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting vector index stats: {str(e)}")
            return {
                "total_chunks": 0,
                "indexed_chunks": 0,
                "indexing_rate": 0.0,
                "embedding_models": {}
            }
    
    def update_vector_index(
        self,
        chunk_id: str,
        vector_id: Optional[str] = None,
        vector_store_type: Optional[str] = None
    ) -> bool:
        """
        更新向量索引信息（在chunk的metadata中）
        
        Args:
            chunk_id: 块ID
            vector_id: 向量存储中的ID
            vector_store_type: 向量存储类型（如chroma, weaviate）
        
        Returns:
            是否成功
        """
        try:
            from .chunk_repository import ChunkRepository
            
            chunk_repo = ChunkRepository(self.session)
            chunk = chunk_repo.get_by_id(chunk_id)
            
            if chunk:
                if chunk.metadata is None:
                    chunk.metadata = {}
                
                vector_index_info = chunk.metadata.get("vector_index", {})
                if vector_id:
                    vector_index_info["vector_id"] = vector_id
                if vector_store_type:
                    vector_index_info["vector_store_type"] = vector_store_type
                
                chunk.metadata["vector_index"] = vector_index_info
                self.session.flush()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating vector index: {str(e)}")
            self.session.rollback()
            return False










"""
文档块Repository
文档分块数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
from database.src.repositories.knowledge_repository import (
    DocumentChunkRepository as DBDocumentChunkRepository
)

logger = logging.getLogger(__name__)


class ChunkRepository:
    """文档块Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBDocumentChunkRepository(session)
    
    def get_by_id(self, chunk_id: str) -> Optional[DBDocumentChunk]:
        """根据ID获取文档块"""
        try:
            uuid_id = UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid chunk_id format: {chunk_id}")
            return None
    
    def get_by_document_id(self, document_id: str) -> List[DBDocumentChunk]:
        """根据文档ID获取所有文档块"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            return self._db_repo.get_by_document_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid document_id format: {document_id}")
            return []
    
    def create_chunk(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
        page_number: Optional[int] = None,
        embedding: Optional[List[float]] = None,
        embedding_model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBDocumentChunk:
        """创建文档块"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            
            # 准备embedding数据
            embedding_data = None
            if embedding:
                embedding_data = {"vector": embedding}
            
            chunk = DBDocumentChunk(
                document_id=uuid_id,
                chunk_index=chunk_index,
                content=content,
                start_char=start_char,
                end_char=end_char,
                page_number=page_number,
                embedding=embedding_data,
                embedding_model=embedding_model,
                chunk_metadata=metadata or {}
            )
            self.session.add(chunk)
            self.session.flush()
            return chunk
        except SQLAlchemyError as e:
            logger.error(f"Error creating chunk: {str(e)}")
            self.session.rollback()
            raise
    
    def create_chunks_batch(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[DBDocumentChunk]:
        """批量创建文档块"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            
            created_chunks = []
            for chunk_data in chunks:
                # 准备embedding数据
                embedding_data = None
                if chunk_data.get("embedding"):
                    embedding_data = {"vector": chunk_data.get("embedding")}
                
                chunk = DBDocumentChunk(
                    document_id=uuid_id,
                    chunk_index=chunk_data.get("chunk_index", 0),
                    content=chunk_data.get("content", ""),
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("end_char"),
                    page_number=chunk_data.get("page_number"),
                    embedding=embedding_data,
                    embedding_model=chunk_data.get("embedding_model"),
                    chunk_metadata=chunk_data.get("metadata", {})
                )
                self.session.add(chunk)
                created_chunks.append(chunk)
            
            self.session.flush()
            return created_chunks
        except SQLAlchemyError as e:
            logger.error(f"Error creating chunks batch: {str(e)}")
            self.session.rollback()
            raise
    
    def update_chunk(
        self,
        chunk_id: str,
        **updates
    ) -> Optional[DBDocumentChunk]:
        """更新文档块"""
        try:
            uuid_id = UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id
            
            # 处理embedding字段
            if "embedding" in updates:
                embedding = updates["embedding"]
                if isinstance(embedding, list):
                    updates["embedding"] = {"vector": embedding}
            
            return self._db_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid chunk_id format: {chunk_id}")
            return None
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """删除文档块"""
        try:
            uuid_id = UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id
            return self._db_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid chunk_id format: {chunk_id}")
            return False
    
    def delete_by_document_id(self, document_id: str) -> int:
        """删除文档的所有块"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            return self._db_repo.delete_by_document_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid document_id format: {document_id}")
            return 0
    
    def get_chunks_with_embeddings(
        self,
        document_id: str
    ) -> List[DBDocumentChunk]:
        """获取文档的所有带嵌入向量的块"""
        try:
            chunks = self.get_by_document_id(document_id)
            return [chunk for chunk in chunks if chunk.embedding is not None]
        except Exception as e:
            logger.error(f"Error getting chunks with embeddings: {str(e)}")
            return []
    
    def update_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        embedding_model: str
    ) -> bool:
        """更新块的嵌入向量"""
        try:
            chunk = self.get_by_id(chunk_id)
            if chunk:
                chunk.embedding = {"vector": embedding}
                chunk.embedding_model = embedding_model
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating embedding: {str(e)}")
            self.session.rollback()
            return False










"""
知识库服务
知识库业务逻辑层
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from ..repositories.knowledge_base_repository import KnowledgeBaseRepository
from ..repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """知识库服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)
    
    async def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        embedding_model: str = "default",
        chunk_strategy: str = "fixed",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建知识库"""
        try:
            # 检查名称是否已存在
            existing = self.kb_repo.get_by_name(name)
            if existing:
                raise ValueError(f"Knowledge base with name '{name}' already exists")
            
            created_by_uuid = None
            if created_by:
                try:
                    created_by_uuid = UUID(created_by)
                except ValueError:
                    logger.warning(f"Invalid created_by UUID: {created_by}")
            
            knowledge_base = self.kb_repo.create(
                name=name,
                description=description or "",
                created_by=created_by_uuid,
                embedding_model=embedding_model,
                chunk_strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                settings=settings or {}
            )
            
            self.db.commit()
            
            return {
                "id": str(knowledge_base.id),
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "status": knowledge_base.status.value,
                "embedding_model": knowledge_base.embedding_model,
                "chunk_strategy": knowledge_base.chunk_strategy,
                "chunk_size": knowledge_base.chunk_size,
                "chunk_overlap": knowledge_base.chunk_overlap,
                "settings": knowledge_base.settings or {},
                "created_at": knowledge_base.created_at.isoformat(),
                "updated_at": knowledge_base.updated_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating knowledge base: {str(e)}", exc_info=True)
            raise
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取知识库详情"""
        try:
            knowledge_base = self.kb_repo.get_by_id(kb_id)
            if not knowledge_base:
                return None
            
            document_count = self.kb_repo.get_document_count(kb_id)
            total_chunks = self.kb_repo.get_total_chunks(kb_id)
            
            return {
                "id": str(knowledge_base.id),
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "status": knowledge_base.status.value,
                "document_count": document_count,
                "total_chunks": total_chunks,
                "embedding_model": knowledge_base.embedding_model,
                "chunk_strategy": knowledge_base.chunk_strategy,
                "chunk_size": knowledge_base.chunk_size,
                "chunk_overlap": knowledge_base.chunk_overlap,
                "settings": knowledge_base.settings or {},
                "created_by": str(knowledge_base.created_by) if knowledge_base.created_by else None,
                "created_at": knowledge_base.created_at.isoformat(),
                "updated_at": knowledge_base.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting knowledge base: {str(e)}", exc_info=True)
            raise
    
    async def list_knowledge_bases(
        self,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取知识库列表"""
        try:
            created_by_uuid = None
            if created_by:
                try:
                    created_by_uuid = UUID(created_by)
                except ValueError:
                    pass
            
            offset = (page - 1) * page_size
            knowledge_bases = self.kb_repo.list_all(
                status=status,
                created_by=created_by_uuid,
                search=search,
                limit=page_size,
                offset=offset
            )
            
            total = self.kb_repo.count(
                status=status,
                created_by=created_by_uuid,
                search=search
            )
            
            # 优化：批量获取文档数量和块数，避免N+1查询问题
            kb_ids = [str(kb.id) for kb in knowledge_bases]
            document_counts = self.kb_repo.get_document_counts_batch(kb_ids)
            total_chunks_map = self.kb_repo.get_total_chunks_batch(kb_ids)
            
            result = []
            for kb in knowledge_bases:
                kb_id_str = str(kb.id)
                document_count = document_counts.get(kb_id_str, 0)
                total_chunks = total_chunks_map.get(kb_id_str, 0)
                
                result.append({
                    "id": kb_id_str,
                    "name": kb.name,
                    "description": kb.description or "",
                    "status": kb.status.value,
                    "document_count": document_count,
                    "total_chunks": total_chunks,
                    "embedding_model": kb.embedding_model,
                    "chunk_strategy": kb.chunk_strategy,
                    "chunk_size": kb.chunk_size,
                    "chunk_overlap": kb.chunk_overlap,
                    "settings": kb.settings or {},
                    "created_at": kb.created_at.isoformat(),
                    "updated_at": kb.updated_at.isoformat()
                })
            
            return {
                "knowledge_bases": result,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {str(e)}", exc_info=True)
            raise
    
    async def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """更新知识库"""
        try:
            updates = {}
            
            if name is not None:
                # 检查名称是否已被其他知识库使用
                existing = self.kb_repo.get_by_name(name)
                if existing and str(existing.id) != kb_id:
                    raise ValueError(f"Knowledge base with name '{name}' already exists")
                updates["name"] = name
            
            if description is not None:
                updates["description"] = description
            
            if status is not None:
                updates["status"] = status
            
            if embedding_model is not None:
                updates["embedding_model"] = embedding_model
            
            if chunk_strategy is not None:
                updates["chunk_strategy"] = chunk_strategy
            
            if chunk_size is not None:
                updates["chunk_size"] = chunk_size
            
            if chunk_overlap is not None:
                updates["chunk_overlap"] = chunk_overlap
            
            if settings is not None:
                # 合并设置而不是替换
                existing_kb = self.kb_repo.get_by_id(kb_id)
                if existing_kb:
                    current_settings = existing_kb.settings or {}
                    current_settings.update(settings)
                    updates["settings"] = current_settings
                else:
                    updates["settings"] = settings
            
            knowledge_base = self.kb_repo.update(kb_id, **updates)
            
            if not knowledge_base:
                return None
            
            self.db.commit()
            
            document_count = self.kb_repo.get_document_count(kb_id)
            total_chunks = self.kb_repo.get_total_chunks(kb_id)
            
            return {
                "id": str(knowledge_base.id),
                "name": knowledge_base.name,
                "description": knowledge_base.description,
                "status": knowledge_base.status.value,
                "document_count": document_count,
                "total_chunks": total_chunks,
                "embedding_model": knowledge_base.embedding_model,
                "chunk_strategy": knowledge_base.chunk_strategy,
                "chunk_size": knowledge_base.chunk_size,
                "chunk_overlap": knowledge_base.chunk_overlap,
                "settings": knowledge_base.settings or {},
                "created_at": knowledge_base.created_at.isoformat(),
                "updated_at": knowledge_base.updated_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating knowledge base: {str(e)}", exc_info=True)
            raise
    
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            success = self.kb_repo.delete(kb_id)
            if success:
                self.db.commit()
            return success
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting knowledge base: {str(e)}", exc_info=True)
            raise
    
    async def get_knowledge_base_stats(self, kb_id: str) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            knowledge_base = self.kb_repo.get_by_id(kb_id)
            if not knowledge_base:
                return {}
            
            document_count = self.kb_repo.get_document_count(kb_id)
            total_chunks = self.kb_repo.get_total_chunks(kb_id)
            
            # 可以添加更多统计信息，如文档类型分布、存储大小等
            
            return {
                "id": str(knowledge_base.id),
                "name": knowledge_base.name,
                "document_count": document_count,
                "total_chunks": total_chunks,
                "status": knowledge_base.status.value,
                "created_at": knowledge_base.created_at.isoformat(),
                "updated_at": knowledge_base.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}", exc_info=True)
            raise




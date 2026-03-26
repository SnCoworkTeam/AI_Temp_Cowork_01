"""
知识库Repository
知识库数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.knowledge_models import (
    KnowledgeBase as DBKnowledgeBase,
    KnowledgeBaseStatus,
    Document as DBDocument
)

logger = logging.getLogger(__name__)


class KnowledgeBaseRepository:
    """知识库Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, kb_id: str) -> Optional[DBKnowledgeBase]:
        """根据ID获取知识库"""
        try:
            uuid_id = UUID(kb_id) if isinstance(kb_id, str) else kb_id
            return self.session.query(DBKnowledgeBase).filter(DBKnowledgeBase.id == uuid_id).first()
        except (ValueError, TypeError):
            logger.warning(f"Invalid knowledge_base_id format: {kb_id}")
            return None
    
    def get_by_name(self, name: str) -> Optional[DBKnowledgeBase]:
        """根据名称获取知识库"""
        return self.session.query(DBKnowledgeBase).filter(DBKnowledgeBase.name == name).first()
    
    def list_all(
        self,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[DBKnowledgeBase]:
        """获取知识库列表"""
        query = self.session.query(DBKnowledgeBase)
        
        if status:
            try:
                kb_status = KnowledgeBaseStatus(status.lower())
                query = query.filter(DBKnowledgeBase.status == kb_status)
            except ValueError:
                logger.warning(f"Invalid status: {status}")
        
        if created_by:
            query = query.filter(DBKnowledgeBase.created_by == created_by)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DBKnowledgeBase.name.ilike(search_pattern),
                    DBKnowledgeBase.description.ilike(search_pattern)
                )
            )
        
        query = query.order_by(desc(DBKnowledgeBase.created_at))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def count(
        self,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> int:
        """统计知识库数量"""
        query = self.session.query(func.count(DBKnowledgeBase.id))
        
        if status:
            try:
                kb_status = KnowledgeBaseStatus(status.lower())
                query = query.filter(DBKnowledgeBase.status == kb_status)
            except ValueError:
                pass
        
        if created_by:
            query = query.filter(DBKnowledgeBase.created_by == created_by)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DBKnowledgeBase.name.ilike(search_pattern),
                    DBKnowledgeBase.description.ilike(search_pattern)
                )
            )
        
        return query.scalar() or 0
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
        embedding_model: str = "default",
        chunk_strategy: str = "fixed",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        settings: Optional[Dict[str, Any]] = None
    ) -> DBKnowledgeBase:
        """创建知识库"""
        try:
            knowledge_base = DBKnowledgeBase(
                name=name,
                description=description or "",
                status=KnowledgeBaseStatus.ACTIVE,
                created_by=created_by,
                embedding_model=embedding_model,
                chunk_strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                settings=settings or {}
            )
            self.session.add(knowledge_base)
            self.session.flush()
            return knowledge_base
        except SQLAlchemyError as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            self.session.rollback()
            raise
    
    def update(
        self,
        kb_id: str,
        **updates
    ) -> Optional[DBKnowledgeBase]:
        """更新知识库"""
        try:
            uuid_id = UUID(kb_id) if isinstance(kb_id, str) else kb_id
            knowledge_base = self.get_by_id(uuid_id)
            
            if not knowledge_base:
                return None
            
            # 处理状态字段
            if "status" in updates:
                status_str = updates["status"]
                try:
                    updates["status"] = KnowledgeBaseStatus(status_str.lower())
                except ValueError:
                    logger.warning(f"Invalid status: {status_str}")
                    del updates["status"]
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(knowledge_base, key):
                    setattr(knowledge_base, key, value)
            
            self.session.flush()
            return knowledge_base
        except (ValueError, TypeError):
            logger.warning(f"Invalid knowledge_base_id format: {kb_id}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            self.session.rollback()
            raise
    
    def delete(self, kb_id: str) -> bool:
        """删除知识库"""
        try:
            uuid_id = UUID(kb_id) if isinstance(kb_id, str) else kb_id
            knowledge_base = self.get_by_id(uuid_id)
            
            if not knowledge_base:
                return False
            
            # 删除关联的文档（级联删除）
            self.session.query(DBDocument).filter(
                DBDocument.knowledge_base_id == uuid_id
            ).delete()
            
            self.session.delete(knowledge_base)
            self.session.flush()
            return True
        except (ValueError, TypeError):
            logger.warning(f"Invalid knowledge_base_id format: {kb_id}")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting knowledge base: {str(e)}")
            self.session.rollback()
            raise
    
    def get_document_count(self, kb_id: str) -> int:
        """获取知识库的文档数量"""
        try:
            uuid_id = UUID(kb_id) if isinstance(kb_id, str) else kb_id
            return self.session.query(func.count(DBDocument.id)).filter(
                DBDocument.knowledge_base_id == uuid_id
            ).scalar() or 0
        except (ValueError, TypeError):
            return 0
    
    def get_total_chunks(self, kb_id: str) -> int:
        """获取知识库的总块数"""
        try:
            uuid_id = UUID(kb_id) if isinstance(kb_id, str) else kb_id
            from database.src.models.knowledge_models import DocumentChunk
            
            return self.session.query(func.count(DocumentChunk.id)).join(
                DBDocument, DocumentChunk.document_id == DBDocument.id
            ).filter(
                DBDocument.knowledge_base_id == uuid_id
            ).scalar() or 0
        except (ValueError, TypeError):
            return 0
    
    def get_document_counts_batch(self, kb_ids: List[str]) -> Dict[str, int]:
        """
        批量获取知识库的文档数量（优化N+1查询问题）
        
        Args:
            kb_ids: 知识库ID列表
            
        Returns:
            字典，键为知识库ID，值为文档数量
        """
        if not kb_ids:
            return {}
        
        try:
            # 转换所有ID为UUID
            uuid_ids = []
            id_mapping = {}  # UUID -> 原始字符串ID的映射
            for kb_id_str in kb_ids:
                try:
                    uuid_id = UUID(kb_id_str)
                    uuid_ids.append(uuid_id)
                    id_mapping[uuid_id] = kb_id_str
                except (ValueError, TypeError):
                    logger.warning(f"Invalid knowledge_base_id format: {kb_id_str}")
                    continue
            
            if not uuid_ids:
                return {}
            
            # 批量查询文档数量
            results = self.session.query(
                DBDocument.knowledge_base_id,
                func.count(DBDocument.id).label('count')
            ).filter(
                DBDocument.knowledge_base_id.in_(uuid_ids)
            ).group_by(
                DBDocument.knowledge_base_id
            ).all()
            
            # 构建结果字典
            counts = {}
            for kb_uuid, count in results:
                kb_id_str = id_mapping.get(kb_uuid, str(kb_uuid))
                counts[kb_id_str] = count or 0
            
            # 对于没有文档的知识库，返回0
            for kb_id_str in kb_ids:
                if kb_id_str not in counts:
                    counts[kb_id_str] = 0
            
            return counts
        except Exception as e:
            logger.error(f"Error getting document counts batch: {str(e)}", exc_info=True)
            # 降级：返回空字典，让调用方处理
            return {kb_id: 0 for kb_id in kb_ids}
    
    def get_total_chunks_batch(self, kb_ids: List[str]) -> Dict[str, int]:
        """
        批量获取知识库的总块数（优化N+1查询问题）
        
        Args:
            kb_ids: 知识库ID列表
            
        Returns:
            字典，键为知识库ID，值为总块数
        """
        if not kb_ids:
            return {}
        
        try:
            # 转换所有ID为UUID
            uuid_ids = []
            id_mapping = {}  # UUID -> 原始字符串ID的映射
            for kb_id_str in kb_ids:
                try:
                    uuid_id = UUID(kb_id_str)
                    uuid_ids.append(uuid_id)
                    id_mapping[uuid_id] = kb_id_str
                except (ValueError, TypeError):
                    logger.warning(f"Invalid knowledge_base_id format: {kb_id_str}")
                    continue
            
            if not uuid_ids:
                return {}
            
            from database.src.models.knowledge_models import DocumentChunk
            
            # 批量查询块数
            results = self.session.query(
                DBDocument.knowledge_base_id,
                func.count(DocumentChunk.id).label('count')
            ).join(
                DocumentChunk, DocumentChunk.document_id == DBDocument.id
            ).filter(
                DBDocument.knowledge_base_id.in_(uuid_ids)
            ).group_by(
                DBDocument.knowledge_base_id
            ).all()
            
            # 构建结果字典
            chunks = {}
            for kb_uuid, count in results:
                kb_id_str = id_mapping.get(kb_uuid, str(kb_uuid))
                chunks[kb_id_str] = count or 0
            
            # 对于没有块的知识库，返回0
            for kb_id_str in kb_ids:
                if kb_id_str not in chunks:
                    chunks[kb_id_str] = 0
            
            return chunks
        except Exception as e:
            logger.error(f"Error getting total chunks batch: {str(e)}", exc_info=True)
            # 降级：返回空字典，让调用方处理
            return {kb_id: 0 for kb_id in kb_ids}




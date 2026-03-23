"""
文档Repository
文档元数据数据访问层（适配层）
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.knowledge_models import (
    Document as DBDocument,
    DocumentType,
    DocumentStatus
)
from database.src.repositories.knowledge_repository import (
    DocumentRepository as DBDocumentRepository
)

logger = logging.getLogger(__name__)


class DocumentRepository:
    """文档Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBDocumentRepository(session)
    
    def get_by_id(self, document_id: str) -> Optional[DBDocument]:
        """根据ID获取文档"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid document_id format: {document_id}")
            return None
    
    def get_by_filename(self, filename: str) -> Optional[DBDocument]:
        """根据文件名获取文档"""
        return self._db_repo.get_by_filename(filename)
    
    def create_document(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        uploaded_by: Optional[UUID] = None,
        knowledge_base_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> DBDocument:
        """创建文档记录"""
        try:
            # 转换文件类型
            # 关键：SQLAlchemy的Enum在序列化str Enum时，会使用枚举的value
            # 但我们需要确保传入的是枚举对象，而不是字符串
            db_file_type = None
            try:
                # 先尝试通过值匹配（小写），确保使用正确的枚举值
                db_file_type = DocumentType(file_type.lower())
            except ValueError:
                # 如果值匹配失败，尝试通过名称匹配（大写）
                try:
                    db_file_type = DocumentType[file_type.upper()]
                except KeyError:
                    db_file_type = DocumentType.UNKNOWN
            
            # 关键修复：确保使用枚举的value而不是name
            # 对于str Enum，SQLAlchemy应该自动使用value，但为了保险，我们显式处理
            # 实际上，SQLAlchemy的Enum类型应该正确处理str Enum，问题可能在于数据库枚举定义
            
            # 构建 document_metadata（统一命名）
            # 如果传入了 metadata 和 document_metadata，合并它们
            doc_metadata = metadata or {}
            if document_metadata:
                # 如果 document_metadata 是字典，合并到 doc_metadata
                if isinstance(document_metadata, dict):
                    doc_metadata.update(document_metadata)
                else:
                    doc_metadata['document_metadata'] = document_metadata
            
            document = DBDocument(
                filename=filename,
                file_type=db_file_type,
                file_size=file_size,
                file_path=file_path,
                status=DocumentStatus.UPLOADING,
                uploaded_by=uploaded_by,
                knowledge_base_id=knowledge_base_id,
                version=1,
                tags=tags or [],
                category=category,
                document_metadata=doc_metadata
            )
            self.session.add(document)
            self.session.flush()
            return document
        except SQLAlchemyError as e:
            logger.error(f"Error creating document: {str(e)}")
            self.session.rollback()
            raise
    
    def update_document(
        self,
        document_id: str,
        **updates
    ) -> Optional[DBDocument]:
        """更新文档"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            
            # 处理特殊字段
            if "status" in updates:
                status_str = updates["status"]
                try:
                    updates["status"] = DocumentStatus[status_str.upper()]
                except KeyError:
                    logger.warning(f"Invalid status: {status_str}")
                    del updates["status"]
            
            return self._db_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid document_id format: {document_id}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档（软删除）"""
        try:
            uuid_id = UUID(document_id) if isinstance(document_id, str) else document_id
            document = self._db_repo.get_by_id(uuid_id)
            if document:
                document.status = DocumentStatus.DELETED
                self.session.flush()
                return True
            return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid document_id format: {document_id}")
            return False
    
    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[DBDocument]:
        """列出文档（默认排除已删除的文档）"""
        try:
            filters = {}
            if status:
                try:
                    filters["status"] = DocumentStatus[status.upper()]
                except KeyError:
                    pass
            else:
                # 如果没有指定status，默认排除DELETED状态的文档
                # 使用NOT过滤器排除DELETED状态
                from sqlalchemy import not_
                documents_query = self.session.query(DBDocument)
                if knowledge_base_id:
                    documents_query = documents_query.filter(DBDocument.knowledge_base_id == knowledge_base_id)
                if category:
                    documents_query = documents_query.filter(DBDocument.category == category)
                if uploaded_by:
                    documents_query = documents_query.filter(DBDocument.uploaded_by == uploaded_by)
                
                # 排除DELETED状态的文档
                documents_query = documents_query.filter(DBDocument.status != DocumentStatus.DELETED)
                
                # 应用搜索过滤
                if search:
                    search_lower = search.lower()
                    documents_query = documents_query.filter(
                        DBDocument.filename.ilike(f'%{search_lower}%')
                    )
                
                # 应用分页
                documents = documents_query.offset(skip).limit(limit).all()
                
                # 应用标签过滤（在内存中过滤，因为标签是JSON字段）
                if tags:
                    documents = [
                        doc for doc in documents
                        if doc.tags and any(tag in doc.tags for tag in tags)
                    ]
                
                return documents
            
            if knowledge_base_id:
                filters["knowledge_base_id"] = knowledge_base_id
            
            if category:
                filters["category"] = category
            
            if uploaded_by:
                filters["uploaded_by"] = uploaded_by
            
            documents = self._db_repo.get_all(skip=skip, limit=limit, filters=filters)
            
            # 标签过滤
            if tags:
                documents = [
                    doc for doc in documents
                    if doc.tags and any(tag in doc.tags for tag in tags)
                ]
            
            # 搜索过滤
            if search:
                search_lower = search.lower()
                documents = [
                    doc for doc in documents
                    if search_lower in doc.filename.lower() or
                       (doc.summary and search_lower in doc.summary.lower())
                ]
            
            # 即使指定了status，也要排除DELETED状态的文档（除非明确要求查看DELETED）
            if status and status.upper() != 'DELETED':
                documents = [doc for doc in documents if doc.status != DocumentStatus.DELETED]
            
            return documents
        except SQLAlchemyError as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise
    
    def count_documents(
        self,
        status: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        uploaded_by: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> int:
        """统计文档数量（默认排除已删除的文档）"""
        try:
            from sqlalchemy import func
            count_query = self.session.query(func.count(DBDocument.id))
            
            if status:
                try:
                    status_enum = DocumentStatus[status.upper()]
                    count_query = count_query.filter(DBDocument.status == status_enum)
                except KeyError:
                    pass
            else:
                # 如果没有指定status，默认排除DELETED状态的文档
                count_query = count_query.filter(DBDocument.status != DocumentStatus.DELETED)
            
            if knowledge_base_id:
                count_query = count_query.filter(DBDocument.knowledge_base_id == knowledge_base_id)
            
            if category:
                count_query = count_query.filter(DBDocument.category == category)
            
            if uploaded_by:
                count_query = count_query.filter(DBDocument.uploaded_by == uploaded_by)
            
            if search:
                search_lower = search.lower()
                count_query = count_query.filter(
                    DBDocument.filename.ilike(f'%{search_lower}%')
                )
            
            total = count_query.scalar() or 0
            
            # 如果指定了tags，需要在内存中过滤（因为tags是JSON字段）
            if tags:
                # 获取所有匹配的文档，然后在内存中过滤
                documents = self.list_documents(
                    skip=0,
                    limit=10000,  # 获取足够多的文档
                    status=status,
                    knowledge_base_id=knowledge_base_id,
                    category=category,
                    tags=tags,
                    uploaded_by=uploaded_by,
                    search=search
                )
                return len(documents)
            
            return total
        except SQLAlchemyError as e:
            logger.error(f"Error counting documents: {str(e)}")
            return 0
    
    def update_status(
        self,
        document_id: str,
        status: str
    ) -> bool:
        """更新文档状态"""
        try:
            return self.update_document(document_id, status=status) is not None
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            return False
    
    def increment_version(self, document_id: str) -> Optional[DBDocument]:
        """增加文档版本"""
        try:
            document = self.get_by_id(document_id)
            if document:
                document.version += 1
                self.session.flush()
            return document
        except Exception as e:
            logger.error(f"Error incrementing document version: {str(e)}")
            self.session.rollback()
            return None
    
    def add_tags(self, document_id: str, tags: List[str]) -> bool:
        """添加标签"""
        try:
            document = self.get_by_id(document_id)
            if document:
                if document.tags is None:
                    document.tags = []
                for tag in tags:
                    if tag not in document.tags:
                        document.tags.append(tag)
                self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding tags: {str(e)}")
            self.session.rollback()
            return False
    
    def remove_tags(self, document_id: str, tags: List[str]) -> bool:
        """移除标签"""
        try:
            document = self.get_by_id(document_id)
            if document:
                if document.tags:
                    document.tags = [t for t in document.tags if t not in tags]
                    self.session.flush()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing tags: {str(e)}")
            self.session.rollback()
            return False
    
    def set_category(self, document_id: str, category: str) -> bool:
        """设置文档分类"""
        try:
            return self.update_document(document_id, category=category) is not None
        except Exception as e:
            logger.error(f"Error setting category: {str(e)}")
            return False
    
    def set_quality_score(self, document_id: str, score: float) -> bool:
        """设置质量评分"""
        try:
            return self.update_document(document_id, quality_score=score) is not None
        except Exception as e:
            logger.error(f"Error setting quality score: {str(e)}")
            return False
    
    def set_summary(self, document_id: str, summary: str) -> bool:
        """设置文档摘要"""
        try:
            return self.update_document(document_id, summary=summary) is not None
        except Exception as e:
            logger.error(f"Error setting summary: {str(e)}")
            return False










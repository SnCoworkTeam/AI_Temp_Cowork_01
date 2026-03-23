"""
知识库Repository
文档、向量块、知识图谱管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from ..models.knowledge_models import (
    Document, DocumentChunk, KnowledgeGraphNode, KnowledgeGraphEdge,
    DocumentType, DocumentStatus
)
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository[Document]):
    """文档Repository"""
    
    def __init__(self, session: Session):
        super().__init__(Document, session)
    
    def get_by_filename(self, filename: str) -> Optional[Document]:
        """
        根据文件名获取文档
        
        Args:
            filename: 文件名
            
        Returns:
            文档实例或None
        """
        try:
            return self.session.query(Document).filter(Document.filename == filename).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting document by filename {filename}: {str(e)}")
            raise
    
    def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        根据分类获取文档列表
        
        Args:
            category: 文档分类
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            文档列表
        """
        try:
            return self.session.query(Document).filter(
                Document.category == category,
                Document.status != DocumentStatus.DELETED
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents by category {category}: {str(e)}")
            raise
    
    def get_by_tags(self, tags: List[str], skip: int = 0, limit: int = 100) -> List[Document]:
        """
        根据标签获取文档列表（包含任一标签）
        
        Args:
            tags: 标签列表
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            文档列表
        """
        try:
            # PostgreSQL数组包含查询
            query = self.session.query(Document).filter(
                Document.status != DocumentStatus.DELETED
            )
            
            # 使用ANY或包含操作
            conditions = [Document.tags.contains([tag]) for tag in tags]
            query = query.filter(or_(*conditions))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents by tags: {str(e)}")
            raise
    
    def get_processed_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        获取已处理文档列表
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            已处理文档列表
        """
        try:
            return self.session.query(Document).filter(
                Document.status == DocumentStatus.PROCESSED
            ).order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting processed documents: {str(e)}")
            raise
    
    def get_by_uploader(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        根据上传者获取文档列表
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            文档列表
        """
        try:
            return self.session.query(Document).filter(
                Document.uploaded_by == user_id,
                Document.status != DocumentStatus.DELETED
            ).order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting documents by uploader {user_id}: {str(e)}")
            raise
    
    def search_by_content(self, keyword: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        根据内容关键词搜索文档
        
        Args:
            keyword: 搜索关键词
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            文档列表
        """
        try:
            return self.session.query(Document).filter(
                and_(
                    Document.status != DocumentStatus.DELETED,
                    or_(
                        Document.title.ilike(f"%{keyword}%"),
                        Document.summary.ilike(f"%{keyword}%")
                    )
                )
            ).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching documents by keyword {keyword}: {str(e)}")
            raise


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """文档块Repository"""
    
    def __init__(self, session: Session):
        super().__init__(DocumentChunk, session)
    
    def get_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        """
        根据文档ID获取所有文档块
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档块列表
        """
        try:
            return self.session.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting chunks by document_id {document_id}: {str(e)}")
            raise
    
    def delete_by_document_id(self, document_id: UUID) -> int:
        """
        删除文档的所有块
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除的块数
        """
        try:
            count = self.session.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete(synchronize_session=False)
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error deleting chunks by document_id {document_id}: {str(e)}")
            self.session.rollback()
            raise


class KnowledgeGraphNodeRepository(BaseRepository[KnowledgeGraphNode]):
    """知识图谱节点Repository"""
    
    def __init__(self, session: Session):
        super().__init__(KnowledgeGraphNode, session)
    
    def get_by_concept(self, concept: str) -> Optional[KnowledgeGraphNode]:
        """
        根据概念名称获取节点（使用label字段）
        
        Args:
            concept: 概念名称（实际使用label字段查询）
            
        Returns:
            知识图谱节点实例或None
        """
        try:
            # 模型没有concept字段，使用label字段
            return self.session.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.label == concept
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting node by concept {concept}: {str(e)}")
            raise
    
    def get_related_nodes(self, node_id: UUID, max_depth: int = 1) -> List[KnowledgeGraphNode]:
        """
        获取相关节点（通过边连接）
        
        Args:
            node_id: 节点ID
            max_depth: 最大深度
            
        Returns:
            相关节点列表
        """
        try:
            # 这里简化实现，实际可能需要递归查询
            # 获取直接连接的节点
            edges = self.session.query(KnowledgeGraphEdge).filter(
                or_(
                    KnowledgeGraphEdge.source_node_id == node_id,
                    KnowledgeGraphEdge.target_node_id == node_id
                )
            ).all()
            
            node_ids = set()
            for edge in edges:
                if edge.source_node_id != node_id:
                    node_ids.add(edge.source_node_id)
                if edge.target_node_id != node_id:
                    node_ids.add(edge.target_node_id)
            
            if node_ids:
                return self.session.query(KnowledgeGraphNode).filter(
                    KnowledgeGraphNode.id.in_(node_ids)
                ).all()
            
            return []
        except SQLAlchemyError as e:
            logger.error(f"Error getting related nodes for {node_id}: {str(e)}")
            raise


class KnowledgeGraphEdgeRepository(BaseRepository[KnowledgeGraphEdge]):
    """知识图谱边Repository"""
    
    def __init__(self, session: Session):
        super().__init__(KnowledgeGraphEdge, session)
    
    def get_by_source_node(self, source_node_id: UUID) -> List[KnowledgeGraphEdge]:
        """
        根据源节点获取所有边
        
        Args:
            source_node_id: 源节点ID
            
        Returns:
            边列表
        """
        try:
            return self.session.query(KnowledgeGraphEdge).filter(
                KnowledgeGraphEdge.source_node_id == source_node_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting edges by source_node_id {source_node_id}: {str(e)}")
            raise
    
    def get_by_target_node(self, target_node_id: UUID) -> List[KnowledgeGraphEdge]:
        """
        根据目标节点获取所有边
        
        Args:
            target_node_id: 目标节点ID
            
        Returns:
            边列表
        """
        try:
            return self.session.query(KnowledgeGraphEdge).filter(
                KnowledgeGraphEdge.target_node_id == target_node_id
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting edges by target_node_id {target_node_id}: {str(e)}")
            raise
    
    def get_by_nodes(
        self,
        source_node_id: UUID,
        target_node_id: UUID
    ) -> Optional[KnowledgeGraphEdge]:
        """
        根据源节点和目标节点获取边
        
        Args:
            source_node_id: 源节点ID
            target_node_id: 目标节点ID
            
        Returns:
            边实例或None
        """
        try:
            return self.session.query(KnowledgeGraphEdge).filter(
                and_(
                    KnowledgeGraphEdge.source_node_id == source_node_id,
                    KnowledgeGraphEdge.target_node_id == target_node_id
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting edge between {source_node_id} and {target_node_id}: {str(e)}"
            )
            raise










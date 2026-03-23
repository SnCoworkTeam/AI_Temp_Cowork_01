"""
搜索服务
搜索业务逻辑层（集成数据库）
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
import time

from ..repositories.search_history_repository import (
    SearchHistoryRepository,
    SearchFeedbackRepository
)
from ..core.embedding_manager import get_embedding_manager
from ..core.vector_store import get_vector_store
from ..repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务（集成数据库）"""
    
    def __init__(self, db: Session):
        self.db = db
        self.search_history_repo = SearchHistoryRepository(db)
        self.feedback_repo = SearchFeedbackRepository(db)
        self.document_repo = DocumentRepository(db)
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            min_score: 最小相似度分数
            filters: 过滤条件
            document_ids: 文档ID过滤
            user_id: 用户ID
        
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        
        try:
            # 生成查询向量
            embedding_manager = get_embedding_manager()
            query_embedding = embedding_manager.encode_single(query)
            
            # 构建过滤条件
            search_filters = {}
            if document_ids:
                search_filters['document_id'] = document_ids[0] if len(document_ids) == 1 else None
            
            if filters:
                search_filters.update(filters)
            
            # 在向量存储中搜索
            vector_store = get_vector_store()
            results = vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=search_filters if search_filters else None
            )
            
            # 过滤和格式化结果
            filtered_results = []
            result_document_ids = []
            
            for result in results:
                score = result.get('score', 0.0)
                if score < min_score:
                    continue
                
                doc_id = result.get('metadata', {}).get('document_id', '')
                # 确保doc_id是字符串
                doc_id_str = str(doc_id) if doc_id else ''
                
                # 检查document_ids过滤（确保类型一致）
                if document_ids:
                    # 将document_ids也转换为字符串列表进行比较
                    document_ids_str = [str(did) for did in document_ids]
                    if doc_id_str not in document_ids_str:
                        continue
                
                # 获取文档信息
                # 确保doc_id是字符串格式
                doc_id_str = str(doc_id) if doc_id else ''
                if not doc_id_str:
                    continue
                
                db_document = self.document_repo.get_by_id(doc_id_str)
                if not db_document:
                    continue
                
                filtered_results.append({
                    "chunk_id": result.get('id', ''),
                    "document_id": doc_id_str,
                    "document_name": db_document.filename,
                    "content": result.get('content', ''),
                    "score": score,
                    "metadata": result.get('metadata', {}),
                    "chunk_metadata": {
                        "chunk_index": result.get('metadata', {}).get('chunk_index', 0),
                        **result.get('metadata', {})
                    }
                })
                
                if doc_id_str not in result_document_ids:
                    result_document_ids.append(doc_id_str)
            
            execution_time = time.time() - start_time
            
            # 记录搜索历史（如果失败不影响搜索结果）
            search_id = None
            try:
                search_history = self.search_history_repo.create_search_history(
                    user_id=user_id,
                    query=query,
                    search_type="semantic",
                    results_count=len(filtered_results),
                    result_document_ids=result_document_ids,
                    execution_time=execution_time,
                    filters=filters,
                    metadata={"top_k": top_k, "min_score": min_score}
                )
                self.db.commit()
                search_id = search_history.get("search_id")
            except Exception as e:
                logger.warning(f"Failed to create search history (non-critical): {str(e)}")
                self.db.rollback()
                # 继续返回搜索结果，即使历史记录失败
            
            return {
                "query": query,
                "results": filtered_results,
                "total": len(filtered_results),
                "execution_time": execution_time,
                "search_id": search_id
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        关键词搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 过滤条件
            document_ids: 文档ID过滤
            user_id: 用户ID
        
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        
        try:
            # 从数据库搜索文档（基于文件名、摘要等）
            documents = self.document_repo.list_documents(
                skip=0,
                limit=top_k * 2,  # 获取更多用于过滤
                search=query,
                status="processed"
            )
            
            # 在文档块中搜索关键词
            from ..repositories.chunk_repository import ChunkRepository
            chunk_repo = ChunkRepository(self.db)
            
            results = []
            result_document_ids = []
            
            for doc in documents:
                doc_id_str = str(doc.id)
                # 检查document_ids过滤（确保类型一致）
                if document_ids:
                    document_ids_str = [str(did) for did in document_ids]
                    if doc_id_str not in document_ids_str:
                        continue
                
                # 搜索文档块
                chunks = chunk_repo.get_by_document_id(str(doc.id))
                for chunk in chunks:
                    if query.lower() in chunk.content.lower():
                        results.append({
                            "chunk_id": str(chunk.id),
                            "document_id": str(doc.id),
                            "document_name": doc.filename,
                            "content": chunk.content,
                            "score": 1.0,  # 关键词匹配给固定分数
                            "metadata": chunk.metadata or {},
                            "chunk_metadata": {
                                "chunk_index": chunk.chunk_index,
                                "start_char": chunk.start_char,
                                "end_char": chunk.end_char,
                                "page_number": chunk.page_number
                            }
                        })
                        
                        if str(doc.id) not in result_document_ids:
                            result_document_ids.append(str(doc.id))
                        
                        if len(results) >= top_k:
                            break
                
                if len(results) >= top_k:
                    break
            
            execution_time = time.time() - start_time
            
            # 记录搜索历史（如果失败不影响搜索结果）
            search_id = None
            try:
                search_history = self.search_history_repo.create_search_history(
                    user_id=user_id,
                    query=query,
                    search_type="keyword",
                    results_count=len(results),
                    result_document_ids=result_document_ids,
                    execution_time=execution_time,
                    filters=filters
                )
                self.db.commit()
                search_id = search_history.get("search_id")
            except Exception as e:
                logger.warning(f"Failed to create search history (non-critical): {str(e)}")
                self.db.rollback()
                # 继续返回搜索结果，即使历史记录失败
            
            return {
                "query": query,
                "results": results[:top_k],
                "total": len(results),
                "execution_time": execution_time,
                "search_id": search_id
            }
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def submit_feedback(
        self,
        search_id: str,
        user_id: Optional[str],
        feedback_type: str,
        document_id: Optional[str] = None,
        relevance_score: Optional[int] = None,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """提交搜索反馈"""
        try:
            feedback = self.feedback_repo.create_feedback(
                search_id=search_id,
                user_id=user_id,
                feedback_type=feedback_type,
                document_id=document_id,
                relevance_score=relevance_score,
                comment=comment
            )
            self.db.commit()
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}", exc_info=True)
            self.db.rollback()
            raise
    
    async def get_search_history(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取搜索历史"""
        try:
            skip = (page - 1) * page_size
            history = self.search_history_repo.get_search_history(
                user_id=user_id,
                skip=skip,
                limit=page_size
            )
            
            return {
                "history": history,
                "page": page,
                "page_size": page_size,
                "total": len(history)
            }
            
        except Exception as e:
            logger.error(f"Error getting search history: {str(e)}", exc_info=True)
            return {
                "history": [],
                "page": page,
                "page_size": page_size,
                "total": 0
            }
    
    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门搜索查询"""
        try:
            return self.search_history_repo.get_popular_queries(limit=limit)
        except Exception as e:
            logger.error(f"Error getting popular queries: {str(e)}", exc_info=True)
            return []










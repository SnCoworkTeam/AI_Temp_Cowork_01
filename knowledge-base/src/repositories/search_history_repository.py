"""
搜索历史Repository
搜索历史、用户行为、反馈数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)

# 注意：这些表需要在数据库迁移中创建
# 这里提供Repository接口，实际表结构需要在migration中定义


class SearchHistoryRepository:
    """搜索历史Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_search_history(
        self,
        user_id: Optional[str],
        query: str,
        search_type: str,
        results_count: int,
        result_document_ids: List[str],
        execution_time: float,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建搜索历史记录
        
        注意：如果数据库中没有search_history表，会使用AuditLog表存储
        """
        try:
            # 使用AuditLog表存储搜索历史（如果没有专门的表）
            from database.src.models.system_models import AuditLog, AuditAction
            import json
            
            user_uuid = None
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    pass
            
            # 确保所有数据都是可序列化的
            # 1. 处理result_document_ids，确保都是字符串
            serializable_doc_ids = []
            for doc_id in result_document_ids:
                if doc_id is not None:
                    # 如果是UUID对象，转换为字符串
                    if isinstance(doc_id, UUID):
                        serializable_doc_ids.append(str(doc_id))
                    else:
                        serializable_doc_ids.append(str(doc_id))
            
            # 2. 处理filters，确保所有值都是可序列化的
            serializable_filters = {}
            if filters:
                for key, value in filters.items():
                    if value is None:
                        serializable_filters[str(key)] = None
                    elif isinstance(value, (str, int, float, bool)):
                        serializable_filters[str(key)] = value
                    elif isinstance(value, (list, tuple)):
                        serializable_filters[str(key)] = [
                            str(item) if not isinstance(item, (str, int, float, bool, type(None))) else item
                            for item in value
                        ]
                    elif isinstance(value, dict):
                        serializable_filters[str(key)] = {
                            str(k): str(v) if not isinstance(v, (str, int, float, bool, type(None), dict, list)) else v
                            for k, v in value.items()
                        }
                    else:
                        serializable_filters[str(key)] = str(value)
            
            # 3. 处理metadata，确保所有值都是可序列化的
            serializable_metadata = {}
            if metadata:
                for key, value in metadata.items():
                    if value is None:
                        serializable_metadata[str(key)] = None
                    elif isinstance(value, (str, int, float, bool)):
                        serializable_metadata[str(key)] = value
                    elif isinstance(value, (list, tuple)):
                        serializable_metadata[str(key)] = [
                            str(item) if not isinstance(item, (str, int, float, bool, type(None))) else item
                            for item in value
                        ]
                    elif isinstance(value, dict):
                        serializable_metadata[str(key)] = {
                            str(k): str(v) if not isinstance(v, (str, int, float, bool, type(None), dict, list)) else v
                            for k, v in value.items()
                        }
                    else:
                        serializable_metadata[str(key)] = str(value)
            
            # 4. 构建details_dict
            details_dict = {
                "query": str(query),
                "search_type": str(search_type),
                "results_count": int(results_count),
                "result_document_ids": serializable_doc_ids,
                "execution_time": float(execution_time),
                "filters": serializable_filters
            }
            if serializable_metadata:
                details_dict.update(serializable_metadata)
            
            # 5. 验证JSON可序列化（额外安全检查）
            try:
                json.dumps(details_dict)
            except (TypeError, ValueError) as e:
                logger.warning(f"Details dict contains non-serializable data: {e}, converting all to strings")
                # 如果还有问题，将所有值转换为字符串
                details_dict = {str(k): str(v) for k, v in details_dict.items()}
            
            audit_log = AuditLog(
                user_id=user_uuid,
                action=AuditAction.READ.value,  # 使用.value获取枚举值（小写字符串）
                resource_type="search",
                resource_id=None,  # resource_id是String类型
                details=details_dict,
                ip_address=None,
                user_agent=None,
                timestamp=datetime.utcnow()
            )
            self.session.add(audit_log)
            self.session.flush()
            
            return {
                "search_id": str(audit_log.id),
                "user_id": user_id,
                "query": query,
                "search_type": search_type,
                "results_count": results_count,
                "created_at": audit_log.created_at.isoformat() if audit_log.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error creating search history: {str(e)}", exc_info=True)
            self.session.rollback()
            raise
    
    def get_search_history(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取搜索历史"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            query = self.session.query(AuditLog).filter(
                and_(
                    AuditLog.action == AuditAction.READ.value,
                    AuditLog.resource_type == "search"
                )
            )
            
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                    query = query.filter(AuditLog.user_id == user_uuid)
                except ValueError:
                    pass
            
            logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
            
            results = []
            for log in logs:
                details = log.details or {}
                results.append({
                    "search_id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "query": details.get("query", ""),
                    "search_type": details.get("search_type", "unknown"),
                    "results_count": details.get("results_count", 0),
                    "execution_time": details.get("execution_time", 0.0),
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting search history: {str(e)}")
            return []
    
    def get_popular_queries(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取热门搜索查询"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            query = self.session.query(AuditLog).filter(
                and_(
                    AuditLog.action == AuditAction.READ.value,
                    AuditLog.resource_type == "search"
                )
            )
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            logs = query.all()
            
            # 统计查询频率
            query_counts = {}
            for log in logs:
                details = log.details or {}
                search_query = details.get("query", "")
                if search_query:
                    query_counts[search_query] = query_counts.get(search_query, 0) + 1
            
            # 排序并返回前N个
            popular = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [
                {
                    "query": q,
                    "count": count
                }
                for q, count in popular
            ]
            
        except Exception as e:
            logger.error(f"Error getting popular queries: {str(e)}")
            return []


class UserBehaviorRepository:
    """用户行为Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_behavior(
        self,
        user_id: Optional[str],
        action_type: str,
        target_type: str,
        target_id: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建用户行为记录"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            user_uuid = None
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    pass
            
            # 映射action_type到AuditAction枚举值（使用.value获取小写字符串值）
            audit_action = AuditAction.READ.value
            if action_type == "download":
                audit_action = AuditAction.READ.value
            elif action_type == "delete":
                audit_action = AuditAction.DELETE.value
            elif action_type == "update":
                audit_action = AuditAction.UPDATE.value
            elif action_type == "create":
                audit_action = AuditAction.CREATE.value
            
            details_dict = {
                "action_type": action_type,
                "context": context or {}
            }
            if metadata:
                details_dict.update(metadata)
            
            audit_log = AuditLog(
                user_id=user_uuid,
                action=audit_action,  # 使用枚举值（小写字符串）
                resource_type=target_type,
                resource_id=target_id,  # resource_id是String类型
                details=details_dict,
                ip_address=None,
                user_agent=None,
                timestamp=datetime.utcnow()
            )
            self.session.add(audit_log)
            self.session.flush()
            
            return {
                "behavior_id": str(audit_log.id),
                "user_id": user_id,
                "action_type": action_type,
                "target_type": target_type,
                "target_id": target_id,
                "created_at": audit_log.created_at.isoformat() if audit_log.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error creating behavior: {str(e)}")
            self.session.rollback()
            raise
    
    def get_user_behaviors(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取用户行为列表"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            query = self.session.query(AuditLog)
            
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                    query = query.filter(AuditLog.user_id == user_uuid)
                except ValueError:
                    pass
            
            if target_type:
                query = query.filter(AuditLog.resource_type == target_type)
            
            logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
            
            results = []
            for log in logs:
                details = log.details or {}
                action_type_value = details.get("action_type") or log.action.value
                
                if action_type and action_type_value != action_type:
                    continue
                
                results.append({
                    "behavior_id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action_type": action_type_value,
                    "target_type": log.resource_type,
                    "target_id": str(log.resource_id) if log.resource_id else None,
                    "context": details.get("context", {}),
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user behaviors: {str(e)}")
            return []
    
    def get_document_view_stats(
        self,
        document_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取文档查看统计"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            query = self.session.query(AuditLog).filter(
                and_(
                    AuditLog.action == AuditAction.READ.value,
                    AuditLog.resource_type == "document",
                    AuditLog.resource_id == document_id
                )
            )
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            logs = query.all()
            
            # 统计唯一用户
            unique_users = set()
            for log in logs:
                if log.user_id:
                    unique_users.add(str(log.user_id))
            
            return {
                "document_id": document_id,
                "total_views": len(logs),
                "unique_users": len(unique_users),
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting document view stats: {str(e)}")
            return {
                "document_id": document_id,
                "total_views": 0,
                "unique_users": 0
            }


class SearchFeedbackRepository:
    """搜索反馈Repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_feedback(
        self,
        search_id: str,
        user_id: Optional[str],
        feedback_type: str,
        document_id: Optional[str] = None,
        relevance_score: Optional[int] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建搜索反馈"""
        try:
            # 使用AuditLog表存储反馈（在details中）
            from database.src.models.system_models import AuditLog, AuditAction
            
            user_uuid = None
            if user_id:
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    pass
            
            doc_uuid = None
            if document_id:
                try:
                    doc_uuid = UUID(document_id)
                except ValueError:
                    pass
            
            details_dict = {
                "search_id": search_id,
                "feedback_type": feedback_type,
                "relevance_score": relevance_score,
                "comment": comment
            }
            if metadata:
                details_dict.update(metadata)
            
            audit_log = AuditLog(
                user_id=user_uuid,
                action=AuditAction.READ.value,  # 使用.value获取枚举值（小写字符串）
                resource_type="search_feedback",
                resource_id=document_id,  # resource_id是String类型
                details=details_dict,
                ip_address=None,
                user_agent=None,
                timestamp=datetime.utcnow()
            )
            self.session.add(audit_log)
            self.session.flush()
            
            return {
                "feedback_id": str(audit_log.id),
                "search_id": search_id,
                "user_id": user_id,
                "feedback_type": feedback_type,
                "document_id": document_id,
                "relevance_score": relevance_score,
                "created_at": audit_log.created_at.isoformat() if audit_log.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            self.session.rollback()
            raise
    
    def get_feedback_by_search(
        self,
        search_id: str
    ) -> List[Dict[str, Any]]:
        """获取搜索的反馈"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            logs = self.session.query(AuditLog).filter(
                and_(
                    AuditLog.action == AuditAction.READ.value,
                    AuditLog.resource_type == "search_feedback"
                )
            ).all()
            
            results = []
            for log in logs:
                details = log.details or {}
                if details.get("search_id") == search_id:
                    results.append({
                        "feedback_id": str(log.id),
                        "search_id": search_id,
                        "user_id": str(log.user_id) if log.user_id else None,
                        "feedback_type": details.get("feedback_type", "neutral"),
                        "document_id": str(log.resource_id) if log.resource_id else None,
                        "relevance_score": details.get("relevance_score"),
                        "comment": details.get("comment"),
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting feedback by search: {str(e)}")
            return []
    
    def get_feedback_stats(
        self,
        document_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取反馈统计"""
        try:
            from database.src.models.system_models import AuditLog, AuditAction
            
            query = self.session.query(AuditLog).filter(
                and_(
                    AuditLog.action == AuditAction.READ.value,
                    AuditLog.resource_type == "search_feedback"
                )
            )
            
            if document_id:
                query = query.filter(AuditLog.resource_id == document_id)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            logs = query.all()
            
            # 统计反馈类型
            feedback_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total_score = 0
            score_count = 0
            
            for log in logs:
                details = log.details or {}
                feedback_type = details.get("feedback_type", "neutral")
                feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
                
                relevance_score = details.get("relevance_score")
                if relevance_score:
                    total_score += relevance_score
                    score_count += 1
            
            avg_score = total_score / score_count if score_count > 0 else 0.0
            
            return {
                "total_feedback": len(logs),
                "feedback_counts": feedback_counts,
                "average_relevance_score": avg_score,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "total_feedback": 0,
                "feedback_counts": {"positive": 0, "negative": 0, "neutral": 0},
                "average_relevance_score": 0.0
            }


"""
反馈服务
处理用户反馈（👍/👎）和质量监控
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import sys
import os

logger = logging.getLogger(__name__)

# 添加database模块到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../database/src'))

# 使用database模块的模型
Feedback = None
QueryLog = None

try:
    import sys
    import os
    # 添加database模块到路径
    database_path = os.path.join(os.path.dirname(__file__), '../../../../database/src')
    if database_path not in sys.path:
        sys.path.insert(0, database_path)
    from models.feedback import Feedback, QueryLog
    logger.info("Successfully imported Feedback models from database module")
except ImportError as e:
    logger.warning(f"Failed to import Feedback models from database module: {e}")
    # 如果导入失败，使用内联定义（临时方案）
    from sqlalchemy import Column, Integer, String, DateTime, Text
    from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class Feedback(Base):
        """反馈数据模型"""
        __tablename__ = "user_feedback"
        
        id = Column(Integer, primary_key=True, index=True)
        query_id = Column(String(255), nullable=False, index=True)
        query = Column(Text, nullable=False)
        feedback_type = Column(String(20), nullable=False)
        result_id = Column(String(255), nullable=True)
        comment = Column(Text, nullable=True)
        user_id = Column(String(255), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        extra_metadata = Column(PGJSONB, nullable=True)  # 重命名为extra_metadata避免与SQLAlchemy保留字冲突
    
    class QueryLog(Base):
        """查询日志数据模型"""
        __tablename__ = "query_logs"
        
        id = Column(Integer, primary_key=True, index=True)
        query_id = Column(String(255), nullable=False, index=True)
        query = Column(Text, nullable=False)
        success = Column(String(10), nullable=False)
        response_time_ms = Column(Integer, nullable=True)
        result_count = Column(Integer, nullable=True)
        user_id = Column(String(255), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        extra_metadata = Column(PGJSONB, nullable=True)  # 重命名为extra_metadata避免与SQLAlchemy保留字冲突


class FeedbackService:
    """反馈服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def submit_feedback(
        self,
        query_id: str,
        feedback_type: str,  # "positive" or "negative"
        query: str,
        result_id: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        提交用户反馈
        
        Args:
            query_id: 查询ID
            feedback_type: 反馈类型（positive/negative）
            query: 查询内容
            result_id: 结果ID（可选）
            comment: 反馈评论（可选）
            user_id: 用户ID（可选）
            metadata: 额外元数据（可选）
        
        Returns:
            反馈提交结果
        """
        try:
            feedback = Feedback(
                query_id=query_id,
                query=query,
                feedback_type=feedback_type,
                result_id=result_id,
                comment=comment,
                user_id=user_id,
                extra_metadata=metadata,  # 使用extra_metadata字段
                created_at=datetime.utcnow()
            )
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            
            logger.info(f"Feedback submitted: {query_id}, type: {feedback_type}")
            
            return {
                "success": True,
                "feedback_id": feedback.id,
                "message": "Feedback submitted successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to submit feedback: {e}", exc_info=True)
            raise
    
    async def get_feedback_stats(self, time_range: str = "7d") -> Dict[str, Any]:
        """
        获取反馈统计
        
        Args:
            time_range: 时间范围（7d, 30d, 90d, all）
        
        Returns:
            反馈统计信息
        """
        try:
            # 计算时间范围
            if time_range == "7d":
                start_time = datetime.utcnow() - timedelta(days=7)
            elif time_range == "30d":
                start_time = datetime.utcnow() - timedelta(days=30)
            elif time_range == "90d":
                start_time = datetime.utcnow() - timedelta(days=90)
            else:
                start_time = None
            
            # 查询反馈
            query = self.db.query(Feedback)
            if start_time:
                query = query.filter(Feedback.created_at >= start_time)
            
            all_feedback = query.all()
            
            # 统计
            total = len(all_feedback)
            positive = len([f for f in all_feedback if f.feedback_type == "positive"])
            negative = len([f for f in all_feedback if f.feedback_type == "negative"])
            satisfaction_rate = (positive / total * 100) if total > 0 else 0.0
            
            return {
                "success": True,
                "time_range": time_range,
                "total_feedback": total,
                "positive_feedback": positive,
                "negative_feedback": negative,
                "satisfaction_rate": round(satisfaction_rate, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
            raise
    
    async def log_query(
        self,
        query_id: str,
        query: str,
        success: bool,
        response_time_ms: Optional[int] = None,
        result_count: Optional[int] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录查询日志（用于质量监控）
        
        Args:
            query_id: 查询ID
            query: 查询内容
            success: 是否成功
            response_time_ms: 响应时间（毫秒）
            result_count: 结果数量
            user_id: 用户ID
            metadata: 额外元数据
        """
        try:
            query_log = QueryLog(
                query_id=query_id,
                query=query,
                success="true" if success else "false",
                response_time_ms=response_time_ms,
                result_count=result_count,
                user_id=user_id,
                extra_metadata=metadata,  # 使用extra_metadata字段
                created_at=datetime.utcnow()
            )
            self.db.add(query_log)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log query: {e}", exc_info=True)
    
    async def get_quality_stats(self, time_range: str = "7d") -> Dict[str, Any]:
        """
        获取质量统计（问答成功率、用户满意度）
        
        Args:
            time_range: 时间范围
        
        Returns:
            质量统计信息
        """
        try:
            # 计算时间范围
            if time_range == "7d":
                start_time = datetime.utcnow() - timedelta(days=7)
            elif time_range == "30d":
                start_time = datetime.utcnow() - timedelta(days=30)
            elif time_range == "90d":
                start_time = datetime.utcnow() - timedelta(days=90)
            else:
                start_time = None
            
            # 查询日志
            query = self.db.query(QueryLog)
            if start_time:
                query = query.filter(QueryLog.created_at >= start_time)
            
            all_logs = query.all()
            
            # 统计
            total_queries = len(all_logs)
            successful_queries = len([log for log in all_logs if log.success == "true"])
            success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0.0
            
            # 平均响应时间
            response_times = [log.response_time_ms for log in all_logs if log.response_time_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # 获取满意度（从反馈统计）
            feedback_stats = await self.get_feedback_stats(time_range)
            satisfaction_rate = feedback_stats.get("satisfaction_rate", 0.0)
            
            return {
                "success": True,
                "time_range": time_range,
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "satisfaction_rate": satisfaction_rate
            }
        except Exception as e:
            logger.error(f"Failed to get quality stats: {e}", exc_info=True)
            raise


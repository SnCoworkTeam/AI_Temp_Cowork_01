"""
价值指标服务
收集和统计系统价值指标（时间节省、错误减少等）
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class ValueMetric(Base):
    """价值指标数据模型"""
    __tablename__ = "value_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String(100), nullable=False, index=True)  # 操作类型
    time_saved_seconds = Column(Float, nullable=True)  # 节省时间（秒）
    error_reduced = Column(Integer, nullable=True)  # 减少错误数
    efficiency_improvement = Column(Float, nullable=True)  # 效率提升（百分比）
    user_id = Column(String(255), nullable=True, index=True)
    extra_metadata = Column(PGJSONB, nullable=True)  # 重命名为extra_metadata避免与SQLAlchemy保留字冲突
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ValueMetricsService:
    """价值指标服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def record_operation_time(
        self,
        operation: str,
        time_saved: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录操作时间节省
        
        Args:
            operation: 操作类型（如"purchase_order_query", "document_search"）
            time_saved: 节省时间（秒）
            user_id: 用户ID（可选）
            metadata: 额外元数据（可选）
        
        Returns:
            记录结果
        """
        try:
            metric = ValueMetric(
                operation=operation,
                time_saved_seconds=time_saved,
                user_id=user_id,
                extra_metadata=metadata,  # 使用extra_metadata字段
                created_at=datetime.utcnow()
            )
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(f"Recorded operation time: {operation}, time_saved: {time_saved}s")
            
            return {
                "success": True,
                "metric_id": metric.id,
                "message": "Operation time recorded successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record operation time: {e}", exc_info=True)
            raise
    
    async def record_error_reduction(
        self,
        operation: str,
        error_reduced: int,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录错误减少
        
        Args:
            operation: 操作类型
            error_reduced: 减少错误数
            user_id: 用户ID（可选）
            metadata: 额外元数据（可选）
        
        Returns:
            记录结果
        """
        try:
            metric = ValueMetric(
                operation=operation,
                error_reduced=error_reduced,
                user_id=user_id,
                extra_metadata=metadata,  # 使用extra_metadata字段
                created_at=datetime.utcnow()
            )
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            
            logger.info(f"Recorded error reduction: {operation}, error_reduced: {error_reduced}")
            
            return {
                "success": True,
                "metric_id": metric.id,
                "message": "Error reduction recorded successfully"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record error reduction: {e}", exc_info=True)
            raise
    
    async def get_time_savings(self, time_range: str = "7d", operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取时间节省统计
        
        Args:
            time_range: 时间范围（7d, 30d, 90d, all）
            operation: 操作类型过滤（可选）
        
        Returns:
            时间节省统计信息
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
            
            # 查询指标
            query = self.db.query(ValueMetric).filter(ValueMetric.time_saved_seconds.isnot(None))
            if start_time:
                query = query.filter(ValueMetric.created_at >= start_time)
            if operation:
                query = query.filter(ValueMetric.operation == operation)
            
            metrics = query.all()
            
            # 统计
            total_time_saved = sum(m.time_saved_seconds for m in metrics if m.time_saved_seconds)
            avg_time_saved = total_time_saved / len(metrics) if metrics else 0
            operation_stats = {}
            
            for metric in metrics:
                op = metric.operation
                if op not in operation_stats:
                    operation_stats[op] = {
                        "count": 0,
                        "total_time_saved": 0,
                        "avg_time_saved": 0
                    }
                operation_stats[op]["count"] += 1
                if metric.time_saved_seconds:
                    operation_stats[op]["total_time_saved"] += metric.time_saved_seconds
            
            # 计算平均值
            for op in operation_stats:
                stats = operation_stats[op]
                stats["avg_time_saved"] = stats["total_time_saved"] / stats["count"] if stats["count"] > 0 else 0
            
            return {
                "success": True,
                "time_range": time_range,
                "total_operations": len(metrics),
                "total_time_saved_seconds": round(total_time_saved, 2),
                "total_time_saved_hours": round(total_time_saved / 3600, 2),
                "avg_time_saved_seconds": round(avg_time_saved, 2),
                "operation_stats": operation_stats
            }
        except Exception as e:
            logger.error(f"Failed to get time savings: {e}", exc_info=True)
            raise
    
    async def get_error_reduction(self, time_range: str = "7d", operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取错误减少统计
        
        Args:
            time_range: 时间范围
            operation: 操作类型过滤（可选）
        
        Returns:
            错误减少统计信息
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
            
            # 查询指标
            query = self.db.query(ValueMetric).filter(ValueMetric.error_reduced.isnot(None))
            if start_time:
                query = query.filter(ValueMetric.created_at >= start_time)
            if operation:
                query = query.filter(ValueMetric.operation == operation)
            
            metrics = query.all()
            
            # 统计
            total_errors_reduced = sum(m.error_reduced for m in metrics if m.error_reduced)
            avg_errors_reduced = total_errors_reduced / len(metrics) if metrics else 0
            
            return {
                "success": True,
                "time_range": time_range,
                "total_operations": len(metrics),
                "total_errors_reduced": total_errors_reduced,
                "avg_errors_reduced": round(avg_errors_reduced, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get error reduction: {e}", exc_info=True)
            raise


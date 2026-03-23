"""
系统Repository
系统配置和审计日志管理
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime

from ..models.system_models import SystemConfig, AuditLog, AuditAction
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SystemConfigRepository(BaseRepository[SystemConfig]):
    """系统配置Repository"""
    
    def __init__(self, session: Session):
        super().__init__(SystemConfig, session)
    
    def get_by_key(self, key: str) -> Optional[SystemConfig]:
        """
        根据配置键获取配置
        
        Args:
            key: 配置键
            
        Returns:
            配置实例或None
        """
        try:
            return self.session.query(SystemConfig).filter(SystemConfig.key == key).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting config by key {key}: {str(e)}")
            raise
    
    def get_by_category(self, category: str) -> List[SystemConfig]:
        """
        根据分类获取配置列表
        
        Args:
            category: 配置分类
            
        Returns:
            配置列表
        """
        try:
            return self.session.query(SystemConfig).filter(
                SystemConfig.category == category
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting configs by category {category}: {str(e)}")
            raise
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.get_by_key(key)
        if config:
            return config.value
        return default
    
    def set_value(self, key: str, value: Any, description: Optional[str] = None) -> SystemConfig:
        """
        设置配置值（如果不存在则创建）
        
        Args:
            key: 配置键
            value: 配置值
            description: 配置描述
            
        Returns:
            配置实例
        """
        try:
            config = self.get_by_key(key)
            if config:
                config.value = value
                if description:
                    config.description = description
            else:
                config = SystemConfig(
                    key=key,
                    value=value,
                    description=description or ""
                )
                self.session.add(config)
            
            self.session.flush()
            return config
        except SQLAlchemyError as e:
            logger.error(f"Error setting config {key}: {str(e)}")
            self.session.rollback()
            raise


class AuditLogRepository(BaseRepository[AuditLog]):
    """审计日志Repository"""
    
    def __init__(self, session: Session):
        super().__init__(AuditLog, session)
    
    def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        根据用户ID获取审计日志
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            审计日志列表
        """
        try:
            return self.session.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting audit logs by user_id {user_id}: {str(e)}")
            raise
    
    def get_by_action(
        self,
        action: AuditAction,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        根据操作类型获取审计日志
        
        Args:
            action: 操作类型
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            审计日志列表
        """
        try:
            return self.session.query(AuditLog).filter(
                AuditLog.action == action
            ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting audit logs by action {action}: {str(e)}")
            raise
    
    def get_by_resource(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        根据资源类型和ID获取审计日志
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID（可选，字符串类型）
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            审计日志列表
        """
        try:
            query = self.session.query(AuditLog).filter(
                AuditLog.resource_type == resource_type
            )
            
            if resource_id:
                query = query.filter(AuditLog.resource_id == str(resource_id))
            
            return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting audit logs by resource {resource_type}/{resource_id}: {str(e)}"
            )
            raise
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        根据日期范围获取审计日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            审计日志列表
        """
        try:
            return self.session.query(AuditLog).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting audit logs by date range: {str(e)}")
            raise
    
    def create_log(
        self,
        user_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> AuditLog:
        """
        创建审计日志
        
        Args:
            user_id: 用户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID（字符串类型）
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            timestamp: 操作时间（可选，默认当前时间）
            
        Returns:
            审计日志实例
        """
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=timestamp or datetime.utcnow()
            )
            self.session.add(log)
            self.session.flush()
            return log
        except SQLAlchemyError as e:
            logger.error(f"Error creating audit log: {str(e)}")
            self.session.rollback()
            raise


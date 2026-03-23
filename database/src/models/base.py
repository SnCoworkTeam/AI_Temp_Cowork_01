"""
基础数据模型
提供通用字段和功能
"""
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from datetime import datetime
from typing import Any, Dict

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    
    # 允许 SQLAlchemy 2.0 忽略旧式类型注解
    __allow_unmapped__ = True
    
    @declared_attr
    def created_at(cls):
        """创建时间"""
        return Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    
    @declared_attr
    def updated_at(cls):
        """更新时间"""
        return Column(
            DateTime,
            default=func.now(),
            onupdate=func.now(),
            nullable=False,
            comment="更新时间"
        )


class BaseModel(Base, TimestampMixin):
    """基础模型类"""
    
    __abstract__ = True
    __allow_unmapped__ = True  # 允许 SQLAlchemy 2.0 忽略旧式类型注解
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]):
        """
        从字典更新模型
        
        Args:
            data: 字典数据
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)



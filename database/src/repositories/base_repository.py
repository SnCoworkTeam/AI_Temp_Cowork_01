"""
基础Repository类
提供通用的CRUD操作
"""
import logging
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from ..models.base import BaseModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """基础Repository类"""
    
    def __init__(self, model: Type[ModelType], session: Session):
        """
        初始化Repository
        
        Args:
            model: SQLAlchemy模型类
            session: 数据库会话
        """
        self.model = model
        self.session = session
    
    def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        try:
            return self.session.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {str(e)}")
            raise
    
    def get_by_ids(self, ids: List[UUID]) -> List[ModelType]:
        """
        根据ID列表获取记录
        
        Args:
            ids: 记录ID列表
            
        Returns:
            模型实例列表
        """
        try:
            return self.session.query(self.model).filter(self.model.id.in_(ids)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ids: {str(e)}")
            raise
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        获取所有记录（支持分页、筛选、排序）
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数
            filters: 筛选条件字典
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            模型实例列表
        """
        try:
            query = self.session.query(self.model)
            
            # 应用筛选条件
            if filters:
                query = self._apply_filters(query, filters)
            
            # 应用排序
            if order_by:
                order_column = getattr(self.model, order_by, None)
                if order_column:
                    if order_desc:
                        query = query.order_by(order_column.desc())
                    else:
                        query = query.order_by(order_column.asc())
            
            # 应用分页
            if limit > 0:
                query = query.offset(skip).limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数
        
        Args:
            filters: 筛选条件字典
            
        Returns:
            记录总数
        """
        try:
            query = self.session.query(func.count(self.model.id))
            
            if filters:
                query = self._apply_filters(query, filters)
            
            return query.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise
    
    def create(self, **kwargs) -> ModelType:
        """
        创建新记录
        
        Args:
            **kwargs: 模型字段
            
        Returns:
            创建的模型实例
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            self.session.flush()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            self.session.rollback()
            raise
    
    def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 记录ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的模型实例或None
        """
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.session.flush()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__} {id}: {str(e)}")
            self.session.rollback()
            raise
    
    def delete(self, id: UUID) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(id)
            if instance:
                self.session.delete(instance)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {str(e)}")
            self.session.rollback()
            raise
    
    def delete_many(self, ids: List[UUID]) -> int:
        """
        批量删除记录
        
        Args:
            ids: 记录ID列表
            
        Returns:
            删除的记录数
        """
        try:
            count = self.session.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error deleting multiple {self.model.__name__}: {str(e)}")
            self.session.rollback()
            raise
    
    def exists(self, id: UUID) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
            
        Returns:
            是否存在
        """
        try:
            return self.session.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {str(e)}")
            raise
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        应用筛选条件
        
        Args:
            query: SQLAlchemy查询对象
            filters: 筛选条件字典
            
        Returns:
            应用筛选后的查询对象
        """
        for key, value in filters.items():
            if value is None:
                continue
            
            # 检查字段是否存在
            if not hasattr(self.model, key):
                continue
            
            column = getattr(self.model, key)
            
            # 处理不同的筛选类型
            if isinstance(value, dict):
                # 支持运算符: gt, gte, lt, lte, like, ilike, in, not_in
                if "gt" in value:
                    query = query.filter(column > value["gt"])
                if "gte" in value:
                    query = query.filter(column >= value["gte"])
                if "lt" in value:
                    query = query.filter(column < value["lt"])
                if "lte" in value:
                    query = query.filter(column <= value["lte"])
                if "like" in value:
                    query = query.filter(column.like(f"%{value['like']}%"))
                if "ilike" in value:
                    query = query.filter(column.ilike(f"%{value['ilike']}%"))
                if "in" in value:
                    query = query.filter(column.in_(value["in"]))
                if "not_in" in value:
                    query = query.filter(~column.in_(value["not_in"]))
            elif isinstance(value, list):
                # 列表值视为IN查询
                query = query.filter(column.in_(value))
            else:
                # 精确匹配
                query = query.filter(column == value)
        
        return query










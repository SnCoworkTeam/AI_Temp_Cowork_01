"""
分类管理服务
提供分类的CRUD操作
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.metadata_classification import MetadataClassification

logger = logging.getLogger(__name__)


class ClassificationManagementService:
    """分类管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_classification(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        parent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建分类"""
        try:
            # 检查是否已存在
            existing = self.db.query(MetadataClassification).filter(
                MetadataClassification.name == name
            ).first()
            if existing:
                raise ValueError(f"Classification with name '{name}' already exists")
            
            # 查找父分类
            parent_id = None
            level = 1
            if parent_name:
                parent = self.db.query(MetadataClassification).filter(
                    MetadataClassification.name == parent_name
                ).first()
                if parent:
                    parent_id = parent.id
                    level = parent.level + 1
                else:
                    raise ValueError(f"Parent classification '{parent_name}' not found")
            
            # 创建分类
            classification = MetadataClassification(
                name=name,
                display_name=display_name,
                description=description,
                parent_id=parent_id,
                level=level
            )
            self.db.add(classification)
            self.db.commit()
            self.db.refresh(classification)
            
            return {
                "id": str(classification.id),
                "name": classification.name,
                "display_name": classification.display_name,
                "description": classification.description,
                "parent_id": str(classification.parent_id) if classification.parent_id else None,
                "level": classification.level
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating classification: {str(e)}", exc_info=True)
            raise
    
    def get_classification(self, name: str) -> Optional[Dict[str, Any]]:
        """获取分类"""
        try:
            classification = self.db.query(MetadataClassification).filter(
                MetadataClassification.name == name
            ).first()
            if not classification:
                return None
            
            return {
                "id": str(classification.id),
                "name": classification.name,
                "display_name": classification.display_name,
                "description": classification.description,
                "parent_id": str(classification.parent_id) if classification.parent_id else None,
                "level": classification.level
            }
        except Exception as e:
            logger.error(f"Error getting classification: {str(e)}", exc_info=True)
            raise
    
    def list_classifications(self) -> List[Dict[str, Any]]:
        """列出所有分类"""
        try:
            classifications = self.db.query(MetadataClassification).order_by(
                MetadataClassification.level,
                MetadataClassification.order_index,
                MetadataClassification.name
            ).all()
            
            return [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "display_name": c.display_name,
                    "description": c.description,
                    "parent_id": str(c.parent_id) if c.parent_id else None,
                    "level": c.level,
                    "children_count": len(c.children) if c.children else 0
                }
                for c in classifications
            ]
        except Exception as e:
            logger.error(f"Error listing classifications: {str(e)}", exc_info=True)
            raise
    
    def update_classification(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新分类"""
        try:
            classification = self.db.query(MetadataClassification).filter(
                MetadataClassification.name == name
            ).first()
            if not classification:
                raise ValueError(f"Classification '{name}' not found")
            
            if display_name:
                classification.display_name = display_name
            if description is not None:
                classification.description = description
            
            self.db.commit()
            self.db.refresh(classification)
            
            return {
                "id": str(classification.id),
                "name": classification.name,
                "display_name": classification.display_name,
                "description": classification.description,
                "parent_id": str(classification.parent_id) if classification.parent_id else None,
                "level": classification.level
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating classification: {str(e)}", exc_info=True)
            raise
    
    def delete_classification(self, name: str) -> bool:
        """删除分类"""
        try:
            classification = self.db.query(MetadataClassification).filter(
                MetadataClassification.name == name
            ).first()
            if not classification:
                raise ValueError(f"Classification '{name}' not found")
            
            # 检查是否有子分类
            if classification.children:
                raise ValueError(f"Cannot delete classification '{name}' because it has children")
            
            self.db.delete(classification)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting classification: {str(e)}", exc_info=True)
            raise


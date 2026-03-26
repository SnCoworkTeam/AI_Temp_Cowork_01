"""
工作流版本管理服务
提供工作流版本的CRUD操作和版本管理功能
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, update

from ..models.workflow_metadata import WorkflowMetadata
from ..models.workflow_version import (
    WorkflowVersion,
    WorkflowVersionTag,
    WorkflowVersionCreate,
    WorkflowVersionUpdate,
    WorkflowVersionSchema,
    VersionRestoreRequest
)

logger = logging.getLogger(__name__)


class VersionService:
    """版本管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(self, version_data: WorkflowVersionCreate) -> WorkflowVersionSchema:
        """
        创建工作流新版本
        
        Args:
            version_data: 版本数据
        
        Returns:
            创建的版本信息
        
        Raises:
            ValueError: 如果工作流不存在或版本号已存在
        """
        try:
            # 检查工作流是否存在
            workflow = self.db.query(WorkflowMetadata).filter(
                WorkflowMetadata.workflow_id == version_data.workflow_id
            ).first()
            
            if not workflow:
                raise ValueError(f"Workflow {version_data.workflow_id} not found")
            
            # 检查版本号是否已存在
            existing_version = self.db.query(WorkflowVersion).filter(
                and_(
                    WorkflowVersion.workflow_id == version_data.workflow_id,
                    WorkflowVersion.version == version_data.version
                )
            ).first()
            
            if existing_version:
                raise ValueError(f"Version {version_data.version} already exists for workflow {version_data.workflow_id}")
            
            # 将其他版本设为非当前版本
            self.db.query(WorkflowVersion).filter(
                and_(
                    WorkflowVersion.workflow_id == version_data.workflow_id,
                    WorkflowVersion.version != version_data.version
                )
            ).update({"is_current": False})
            
            # 创建新版本
            db_version = WorkflowVersion(
                workflow_id=version_data.workflow_id,
                version=version_data.version,
                version_number=version_data.version_number,
                description=version_data.description,
                change_summary=version_data.change_summary,
                definition=version_data.definition,
                changes=version_data.changes,
                created_by=version_data.created_by,
                is_current=True,  # 新创建的版本设为当前版本
                deployed_at=datetime.utcnow()
            )
            
            self.db.add(db_version)
            self.db.commit()
            self.db.refresh(db_version)
            
            # 更新工作流元数据的版本号
            workflow.version = version_data.version
            self.db.commit()
            
            logger.info(f"Created version {version_data.version} for workflow {version_data.workflow_id}")
            return self._version_to_schema(db_version)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create version: {str(e)}", exc_info=True)
            raise
    
    def get_versions(
        self,
        workflow_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取工作流的版本列表
        
        Args:
            workflow_id: 工作流ID
            skip: 跳过的记录数
            limit: 每页记录数
        
        Returns:
            版本列表和分页信息
        """
        try:
            # 查询总数
            total = self.db.query(WorkflowVersion).filter(
                WorkflowVersion.workflow_id == workflow_id
            ).count()
            
            # 查询版本列表
            versions = (
                self.db.query(WorkflowVersion)
                .filter(WorkflowVersion.workflow_id == workflow_id)
                .order_by(WorkflowVersion.version_number.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            
            items = [self._version_to_schema(version) for version in versions]
            
            return {
                "items": items,
                "total": total,
                "page": skip // limit + 1 if limit > 0 else 1,
                "page_size": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1
            }
            
        except Exception as e:
            logger.error(f"Failed to get versions for workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    def get_version(self, workflow_id: str, version: str) -> Optional[WorkflowVersionSchema]:
        """
        获取特定版本的工作流
        
        Args:
            workflow_id: 工作流ID
            version: 版本号
        
        Returns:
            版本信息，如果不存在返回None
        """
        try:
            db_version = (
                self.db.query(WorkflowVersion)
                .filter(
                    and_(
                        WorkflowVersion.workflow_id == workflow_id,
                        WorkflowVersion.version == version
                    )
                )
                .first()
            )
            
            if db_version:
                return self._version_to_schema(db_version)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get version {version} for workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    def set_current_version(self, workflow_id: str, version: str) -> WorkflowVersionSchema:
        """
        设置当前版本
        
        Args:
            workflow_id: 工作流ID
            version: 要设置为当前版本的版本号
        
        Returns:
            更新后的版本信息
        
        Raises:
            ValueError: 如果版本不存在
        """
        try:
            # 检查版本是否存在
            db_version = (
                self.db.query(WorkflowVersion)
                .filter(
                    and_(
                        WorkflowVersion.workflow_id == workflow_id,
                        WorkflowVersion.version == version
                    )
                )
                .first()
            )
            
            if not db_version:
                raise ValueError(f"Version {version} not found for workflow {workflow_id}")
            
            # 将所有版本设为非当前
            self.db.query(WorkflowVersion).filter(
                WorkflowVersion.workflow_id == workflow_id
            ).update({"is_current": False})
            
            # 将指定版本设为当前
            db_version.is_current = True
            db_version.deployed_at = datetime.utcnow()
            
            # 更新工作流元数据的版本号
            workflow = self.db.query(WorkflowMetadata).filter(
                WorkflowMetadata.workflow_id == workflow_id
            ).first()
            
            if workflow:
                workflow.version = version
            
            self.db.commit()
            self.db.refresh(db_version)
            
            logger.info(f"Set current version {version} for workflow {workflow_id}")
            return self._version_to_schema(db_version)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set current version {version} for workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    def restore_version(
        self,
        workflow_id: str,
        version: str,
        description: Optional[str] = None
    ) -> WorkflowVersionSchema:
        """
        恢复特定版本（基于历史版本创建新版本）
        
        Args:
            workflow_id: 工作流ID
            version: 要恢复的版本号
            description: 恢复操作的描述
        
        Returns:
            新创建的版本信息
        
        Raises:
            ValueError: 如果源版本不存在
        """
        try:
            # 获取要恢复的版本
            source_version = self.get_version(workflow_id, version)
            if not source_version:
                raise ValueError(f"Version {version} not found for workflow {workflow_id}")
            
            # 获取当前最高版本号
            latest_version = (
                self.db.query(WorkflowVersion)
                .filter(WorkflowVersion.workflow_id == workflow_id)
                .order_by(WorkflowVersion.version_number.desc())
                .first()
            )
            
            current_highest = latest_version.version_number if latest_version else 0
            
            # 创建新版本
            new_version_number = current_highest + 1
            new_version_name = f"v{new_version_number}.0"
            
            restore_data = WorkflowVersionCreate(
                workflow_id=workflow_id,
                version=new_version_name,
                version_number=new_version_number,
                description=description or f"Restored from version {version}",
                change_summary=f"Restored from version {version}",
                definition=source_version.definition,
                changes={
                    "restored_from": version,
                    "restore_description": description,
                    "restore_timestamp": datetime.utcnow().isoformat()
                },
                created_by=source_version.created_by
            )
            
            return self.create_version(restore_data)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to restore version {version} for workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    def add_version_tag(self, workflow_id: str, version: str, tag: str) -> WorkflowVersionSchema:
        """
        为版本添加标签
        
        Args:
            workflow_id: 工作流ID
            version: 版本号
            tag: 标签名称
        
        Returns:
            更新后的版本信息
        
        Raises:
            ValueError: 如果版本不存在或标签已存在
        """
        try:
            # 获取版本
            db_version = (
                self.db.query(WorkflowVersion)
                .filter(
                    and_(
                        WorkflowVersion.workflow_id == workflow_id,
                        WorkflowVersion.version == version
                    )
                )
                .first()
            )
            
            if not db_version:
                raise ValueError(f"Version {version} not found for workflow {workflow_id}")
            
            # 检查标签是否已存在
            existing_tag = (
                self.db.query(WorkflowVersionTag)
                .filter(
                    and_(
                        WorkflowVersionTag.version_id == db_version.id,
                        WorkflowVersionTag.tag == tag
                    )
                )
                .first()
            )
            
            if existing_tag:
                raise ValueError(f"Tag {tag} already exists for version {version}")
            
            # 添加新标签
            new_tag = WorkflowVersionTag(version_id=db_version.id, tag=tag)
            self.db.add(new_tag)
            self.db.commit()
            self.db.refresh(db_version)
            
            logger.info(f"Added tag {tag} to version {version} for workflow {workflow_id}")
            return self._version_to_schema(db_version)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add tag {tag} to version {version}: {str(e)}", exc_info=True)
            raise
    
    def remove_version_tag(self, workflow_id: str, version: str, tag: str) -> WorkflowVersionSchema:
        """
        移除版本标签
        
        Args:
            workflow_id: 工作流ID
            version: 版本号
            tag: 标签名称
        
        Returns:
            更新后的版本信息
        
        Raises:
            ValueError: 如果版本不存在或标签不存在
        """
        try:
            # 获取版本
            db_version = (
                self.db.query(WorkflowVersion)
                .filter(
                    and_(
                        WorkflowVersion.workflow_id == workflow_id,
                        WorkflowVersion.version == version
                    )
                )
                .first()
            )
            
            if not db_version:
                raise ValueError(f"Version {version} not found for workflow {workflow_id}")
            
            # 查找并移除标签
            tag_to_remove = (
                self.db.query(WorkflowVersionTag)
                .filter(
                    and_(
                        WorkflowVersionTag.version_id == db_version.id,
                        WorkflowVersionTag.tag == tag
                    )
                )
                .first()
            )
            
            if not tag_to_remove:
                raise ValueError(f"Tag {tag} not found for version {version}")
            
            self.db.delete(tag_to_remove)
            self.db.commit()
            self.db.refresh(db_version)
            
            logger.info(f"Removed tag {tag} from version {version} for workflow {workflow_id}")
            return self._version_to_schema(db_version)
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove tag {tag} from version {version}: {str(e)}", exc_info=True)
            raise
    
    def _version_to_schema(self, db_version: WorkflowVersion) -> WorkflowVersionSchema:
        """将数据库模型转换为Schema"""
        # 获取标签列表
        tags = [tag.tag for tag in db_version.tags] if db_version.tags else []
        
        return WorkflowVersionSchema(
            id=db_version.id,
            workflow_id=db_version.workflow_id,
            version=db_version.version,
            version_number=db_version.version_number,
            description=db_version.description,
            change_summary=db_version.change_summary,
            definition=db_version.definition,
            changes=db_version.changes,
            created_by=db_version.created_by,
            is_current=db_version.is_current,
            deployed_at=db_version.deployed_at,
            created_at=db_version.created_at,
            updated_at=db_version.updated_at,
            tags=tags
        )


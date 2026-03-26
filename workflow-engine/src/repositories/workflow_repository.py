"""
工作流Repository
工作流定义数据访问层
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

# 导入数据库模型
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.models.workflow_models import (
    WorkflowDefinition as DBWorkflowDefinition,
    WorkflowNode as DBWorkflowNode,
    WorkflowConnection as DBWorkflowConnection,
    WorkflowStatus,
    NodeType
)
from database.src.repositories.workflow_repository import (
    WorkflowDefinitionRepository as DBWorkflowDefinitionRepository,
    WorkflowNodeRepository as DBWorkflowNodeRepository,
    WorkflowConnectionRepository as DBWorkflowConnectionRepository
)

logger = logging.getLogger(__name__)


class WorkflowRepository:
    """工作流Repository（适配层）"""
    
    def __init__(self, session: Session):
        self.session = session
        self._db_repo = DBWorkflowDefinitionRepository(session)
        self._node_repo = DBWorkflowNodeRepository(session)
        self._connection_repo = DBWorkflowConnectionRepository(session)
    
    def get_by_id(self, workflow_id: str) -> Optional[DBWorkflowDefinition]:
        """根据ID获取工作流定义"""
        try:
            uuid_id = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            return self._db_repo.get_by_id(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return None
    
    def get_by_name(self, name: str) -> Optional[DBWorkflowDefinition]:
        """根据名称获取工作流定义"""
        return self._db_repo.get_by_name(name)
    
    def get_by_name_and_version(
        self,
        name: str,
        version: str
    ) -> Optional[DBWorkflowDefinition]:
        """根据名称和版本获取工作流定义"""
        try:
            workflow = self.session.query(DBWorkflowDefinition).filter(
                and_(
                    DBWorkflowDefinition.name == name,
                    DBWorkflowDefinition.version == version
                )
            ).first()
            return workflow
        except SQLAlchemyError as e:
            logger.error(f"Error getting workflow by name and version: {str(e)}")
            return None
    
    def list_versions(self, name: str) -> List[Dict[str, Any]]:
        """列出工作流的所有版本"""
        try:
            workflows = self.session.query(DBWorkflowDefinition).filter(
                DBWorkflowDefinition.name == name
            ).order_by(desc(DBWorkflowDefinition.created_at)).all()
            
            return [
                {
                    "id": str(w.id),
                    "version": w.version,
                    "status": w.status.value if hasattr(w.status, 'value') else str(w.status),
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "created_by": str(w.created_by) if w.created_by else None
                }
                for w in workflows
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error listing workflow versions: {str(e)}")
            return []
    
    def create_workflow(
        self,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        status: str = "draft",
        created_by: Optional[UUID] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBWorkflowDefinition:
        """创建工作流定义"""
        try:
            logger.info(f"[DEBUG] Creating workflow: name='{name}', version='{version}', created_by='{created_by}'")

            # 转换版本 - 数据库中version字段现在是VARCHAR(50)类型
            # 保持语义版本号格式
            if isinstance(version, str):
                db_version = version  # 直接使用字符串版本号
            else:
                db_version = str(version) + ".0.0"  # 转换整数为语义版本号
            logger.info(f"[DEBUG] Using version: {db_version}")

            # 检查版本是否已存在
            logger.info(f"[DEBUG] Checking if workflow exists: name='{name}', version={db_version}")
            existing = self.get_by_name_and_version(name, str(db_version))
            logger.info(f"[DEBUG] Workflow check result: exists={existing is not None}")
            if existing:
                raise ValueError(f"Workflow '{name}' version '{db_version}' already exists")

            # 转换状态
            db_status = WorkflowStatus.DRAFT
            if status == "active":
                db_status = WorkflowStatus.ACTIVE
            elif status == "inactive":
                db_status = WorkflowStatus.INACTIVE
            elif status == "archived":
                db_status = WorkflowStatus.ARCHIVED

            logger.info(f"[DEBUG] Creating DBWorkflowDefinition object with status='{db_status.value}', version='{db_version}'")
            workflow = DBWorkflowDefinition(
                name=name,
                description=description,
                version=db_version,  # 使用字符串版本号
                status=db_status.value,  # 使用枚举的value属性（小写字符串：'draft', 'active'等）
                created_by=created_by,
                config=config or {},
                workflow_metadata=metadata or {}  # 使用正确的字段名 workflow_metadata
            )
            logger.info(f"[DEBUG] Adding workflow to session")
            self.session.add(workflow)
            logger.info(f"[DEBUG] Flushing session")
            self.session.flush()
            logger.info(f"[DEBUG] Workflow created successfully with id={workflow.id}")
            return workflow
        except SQLAlchemyError as e:
            logger.error(f"[DEBUG] SQLAlchemyError creating workflow: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"[DEBUG] Unexpected error creating workflow: {str(e)}", exc_info=True)
            raise
    
    def create_new_version(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBWorkflowDefinition:
        """创建工作流新版本（自动递增版本号）"""
        try:
            # 获取最新版本
            latest = self.session.query(DBWorkflowDefinition).filter(
                DBWorkflowDefinition.name == name
            ).order_by(desc(DBWorkflowDefinition.created_at)).first()
            
            # 计算新版本号
            if latest:
                try:
                    version_parts = latest.version.split('.')
                    if len(version_parts) >= 3:
                        major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
                        new_version = f"{major}.{minor}.{patch + 1}"
                    else:
                        new_version = f"{latest.version}.1"
                except:
                    new_version = f"{latest.version}.1"
            else:
                new_version = "1.0.0"
            
            return self.create_workflow(
                name=name,
                description=description,
                version=new_version,
                status="draft",
                created_by=created_by,
                config=config,
                metadata=metadata
            )
        except SQLAlchemyError as e:
            logger.error(f"Error creating new workflow version: {str(e)}")
            raise
    
    def update_workflow(
        self,
        workflow_id: str,
        **updates
    ) -> Optional[DBWorkflowDefinition]:
        """更新工作流定义"""
        try:
            uuid_id = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            
            # 如果更新中包含 status，需要转换为 WorkflowStatus 枚举
            if "status" in updates:
                status_str = updates["status"]
                try:
                    updates["status"] = WorkflowStatus[status_str.upper()].value
                except KeyError:
                    logger.warning(f"Invalid status: {status_str}")
                    # 如果状态无效，尝试直接使用字符串值
                    updates["status"] = status_str
            
            return self._db_repo.update(uuid_id, **updates)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return None
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流定义"""
        try:
            uuid_id = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
            return self._db_repo.delete(uuid_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            return False
    
    def list_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        created_by: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> List[DBWorkflowDefinition]:
        """列出工作流"""
        try:
            filters = {}
            if status:
                try:
                    filters["status"] = WorkflowStatus[status.upper()]
                except KeyError:
                    pass
            
            if created_by:
                filters["created_by"] = created_by
            
            # 如果 session 处于错误状态，先回滚
            if self.session.is_active and self.session.in_transaction():
                try:
                    # 检查是否有未提交的错误
                    self.session.rollback()
                except Exception:
                    pass
            
            workflows = self._db_repo.get_all(skip=skip, limit=limit, filters=filters)
            
            # 搜索过滤
            if search:
                search_lower = search.lower()
                workflows = [
                    w for w in workflows
                    if search_lower in w.name.lower() or
                       (w.description and search_lower in w.description.lower())
                ]
            
            return workflows
        except SQLAlchemyError as e:
            logger.error(f"Error listing workflows: {str(e)}")
            # 发生错误时回滚
            try:
                self.session.rollback()
            except Exception:
                pass
            raise
    
    def get_latest_version(self, name: str) -> Optional[DBWorkflowDefinition]:
        """获取工作流的最新版本"""
        try:
            return self.session.query(DBWorkflowDefinition).filter(
                DBWorkflowDefinition.name == name
            ).order_by(desc(DBWorkflowDefinition.created_at)).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest workflow version: {str(e)}")
            return None
    
    def get_active_version(self, name: str) -> Optional[DBWorkflowDefinition]:
        """获取工作流的活跃版本"""
        try:
            return self.session.query(DBWorkflowDefinition).filter(
                and_(
                    DBWorkflowDefinition.name == name,
                    DBWorkflowDefinition.status == WorkflowStatus.ACTIVE
                )
            ).order_by(desc(DBWorkflowDefinition.created_at)).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active workflow version: {str(e)}")
            return None










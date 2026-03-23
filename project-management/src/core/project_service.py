"""
项目管理核心服务
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from database.src.models.project_models import (
    Project, ProjectPhase, Milestone, Task, WeeklyReport, Risk,
    ProjectStatus, TaskStatus, MilestoneStatus
)
from database.src.models.knowledge_models import KnowledgeBase
from database.src.models.workflow_models import WorkflowDefinition

logger = logging.getLogger(__name__)


class ProjectService:
    """项目管理核心服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_project(self, project_data: Dict[str, Any]) -> Project:
        """创建项目"""
        try:
            # 检查项目编码是否已存在
            existing = self.db.query(Project).filter(
                Project.project_code == project_data['project_code']
            ).first()
            if existing:
                raise ValueError(f"项目编码 {project_data['project_code']} 已存在")
            
            project = Project(
                project_code=project_data['project_code'],
                name=project_data['name'],
                description=project_data.get('description'),
                status=ProjectStatus(project_data.get('status', 'planning')),
                priority=project_data.get('priority', 'medium'),
                manager_id=project_data.get('manager_id'),
                start_date=project_data.get('start_date'),
                end_date=project_data.get('end_date'),
                budget=project_data.get('budget'),
                metadata=project_data.get('metadata', {})
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            logger.info(f"项目创建成功: {project.id} - {project.name}")
            return project
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建项目失败: {str(e)}", exc_info=True)
            raise
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目详情"""
        try:
            return self.db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
        except ValueError:
            return None
    
    async def list_projects(
        self,
        status: Optional[str] = None,
        manager_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """获取项目列表"""
        query = self.db.query(Project)
        
        if status:
            query = query.filter(Project.status == ProjectStatus(status))
        if manager_id:
            try:
                query = query.filter(Project.manager_id == uuid.UUID(manager_id))
            except ValueError:
                pass  # 无效的UUID，忽略过滤
        
        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            'items': projects,
            'total': total,
            'offset': offset,
            'limit': limit
        }
    
    async def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Project:
        """更新项目"""
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        for key, value in update_data.items():
            if hasattr(project, key) and value is not None:
                if key == 'status':
                    setattr(project, key, ProjectStatus(value))
                else:
                    setattr(project, key, value)
        
        self.db.commit()
        self.db.refresh(project)
        return project
    
    async def create_weekly_report(self, project_id: str, report_data: Dict[str, Any]) -> WeeklyReport:
        """创建周报"""
        project = await self.get_project(project_id)
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        report = WeeklyReport(
            project_id=project.id,
            report_date=report_data['report_date'],
            reporter_id=report_data.get('reporter_id'),
            week_number=report_data.get('week_number'),
            content_plan=report_data.get('content_plan'),
            content_achievement=report_data.get('content_achievement'),
            key_tasks_completed=report_data.get('key_tasks_completed', []),
            issues_risks=report_data.get('issues_risks'),
            next_week_plan=report_data.get('next_week_plan'),
            metrics=report_data.get('metrics', {})
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        # 更新项目进度
        await self._update_project_progress(project_id)
        
        return report
    
    async def _update_project_progress(self, project_id: str):
        """更新项目整体进度"""
        project = await self.get_project(project_id)
        if not project:
            return
        
        # 计算任务完成率
        total_tasks = self.db.query(func.count(Task.id)).filter(
            Task.project_id == project.id
        ).scalar() or 0
        
        completed_tasks = self.db.query(func.count(Task.id)).filter(
            Task.project_id == project.id,
            Task.status == TaskStatus.COMPLETED
        ).scalar() or 0
        
        if total_tasks > 0:
            project.progress_percent = (completed_tasks / total_tasks) * 100
        else:
            # 基于里程碑计算
            total_milestones = self.db.query(func.count(Milestone.id)).filter(
                Milestone.project_id == project.id
            ).scalar() or 0
            
            completed_milestones = self.db.query(func.count(Milestone.id)).filter(
                Milestone.project_id == project.id,
                Milestone.status == MilestoneStatus.COMPLETED
            ).scalar() or 0
            
            if total_milestones > 0:
                project.progress_percent = (completed_milestones / total_milestones) * 100
        
        self.db.commit()


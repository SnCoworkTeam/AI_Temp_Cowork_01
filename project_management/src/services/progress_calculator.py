"""
进度自动计算服务
实现项目、阶段、任务的进度自动计算
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from database.src.models.project_models import Project, ProjectPhase, Task, TaskStatus

logger = logging.getLogger(__name__)


class ProgressCalculator:
    """进度计算器"""

    @staticmethod
    def calculate_task_progress(task: Task) -> float:
        """
        计算任务进度

        规则：
        - 如果任务已完成，进度为100%
        - 如果任务被取消，进度为0%
        - 否则使用progress_percent字段
        """
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        if task.status == TaskStatus.CANCELLED:
            return 0.0
        return task.progress_percent or 0.0

    @staticmethod
    def calculate_phase_progress(phase: ProjectPhase, db: Session) -> float:
        """
        计算阶段进度

        规则：
        - 阶段进度 = 阶段下所有任务的加权平均进度
        - 权重 = 任务的estimated_hours（如果为None，则使用平均权重）
        """
        tasks = db.query(Task).filter(Task.phase_id == phase.id).all()

        if not tasks:
            return phase.progress_percent or 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for task in tasks:
            task_progress = ProgressCalculator.calculate_task_progress(task)
            weight = task.estimated_hours if task.estimated_hours else 1.0
            weighted_sum += task_progress * weight
            total_weight += weight

        if total_weight == 0:
            # 如果所有任务都没有estimated_hours，使用简单平均
            avg_progress = sum(ProgressCalculator.calculate_task_progress(t) for t in tasks) / len(tasks)
            return round(avg_progress, 2)

        progress = weighted_sum / total_weight
        return round(progress, 2)

    @staticmethod
    def calculate_project_progress(project: Project, db: Session) -> float:
        """
        计算项目进度

        规则：
        - 项目进度 = 所有任务的加权平均进度
        - 权重 = 任务的estimated_hours（如果为None，则使用平均权重）
        - 如果项目有阶段，也可以基于阶段进度计算
        """
        # 方法1：基于所有任务计算
        tasks = db.query(Task).filter(Task.project_id == project.id).all()

        if not tasks:
            # 如果没有任务，检查是否有阶段
            phases = db.query(ProjectPhase).filter(ProjectPhase.project_id == project.id).all()
            if phases:
                # 基于阶段进度计算
                phase_progresses = []
                for phase in phases:
                    phase_progress = ProgressCalculator.calculate_phase_progress(phase, db)
                    phase_progresses.append(phase_progress)

                if phase_progresses:
                    avg_progress = sum(phase_progresses) / len(phase_progresses)
                    return round(avg_progress, 2)

            return project.progress_percent or 0.0

        # 使用任务的加权平均
        total_weight = 0.0
        weighted_sum = 0.0

        for task in tasks:
            task_progress = ProgressCalculator.calculate_task_progress(task)
            weight = task.estimated_hours if task.estimated_hours else 1.0
            weighted_sum += task_progress * weight
            total_weight += weight

        if total_weight == 0:
            # 如果所有任务都没有estimated_hours，使用简单平均
            avg_progress = sum(ProgressCalculator.calculate_task_progress(t) for t in tasks) / len(tasks)
            return round(avg_progress, 2)

        progress = weighted_sum / total_weight
        return round(progress, 2)

    @staticmethod
    def update_phase_progress(phase_id: UUID, db: Session) -> float:
        """
        更新阶段进度并保存到数据库
        """
        phase = db.query(ProjectPhase).filter(ProjectPhase.id == phase_id).first()
        if not phase:
            raise ValueError(f"阶段不存在: {phase_id}")

        progress = ProgressCalculator.calculate_phase_progress(phase, db)
        phase.progress_percent = progress
        db.flush()

        logger.info(f"更新阶段进度: {phase.name} -> {progress}%")
        return progress

    @staticmethod
    def update_project_progress(project_id: UUID, db: Session) -> float:
        """
        更新项目进度并保存到数据库
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        progress = ProgressCalculator.calculate_project_progress(project, db)
        project.progress_percent = progress
        db.flush()

        logger.info(f"更新项目进度: {project.name} -> {progress}%")
        return progress

    @staticmethod
    def update_related_progresses(task: Task, db: Session):
        """
        更新任务相关的阶段和项目进度

        当任务创建、更新或删除时调用
        """
        try:
            # 更新阶段进度
            if task.phase_id:
                ProgressCalculator.update_phase_progress(task.phase_id, db)

            # 更新项目进度
            ProgressCalculator.update_project_progress(task.project_id, db)

            db.flush()
        except Exception as e:
            logger.error(f"更新相关进度失败: {e!s}", exc_info=True)
            # 不抛出异常，避免影响主流程

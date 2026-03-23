"""
计划任务与实际任务同步服务
维护计划任务和实际任务之间的一致性
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from database.src.models.project_models import Project, ProjectPlan, ProjectPlanTask, Task

logger = logging.getLogger(__name__)


class PlanSyncService:
    """计划同步服务"""

    @classmethod
    def sync_plan_to_actual(cls, plan_task_id: UUID, db: Session) -> Task | None:
        """
        将计划任务同步为实际任务

        Args:
            plan_task_id: 计划任务ID
            db: 数据库会话

        Returns:
            创建或更新的实际任务，如果失败返回None
        """
        try:
            # 获取计划任务
            plan_task = db.query(ProjectPlanTask).filter(ProjectPlanTask.id == plan_task_id).first()

            if not plan_task:
                logger.error(f"计划任务不存在: {plan_task_id}")
                return None

            # 获取计划信息
            plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_task.plan_id).first()

            if not plan:
                logger.error(f"计划不存在: {plan_task.plan_id}")
                return None

            # 获取项目信息
            project = db.query(Project).filter(Project.id == plan.project_id).first()

            if not project:
                logger.error(f"项目不存在: {plan.project_id}")
                return None

            # 如果已经有关联的实际任务，更新它
            if plan_task.actual_task_id:
                actual_task = db.query(Task).filter(Task.id == plan_task.actual_task_id).first()

                if actual_task:
                    # 更新现有任务
                    actual_task.name = plan_task.name
                    actual_task.description = plan_task.description
                    actual_task.start_date = plan_task.start_date
                    actual_task.end_date = plan_task.end_date
                    actual_task.assignee_id = plan_task.assignee_id
                    actual_task.estimated_hours = plan_task.estimated_hours
                    actual_task.priority = plan_task.priority

                    # 更新状态映射
                    status_mapping = {
                        "planned": "todo",
                        "in_progress": "in_progress",
                        "completed": "completed",
                        "cancelled": "cancelled",
                    }
                    if plan_task.status:
                        actual_task.status = status_mapping.get(
                            (
                                plan_task.status.value.lower()
                                if hasattr(plan_task.status, "value")
                                else str(plan_task.status).lower()
                            ),
                            "todo",
                        )

                    db.commit()
                    db.refresh(actual_task)
                    logger.info(f"已更新实际任务: {actual_task.id}")
                    return actual_task

            # 创建新的实际任务
            from database.src.models.project_models import TaskStatus

            # 状态映射
            status_mapping = {
                "planned": TaskStatus.TODO,
                "in_progress": TaskStatus.IN_PROGRESS,
                "completed": TaskStatus.COMPLETED,
                "cancelled": TaskStatus.CANCELLED,
            }

            task_status = TaskStatus.TODO
            if plan_task.status:
                task_status = status_mapping.get(
                    (
                        plan_task.status.value.lower()
                        if hasattr(plan_task.status, "value")
                        else str(plan_task.status).lower()
                    ),
                    TaskStatus.TODO,
                )

            actual_task = Task(
                project_id=project.id,
                phase_id=plan_task.phase_id,
                milestone_id=plan_task.milestone_id,
                category_id=plan_task.category_id,
                name=plan_task.name,
                description=plan_task.description,
                start_date=plan_task.start_date,
                end_date=plan_task.end_date,
                assignee_id=plan_task.assignee_id,
                estimated_hours=plan_task.estimated_hours,
                priority=plan_task.priority or "medium",
                status=task_status,
            )

            db.add(actual_task)
            db.flush()

            # 更新计划任务的关联
            plan_task.actual_task_id = actual_task.id

            db.commit()
            db.refresh(actual_task)

            logger.info(f"已创建实际任务: {actual_task.id}，关联到计划任务: {plan_task_id}")
            return actual_task

        except Exception as e:
            logger.error(f"同步计划任务到实际任务失败: {e!s}", exc_info=True)
            db.rollback()
            return None

    @classmethod
    def sync_actual_to_plan(cls, task_id: UUID, plan_task_id: UUID, db: Session) -> ProjectPlanTask | None:
        """
        将实际任务的进度同步回计划任务

        Args:
            task_id: 实际任务ID
            plan_task_id: 计划任务ID
            db: 数据库会话

        Returns:
            更新的计划任务，如果失败返回None
        """
        try:
            # 获取实际任务
            actual_task = db.query(Task).filter(Task.id == task_id).first()
            if not actual_task:
                logger.error(f"实际任务不存在: {task_id}")
                return None

            # 获取计划任务
            plan_task = db.query(ProjectPlanTask).filter(ProjectPlanTask.id == plan_task_id).first()

            if not plan_task:
                logger.error(f"计划任务不存在: {plan_task_id}")
                return None

            # 验证关联关系
            if plan_task.actual_task_id != task_id:
                logger.warning(f"计划任务 {plan_task_id} 与实际任务 {task_id} 未关联")
                plan_task.actual_task_id = task_id

            # 同步进度信息
            plan_task.progress_percent = actual_task.progress_percent or 0.0
            plan_task.actual_start_date = actual_task.actual_start_date
            plan_task.actual_end_date = actual_task.actual_end_date
            plan_task.actual_hours = actual_task.actual_hours

            # 同步状态
            status_mapping = {
                "todo": "planned",
                "in_progress": "in_progress",
                "completed": "completed",
                "cancelled": "cancelled",
            }

            if actual_task.status:
                mapped_status = status_mapping.get(
                    (
                        actual_task.status.value.lower()
                        if hasattr(actual_task.status, "value")
                        else str(actual_task.status).lower()
                    ),
                    "planned",
                )
                from database.src.models.project_models import PlanTaskStatus

                try:
                    plan_task.status = PlanTaskStatus(mapped_status)
                except ValueError:
                    pass

            db.commit()
            db.refresh(plan_task)

            logger.info(f"已同步实际任务进度到计划任务: {plan_task_id}")
            return plan_task

        except Exception as e:
            logger.error(f"同步实际任务到计划任务失败: {e!s}", exc_info=True)
            db.rollback()
            return None

    @classmethod
    def batch_sync_plan_to_actual(cls, plan_id: UUID, db: Session) -> dict[str, int]:
        """
        批量将计划任务同步为实际任务

        Args:
            plan_id: 计划ID
            db: 数据库会话

        Returns:
            同步结果统计
        """
        try:
            plan_tasks = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan_id).all()

            results = {"total": len(plan_tasks), "created": 0, "updated": 0, "skipped": 0, "failed": 0}

            for plan_task in plan_tasks:
                try:
                    if plan_task.actual_task_id:
                        # 更新现有任务
                        result = cls.sync_plan_to_actual(plan_task.id, db)
                        if result:
                            results["updated"] += 1
                        else:
                            results["failed"] += 1
                    else:
                        # 创建新任务
                        result = cls.sync_plan_to_actual(plan_task.id, db)
                        if result:
                            results["created"] += 1
                        else:
                            results["failed"] += 1
                except Exception as e:
                    logger.error(f"同步计划任务失败 {plan_task.id}: {e!s}")
                    results["failed"] += 1
                    results["skipped"] += 1

            logger.info(f"批量同步完成: {results}")
            return results

        except Exception as e:
            logger.error(f"批量同步失败: {e!s}", exc_info=True)
            return {"total": 0, "created": 0, "updated": 0, "skipped": 0, "failed": 1}

    @classmethod
    def check_sync_status(cls, plan_task_id: UUID, db: Session) -> dict:
        """
        检查计划任务与实际任务的同步状态

        Args:
            plan_task_id: 计划任务ID
            db: 数据库会话

        Returns:
            同步状态信息
        """
        try:
            plan_task = db.query(ProjectPlanTask).filter(ProjectPlanTask.id == plan_task_id).first()

            if not plan_task:
                return {"is_synced": False, "has_actual_task": False, "sync_status": "plan_task_not_found"}

            if not plan_task.actual_task_id:
                return {"is_synced": False, "has_actual_task": False, "sync_status": "not_synced"}

            actual_task = db.query(Task).filter(Task.id == plan_task.actual_task_id).first()

            if not actual_task:
                return {"is_synced": False, "has_actual_task": False, "sync_status": "actual_task_not_found"}

            # 检查数据一致性
            is_consistent = (
                plan_task.name == actual_task.name
                and plan_task.start_date == actual_task.start_date
                and plan_task.end_date == actual_task.end_date
            )

            return {
                "is_synced": True,
                "has_actual_task": True,
                "sync_status": "synced" if is_consistent else "inconsistent",
                "actual_task_id": str(actual_task.id),
                "is_consistent": is_consistent,
                "differences": (
                    {
                        "name": plan_task.name != actual_task.name,
                        "start_date": plan_task.start_date != actual_task.start_date,
                        "end_date": plan_task.end_date != actual_task.end_date,
                    }
                    if not is_consistent
                    else {}
                ),
            }

        except Exception as e:
            logger.error(f"检查同步状态失败: {e!s}", exc_info=True)
            return {"is_synced": False, "has_actual_task": False, "sync_status": "error", "error": str(e)}

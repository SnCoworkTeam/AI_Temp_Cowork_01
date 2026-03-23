"""
项目计划通知服务
处理计划变更通知、关键路径任务延期预警等
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PlanNotificationService:
    """计划通知服务"""

    @classmethod
    def notify_plan_changed(
        cls, plan_id: UUID, change_type: str, changed_by: UUID, change_description: str, db: Session
    ):
        """
        通知计划变更

        Args:
            plan_id: 计划ID
            change_type: 变更类型（task_added, task_updated, dependency_changed等）
            changed_by: 变更人ID
            change_description: 变更描述
            db: 数据库会话
        """
        try:
            from database.src.models.project_models import Project, ProjectMember, ProjectPlan
            from database.src.models.system_models import Notification

            # 获取计划信息
            plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_id).first()
            if not plan:
                logger.warning(f"计划不存在: {plan_id}")
                return

            # 获取项目信息
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            if not project:
                logger.warning(f"项目不存在: {plan.project_id}")
                return

            # 获取需要通知的用户（项目成员、项目经理）
            notify_user_ids = set()

            # 添加项目经理
            if project.manager_id:
                notify_user_ids.add(project.manager_id)

            # 添加项目成员
            members = db.query(ProjectMember).filter(ProjectMember.project_id == project.id).all()
            for member in members:
                if member.user_id:
                    notify_user_ids.add(member.user_id)

            # 排除变更人自己
            notify_user_ids.discard(changed_by)

            # 创建通知
            change_type_names = {
                "task_added": "添加任务",
                "task_updated": "更新任务",
                "task_deleted": "删除任务",
                "dependency_changed": "变更依赖",
                "date_updated": "更新日期",
                "plan_updated": "更新计划",
            }

            change_type_name = change_type_names.get(change_type, change_type)
            title = "项目计划已变更"
            message = f"项目 '{project.name}' 的计划 '{plan.name}' 已变更：{change_type_name}。{change_description}"

            for user_id in notify_user_ids:
                try:
                    notification = Notification(
                        user_id=user_id,
                        title=title,
                        message=message,
                        type="plan_changed",
                        metadata={
                            "plan_id": str(plan_id),
                            "project_id": str(project.id),
                            "change_type": change_type,
                            "changed_by": str(changed_by),
                        },
                        is_read=False,
                    )
                    db.add(notification)
                except Exception as e:
                    logger.error(f"创建通知失败（用户 {user_id}）: {e!s}")

            db.commit()
            logger.info(f"已为 {len(notify_user_ids)} 个用户创建计划变更通知")

        except Exception as e:
            logger.error(f"通知计划变更失败: {e!s}", exc_info=True)
            db.rollback()

    @classmethod
    def notify_critical_task_delayed(cls, task_id: UUID, db: Session):
        """
        通知关键任务延期

        Args:
            task_id: 任务ID
            db: 数据库会话
        """
        try:
            from database.src.models.project_models import Project, ProjectMember, ProjectPlan, ProjectPlanTask
            from database.src.models.system_models import Notification

            # 获取任务信息
            task = db.query(ProjectPlanTask).filter(ProjectPlanTask.id == task_id).first()
            if not task:
                logger.warning(f"任务不存在: {task_id}")
                return

            # 检查是否是关键任务
            if not task.is_critical:
                return

            # 检查是否延期
            if not task.end_date:
                return

            # 如果实际结束日期晚于计划结束日期，或者当前日期已超过计划结束日期但任务未完成
            is_delayed = False
            if task.actual_end_date and task.end_date:
                if task.actual_end_date > task.end_date:
                    is_delayed = True
            elif datetime.now().date() > task.end_date:
                # 检查任务状态
                if task.status.value.lower() not in ["completed", "cancelled"]:
                    is_delayed = True

            if not is_delayed:
                return

            # 获取计划信息
            plan = db.query(ProjectPlan).filter(ProjectPlan.id == task.plan_id).first()
            if not plan:
                return

            # 获取项目信息
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            if not project:
                return

            # 获取需要通知的用户
            notify_user_ids = set()

            if project.manager_id:
                notify_user_ids.add(project.manager_id)

            if task.assignee_id:
                notify_user_ids.add(task.assignee_id)

            members = db.query(ProjectMember).filter(ProjectMember.project_id == project.id).all()
            for member in members:
                if member.user_id:
                    notify_user_ids.add(member.user_id)

            # 创建通知
            delay_days = 0
            if task.actual_end_date and task.end_date:
                delay_days = (task.actual_end_date - task.end_date).days
            elif task.end_date:
                delay_days = (datetime.now().date() - task.end_date).days

            title = "⚠️ 关键任务延期预警"
            message = f"项目 '{project.name}' 的关键任务 '{task.name}' 已延期 {delay_days} 天，可能影响项目进度。"

            for user_id in notify_user_ids:
                try:
                    notification = Notification(
                        user_id=user_id,
                        title=title,
                        message=message,
                        type="critical_task_delayed",
                        metadata={
                            "task_id": str(task_id),
                            "plan_id": str(plan.id),
                            "project_id": str(project.id),
                            "delay_days": delay_days,
                        },
                        is_read=False,
                    )
                    db.add(notification)
                except Exception as e:
                    logger.error(f"创建延期通知失败（用户 {user_id}）: {e!s}")

            db.commit()
            logger.info(f"已为 {len(notify_user_ids)} 个用户创建关键任务延期通知")

        except Exception as e:
            logger.error(f"通知关键任务延期失败: {e!s}", exc_info=True)
            db.rollback()

    @classmethod
    def check_and_notify_delayed_tasks(cls, plan_id: UUID, db: Session):
        """
        检查计划中的所有关键任务，通知延期的任务

        Args:
            plan_id: 计划ID
            db: 数据库会话
        """
        try:
            from database.src.models.project_models import ProjectPlanTask

            # 获取所有关键任务
            critical_tasks = (
                db.query(ProjectPlanTask)
                .filter(ProjectPlanTask.plan_id == plan_id, ProjectPlanTask.is_critical == True)
                .all()
            )

            for task in critical_tasks:
                cls.notify_critical_task_delayed(task.id, db)

            logger.info(f"已检查计划 {plan_id} 的 {len(critical_tasks)} 个关键任务")

        except Exception as e:
            logger.error(f"检查延期任务失败: {e!s}", exc_info=True)

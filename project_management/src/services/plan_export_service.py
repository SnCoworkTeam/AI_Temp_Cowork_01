"""
项目计划导出服务
支持导出为Excel和MS Project格式
"""

import io
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not available, Excel export will be disabled")

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logging.warning("openpyxl not available, Excel export will use pandas only")

logger = logging.getLogger(__name__)


class PlanExportService:
    """计划导出服务"""

    @classmethod
    def export_to_excel(cls, plan_id: UUID, db: Session) -> bytes:
        """
        导出项目计划为Excel格式

        Args:
            plan_id: 计划ID
            db: 数据库会话

        Returns:
            Excel文件的字节数据
        """
        from database.src.models.project_models import ProjectPlan, ProjectPlanTask

        if not PANDAS_AVAILABLE:
            raise ValueError("pandas is required for Excel export")

        # 获取计划信息
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"计划不存在: {plan_id}")

        # 获取计划任务
        tasks = (
            db.query(ProjectPlanTask)
            .filter(ProjectPlanTask.plan_id == plan_id)
            .order_by(ProjectPlanTask.start_date.asc())
            .all()
        )

        # 构建任务数据
        task_data = []
        for task in tasks:
            dependencies_str = ""
            if task.dependencies:
                dep_ids = []
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        dep_ids.append(str(dep["task_id"]))
                dependencies_str = ", ".join(dep_ids)

            task_data.append(
                {
                    "任务ID": str(task.id),
                    "任务名称": task.name,
                    "任务描述": task.description or "",
                    "开始日期": task.start_date.isoformat() if task.start_date else "",
                    "结束日期": task.end_date.isoformat() if task.end_date else "",
                    "持续天数": task.duration_days or "",
                    "进度(%)": task.progress_percent or 0.0,
                    "状态": task.status.value if hasattr(task.status, "value") else str(task.status),
                    "优先级": task.priority or "medium",
                    "是否关键任务": "是" if task.is_critical else "否",
                    "依赖任务": dependencies_str,
                    "负责人": task.assignee_id if task.assignee_id else "",
                    "预估工时(小时)": task.estimated_hours or "",
                    "实际工时(小时)": task.actual_hours or "",
                }
            )

        # 创建DataFrame
        df = pd.DataFrame(task_data)

        # 创建Excel写入器
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 写入计划信息
            plan_info = pd.DataFrame(
                {
                    "属性": ["计划名称", "计划描述", "版本", "开始日期", "结束日期", "任务数量"],
                    "值": [
                        plan.name,
                        plan.description or "",
                        plan.version,
                        plan.start_date.isoformat() if plan.start_date else "",
                        plan.end_date.isoformat() if plan.end_date else "",
                        len(tasks),
                    ],
                }
            )
            plan_info.to_excel(writer, sheet_name="计划信息", index=False)

            # 写入任务列表
            df.to_excel(writer, sheet_name="任务列表", index=False)

        output.seek(0)
        return output.getvalue()

    @classmethod
    def export_to_ms_project_xml(cls, plan_id: UUID, db: Session) -> str:
        """
        导出项目计划为MS Project XML格式

        Args:
            plan_id: 计划ID
            db: 数据库会话

        Returns:
            MS Project XML格式的字符串
        """
        from database.src.models.project_models import ProjectPlan, ProjectPlanTask

        # 获取计划信息
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"计划不存在: {plan_id}")

        # 获取计划任务
        tasks = (
            db.query(ProjectPlanTask)
            .filter(ProjectPlanTask.plan_id == plan_id)
            .order_by(ProjectPlanTask.start_date.asc())
            .all()
        )

        # 构建任务映射（用于依赖关系）
        task_map = {str(task.id): idx + 2 for idx, task in enumerate(tasks)}  # 从2开始，因为1是项目摘要任务

        # 构建XML
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Project xmlns="http://schemas.microsoft.com/project">',
            f"<Name>{plan.name}</Name>",
            f"<Title>{plan.name}</Title>",
            "<CalendarUID>1</CalendarUID>",
            "<StartDate>"
            + (plan.start_date.isoformat() if plan.start_date else datetime.now().date().isoformat())
            + "</StartDate>",
            "<FinishDate>"
            + (plan.end_date.isoformat() if plan.end_date else datetime.now().date().isoformat())
            + "</FinishDate>",
            "<Tasks>",
        ]

        # 添加项目摘要任务
        xml_parts.append("<Task>")
        xml_parts.append("<UID>1</UID>")
        xml_parts.append(f"<Name>{plan.name}</Name>")
        xml_parts.append("<OutlineLevel>0</OutlineLevel>")
        xml_parts.append("<Summary>1</Summary>")
        if plan.start_date:
            xml_parts.append(f"<Start>{plan.start_date.isoformat()}T08:00:00</Start>")
        if plan.end_date:
            xml_parts.append(f"<Finish>{plan.end_date.isoformat()}T17:00:00</Finish>")
        xml_parts.append("</Task>")

        # 添加任务
        for idx, task in enumerate(tasks, start=2):
            xml_parts.append("<Task>")
            xml_parts.append(f"<UID>{idx}</UID>")
            xml_parts.append(f"<Name>{task.name}</Name>")
            xml_parts.append("<OutlineLevel>1</OutlineLevel>")

            if task.start_date:
                xml_parts.append(f"<Start>{task.start_date.isoformat()}T08:00:00</Start>")
            if task.end_date:
                xml_parts.append(f"<Finish>{task.end_date.isoformat()}T17:00:00</Finish>")

            if task.duration_days:
                xml_parts.append(f"<Duration>PT{task.duration_days * 8}H0M0S</Duration>")

            # 添加依赖关系
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        dep_task_id = str(dep["task_id"])
                        if dep_task_id in task_map:
                            dep_uid = task_map[dep_task_id]
                            xml_parts.append("<PredecessorLink>")
                            xml_parts.append(f"<PredecessorUID>{dep_uid}</PredecessorUID>")
                            xml_parts.append("<Type>1</Type>")  # Finish-to-Start
                            xml_parts.append("</PredecessorLink>")

            # 添加进度
            if task.progress_percent:
                xml_parts.append(f"<PercentComplete>{int(task.progress_percent)}</PercentComplete>")

            xml_parts.append("</Task>")

        xml_parts.append("</Tasks>")
        xml_parts.append("</Project>")

        return "\n".join(xml_parts)

    @classmethod
    def export_to_json(cls, plan_id: UUID, db: Session) -> dict:
        """
        导出项目计划为JSON格式

        Args:
            plan_id: 计划ID
            db: 数据库会话

        Returns:
            JSON格式的字典
        """
        from database.src.models.project_models import ProjectPlan, ProjectPlanTask

        # 获取计划信息
        plan = db.query(ProjectPlan).filter(ProjectPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"计划不存在: {plan_id}")

        # 获取计划任务
        tasks = (
            db.query(ProjectPlanTask)
            .filter(ProjectPlanTask.plan_id == plan_id)
            .order_by(ProjectPlanTask.start_date.asc())
            .all()
        )

        # 构建JSON数据
        plan_data = {
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "description": plan.description,
                "version": plan.version,
                "start_date": plan.start_date.isoformat() if plan.start_date else None,
                "end_date": plan.end_date.isoformat() if plan.end_date else None,
            },
            "tasks": [],
        }

        for task in tasks:
            task_data = {
                "id": str(task.id),
                "name": task.name,
                "description": task.description,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "end_date": task.end_date.isoformat() if task.end_date else None,
                "duration_days": task.duration_days,
                "progress_percent": task.progress_percent or 0.0,
                "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                "priority": task.priority or "medium",
                "is_critical": task.is_critical or False,
                "dependencies": task.dependencies or [],
                "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                "estimated_hours": task.estimated_hours,
                "actual_hours": task.actual_hours,
            }
            plan_data["tasks"].append(task_data)

        return plan_data

    @classmethod
    def import_from_excel(cls, excel_data: bytes, project_id: UUID, plan_name: str, db: Session) -> dict:
        """
        从Excel导入项目计划

        Args:
            excel_data: Excel文件的字节数据
            project_id: 项目ID
            plan_name: 计划名称
            db: 数据库会话

        Returns:
            导入结果字典，包含创建的 plan_id 和 task_count
        """
        from database.src.models.basic_data_models import BasicDataCategory
        from database.src.models.project_models import PlanTaskStatus, ProjectPlan, ProjectPlanTask

        if not PANDAS_AVAILABLE:
            raise ValueError("pandas is required for Excel import")

        # 读取Excel文件
        excel_file = io.BytesIO(excel_data)

        try:
            # 尝试读取"任务列表"工作表
            try:
                df = pd.read_excel(excel_file, sheet_name="任务列表")
            except:
                # 如果没有"任务列表"工作表，读取第一个工作表
                excel_file.seek(0)
                df = pd.read_excel(excel_file, sheet_name=0)

            # 创建计划
            plan = ProjectPlan(
                project_id=project_id,
                name=plan_name,
                description="从Excel导入的计划",
                version="1.0",
                is_active=True,
                is_baseline=False,
            )
            db.add(plan)
            db.flush()

            # 解析任务数据
            tasks_created = 0
            tasks_failed = 0
            errors = []

            # 列名映射（支持中英文）
            column_mapping = {
                "任务名称": "name",
                "任务ID": "id",
                "任务描述": "description",
                "开始日期": "start_date",
                "结束日期": "end_date",
                "持续天数": "duration_days",
                "进度(%)": "progress",
                "状态": "status",
                "优先级": "priority",
                "是否关键任务": "is_critical",
                "依赖任务": "dependencies",
                "负责人": "assignee",
                "预估工时(小时)": "estimated_hours",
                "实际工时(小时)": "actual_hours",
                # 英文列名
                "name": "name",
                "task_name": "name",
                "description": "description",
                "start_date": "start_date",
                "end_date": "end_date",
                "duration": "duration_days",
                "progress": "progress",
                "status": "status",
                "priority": "priority",
                "is_critical": "is_critical",
                "dependencies": "dependencies",
                "assignee": "assignee",
                "estimated_hours": "estimated_hours",
                "actual_hours": "actual_hours",
            }

            # 标准化列名
            df.columns = df.columns.str.strip()
            normalized_columns = {}
            for col in df.columns:
                for key, value in column_mapping.items():
                    if key.lower() in col.lower() or col.lower() in key.lower():
                        normalized_columns[col] = value
                        break

            # 获取任务类型（从基础数据）
            task_type_category = (
                db.query(BasicDataCategory)
                .filter(BasicDataCategory.category_type == "task_type", BasicDataCategory.is_active == True)
                .first()
            )

            if not task_type_category:
                raise ValueError("未找到任务类型基础数据，请先在基础数据中创建任务类型")

            for idx, row in df.iterrows():
                try:
                    # 解析任务名称（必需）
                    task_name = None
                    for col in df.columns:
                        if normalized_columns.get(col) == "name":
                            task_name = str(row[col]).strip() if pd.notna(row[col]) else None
                            break

                    if not task_name or task_name == "nan" or task_name == "":
                        tasks_failed += 1
                        errors.append(f"第{idx+2}行: 任务名称不能为空")
                        continue

                    # 解析日期
                    start_date = None
                    end_date = None
                    for col in df.columns:
                        if normalized_columns.get(col) == "start_date":
                            if pd.notna(row[col]):
                                if isinstance(row[col], str):
                                    try:
                                        start_date = datetime.strptime(row[col], "%Y-%m-%d").date()
                                    except:
                                        start_date = pd.to_datetime(row[col]).date()
                                else:
                                    start_date = pd.to_datetime(row[col]).date()
                        elif normalized_columns.get(col) == "end_date":
                            if pd.notna(row[col]):
                                if isinstance(row[col], str):
                                    try:
                                        end_date = datetime.strptime(row[col], "%Y-%m-%d").date()
                                    except:
                                        end_date = pd.to_datetime(row[col]).date()
                                else:
                                    end_date = pd.to_datetime(row[col]).date()

                    # 解析持续时间
                    duration_days = None
                    for col in df.columns:
                        if normalized_columns.get(col) == "duration_days":
                            if pd.notna(row[col]):
                                try:
                                    duration_days = int(float(row[col]))
                                except:
                                    pass

                    # 解析进度
                    progress_percent = 0.0
                    for col in df.columns:
                        if normalized_columns.get(col) == "progress":
                            if pd.notna(row[col]):
                                try:
                                    progress_percent = float(row[col])
                                    if progress_percent > 100:
                                        progress_percent = 100
                                    elif progress_percent < 0:
                                        progress_percent = 0
                                except:
                                    pass

                    # 解析状态
                    task_status = PlanTaskStatus.PLANNED
                    for col in df.columns:
                        if normalized_columns.get(col) == "status":
                            if pd.notna(row[col]):
                                status_str = str(row[col]).lower().strip()
                                if "完成" in status_str or "completed" in status_str:
                                    task_status = PlanTaskStatus.COMPLETED
                                elif "进行" in status_str or "in_progress" in status_str or "in progress" in status_str:
                                    task_status = PlanTaskStatus.IN_PROGRESS
                                elif "取消" in status_str or "cancelled" in status_str:
                                    task_status = PlanTaskStatus.CANCELLED

                    # 解析优先级
                    priority = "medium"
                    for col in df.columns:
                        if normalized_columns.get(col) == "priority":
                            if pd.notna(row[col]):
                                priority_str = str(row[col]).lower().strip()
                                if priority_str in ["low", "medium", "high", "critical", "低", "中", "高", "紧急"]:
                                    priority = priority_str

                    # 解析是否关键任务
                    is_critical = False
                    for col in df.columns:
                        if normalized_columns.get(col) == "is_critical":
                            if pd.notna(row[col]):
                                critical_str = str(row[col]).lower().strip()
                                if critical_str in ["是", "yes", "true", "1", "y"]:
                                    is_critical = True

                    # 解析依赖关系（暂时跳过，需要任务ID映射）
                    dependencies = []

                    # 创建任务
                    plan_task = ProjectPlanTask(
                        plan_id=plan.id,
                        category_id=task_type_category.id,  # 使用默认任务类型
                        name=task_name,
                        description=None,  # 可以从Excel读取，这里简化处理
                        start_date=start_date,
                        end_date=end_date,
                        duration_days=duration_days,
                        progress_percent=progress_percent,
                        status=task_status,
                        priority=priority,
                        is_critical=is_critical,
                        dependencies=dependencies,
                    )

                    db.add(plan_task)
                    tasks_created += 1

                except Exception as e:
                    tasks_failed += 1
                    errors.append(f"第{idx+2}行: {e!s}")
                    logger.error(f"导入任务失败（第{idx+2}行）: {e!s}", exc_info=True)

            db.commit()
            db.refresh(plan)

            return {
                "success": True,
                "plan_id": str(plan.id),
                "plan_name": plan.name,
                "tasks_created": tasks_created,
                "tasks_failed": tasks_failed,
                "errors": errors[:10],  # 只返回前10个错误
            }

        except Exception as e:
            db.rollback()
            logger.error(f"导入Excel失败: {e!s}", exc_info=True)
            raise ValueError(f"导入Excel失败: {e!s}")

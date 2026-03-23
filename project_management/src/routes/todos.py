"""
待办事项管理路由
"""

import contextlib
import logging
from datetime import datetime
from uuid import UUID

from database.src.core.session import get_db
from database.src.models.todo_models import Todo, TodoCategory, TodoPriority, TodoStatus
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic模型
class TodoCreate(BaseModel):
    """创建待办事项请求模型"""

    title: str
    description: str | None = None
    category: str | None = "work"
    priority: str | None = "medium"
    due_date: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    user_id: str | None = None  # 指定用户ID（用于分配给填报人）
    metadata: dict | None = None


class TodoUpdate(BaseModel):
    """更新待办事项请求模型"""

    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    due_date: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    metadata: dict | None = None


class TodoResponse(BaseModel):
    """待办事项响应模型"""

    id: str
    user_id: str
    title: str
    description: str | None = None
    category: str
    priority: str
    status: str
    due_date: str | None = None
    completed_at: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    project_name: str | None = None
    task_name: str | None = None
    metadata: dict | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TodoListResponse(BaseModel):
    """待办事项列表响应"""

    total: int
    items: list[TodoResponse]


class TodoStatisticsResponse(BaseModel):
    """待办事项统计响应"""

    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int
    high_priority: int
    medium_priority: int
    low_priority: int


@router.get("", response_model=TodoListResponse)
async def list_todos(
    status: str | None = Query(None, description="状态过滤"),
    category: str | None = Query(None, description="分类过滤"),
    priority: str | None = Query(None, description="优先级过滤"),
    project_id: str | None = Query(None, description="项目ID过滤"),
    overdue: bool | None = Query(None, description="是否过期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """获取待办事项列表"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的用户ID")

        # 如果指定了project_id，不限制user_id（因为待办可能是分配给填报人的）
        # 否则只查询当前用户的待办
        query = db.query(Todo) if project_id else db.query(Todo).filter(Todo.user_id == user_uuid)

        if status:
            try:
                todo_status = TodoStatus(status.lower())
                query = query.filter(Todo.status == todo_status)
            except ValueError:
                pass

        if category:
            try:
                todo_category = TodoCategory(category.lower())
                query = query.filter(Todo.category == todo_category)
            except ValueError:
                pass

        if priority:
            try:
                todo_priority = TodoPriority(priority.lower())
                query = query.filter(Todo.priority == todo_priority)
            except ValueError:
                pass

        if project_id:
            try:
                project_uuid = UUID(project_id)
                query = query.filter(Todo.project_id == project_uuid)
                # 显示该项目的所有待办，不过滤report_visible
                # 这样所有待办都会在进度报告中显示
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        if overdue is True:
            from datetime import datetime

            query = query.filter(
                Todo.due_date < datetime.now(), Todo.status != TodoStatus.COMPLETED, Todo.status != TodoStatus.CANCELLED
            )

        total = query.count()
        todos = (
            query.order_by(Todo.priority.desc(), Todo.due_date.asc(), Todo.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 获取项目名称和任务名称
        project_ids = {str(t.project_id) for t in todos if t.project_id}
        task_ids = {str(t.task_id) for t in todos if t.task_id}
        projects = {}
        tasks = {}

        if project_ids:
            from database.src.models.project_models import Project

            project_list = db.query(Project).filter(Project.id.in_([UUID(pid) for pid in project_ids])).all()
            projects = {str(p.id): p.name for p in project_list}

        if task_ids:
            from database.src.models.project_models import Task

            task_list = db.query(Task).filter(Task.id.in_([UUID(tid) for tid in task_ids])).all()
            tasks = {str(t.id): t.name for t in task_list}

        items = []
        for todo in todos:
            items.append(
                TodoResponse(
                    id=str(todo.id),
                    user_id=str(todo.user_id),
                    title=todo.title,
                    description=todo.description,
                    category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
                    priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
                    status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
                    due_date=todo.due_date.isoformat() if todo.due_date else None,
                    completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
                    project_id=str(todo.project_id) if todo.project_id else None,
                    task_id=str(todo.task_id) if todo.task_id else None,
                    project_name=projects.get(str(todo.project_id)) if todo.project_id else None,
                    task_name=tasks.get(str(todo.task_id)) if todo.task_id else None,
                    metadata=todo.extra_metadata,
                    created_at=todo.created_at.isoformat() if todo.created_at else "",
                    updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
                )
            )

        return TodoListResponse(total=total, items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待办事项列表失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取待办事项列表失败: {e!s}")


@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(todo_data: TodoCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """创建待办事项"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=401, detail="需要登录")

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的用户ID")

        # 解析分类
        category = TodoCategory.WORK
        if todo_data.category:
            try:
                category = TodoCategory(todo_data.category.lower())
            except ValueError:
                category = TodoCategory.WORK

        # 解析优先级
        priority = TodoPriority.MEDIUM
        if todo_data.priority:
            try:
                priority = TodoPriority(todo_data.priority.lower())
            except ValueError:
                priority = TodoPriority.MEDIUM

        # 解析截止日期
        due_date = None
        if todo_data.due_date:
            try:
                due_date = datetime.fromisoformat(todo_data.due_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    due_date = datetime.strptime(todo_data.due_date, "%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    due_date = datetime.strptime(todo_data.due_date, "%Y-%m-%d")

        # 解析项目ID和任务ID
        project_uuid = None
        if todo_data.project_id:
            try:
                project_uuid = UUID(todo_data.project_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的项目ID")

        task_uuid = None
        if todo_data.task_id:
            try:
                task_uuid = UUID(todo_data.task_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的任务ID")

        # 如果指定了user_id（用于分配给填报人），使用指定的user_id
        if todo_data.user_id:
            try:
                user_uuid = UUID(todo_data.user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的用户ID")

        # 准备metadata，如果是项目相关的待办，标记为在报告中显示
        metadata = todo_data.metadata or {}
        if project_uuid:
            metadata["report_visible"] = True

        # 创建待办事项
        todo = Todo(
            user_id=user_uuid,
            title=todo_data.title,
            description=todo_data.description,
            category=category,
            priority=priority,
            status=TodoStatus.PENDING,
            due_date=due_date,
            project_id=project_uuid,
            task_id=task_uuid,
            extra_metadata=metadata,
        )

        db.add(todo)
        db.commit()
        db.refresh(todo)

        return TodoResponse(
            id=str(todo.id),
            user_id=str(todo.user_id),
            title=todo.title,
            description=todo.description,
            category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
            priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
            status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
            due_date=todo.due_date.isoformat() if todo.due_date else None,
            completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
            project_id=str(todo.project_id) if todo.project_id else None,
            task_id=str(todo.task_id) if todo.task_id else None,
            metadata=todo.extra_metadata,
            created_at=todo.created_at.isoformat() if todo.created_at else "",
            updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建待办事项失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建待办事项失败: {e!s}")


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取待办事项详情"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            todo_uuid = UUID(todo_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        todo = db.query(Todo).filter(Todo.id == todo_uuid, Todo.user_id == user_uuid).first()

        if not todo:
            raise HTTPException(status_code=404, detail="待办事项不存在")

        # 获取项目名称和任务名称
        project_name = None
        task_name = None
        if todo.project_id:
            from database.src.models.project_models import Project

            project = db.query(Project).filter(Project.id == todo.project_id).first()
            if project:
                project_name = project.name

        if todo.task_id:
            from database.src.models.project_models import Task

            task = db.query(Task).filter(Task.id == todo.task_id).first()
            if task:
                task_name = task.name

        return TodoResponse(
            id=str(todo.id),
            user_id=str(todo.user_id),
            title=todo.title,
            description=todo.description,
            category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
            priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
            status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
            due_date=todo.due_date.isoformat() if todo.due_date else None,
            completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
            project_id=str(todo.project_id) if todo.project_id else None,
            task_id=str(todo.task_id) if todo.task_id else None,
            project_name=project_name,
            task_name=task_name,
            metadata=todo.extra_metadata,
            created_at=todo.created_at.isoformat() if todo.created_at else "",
            updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待办事项详情失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取待办事项详情失败: {e!s}")


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: str, todo_data: TodoUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """更新待办事项"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            todo_uuid = UUID(todo_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        todo = db.query(Todo).filter(Todo.id == todo_uuid, Todo.user_id == user_uuid).first()

        if not todo:
            raise HTTPException(status_code=404, detail="待办事项不存在")

        # 更新字段
        if todo_data.title is not None:
            todo.title = todo_data.title
        if todo_data.description is not None:
            todo.description = todo_data.description
        if todo_data.category is not None:
            with contextlib.suppress(ValueError):
                todo.category = TodoCategory(todo_data.category.lower())
        if todo_data.priority is not None:
            with contextlib.suppress(ValueError):
                todo.priority = TodoPriority(todo_data.priority.lower())
        if todo_data.status is not None:
            try:
                new_status = TodoStatus(todo_data.status.lower())
                todo.status = new_status
                # 如果状态变为已完成，设置完成时间
                if new_status == TodoStatus.COMPLETED and not todo.completed_at:
                    todo.completed_at = datetime.now()
                # 如果从已完成变为其他状态，清除完成时间
                elif new_status != TodoStatus.COMPLETED and todo.completed_at:
                    todo.completed_at = None
            except ValueError:
                pass
        if todo_data.due_date is not None:
            if todo_data.due_date:
                try:
                    todo.due_date = datetime.fromisoformat(todo_data.due_date.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    try:
                        todo.due_date = datetime.strptime(todo_data.due_date, "%Y-%m-%d %H:%M:%S")
                    except (ValueError, AttributeError):
                        todo.due_date = datetime.strptime(todo_data.due_date, "%Y-%m-%d")
            else:
                todo.due_date = None
        if todo_data.project_id is not None:
            if todo_data.project_id:
                try:
                    todo.project_id = UUID(todo_data.project_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="无效的项目ID")
            else:
                todo.project_id = None
        if todo_data.task_id is not None:
            if todo_data.task_id:
                try:
                    todo.task_id = UUID(todo_data.task_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="无效的任务ID")
            else:
                todo.task_id = None
        if todo_data.metadata is not None:
            todo.extra_metadata = todo_data.metadata

        db.commit()
        db.refresh(todo)

        # 获取项目名称和任务名称
        project_name = None
        task_name = None
        if todo.project_id:
            from database.src.models.project_models import Project

            project = db.query(Project).filter(Project.id == todo.project_id).first()
            if project:
                project_name = project.name

        if todo.task_id:
            from database.src.models.project_models import Task

            task = db.query(Task).filter(Task.id == todo.task_id).first()
            if task:
                task_name = task.name

        return TodoResponse(
            id=str(todo.id),
            user_id=str(todo.user_id),
            title=todo.title,
            description=todo.description,
            category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
            priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
            status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
            due_date=todo.due_date.isoformat() if todo.due_date else None,
            completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
            project_id=str(todo.project_id) if todo.project_id else None,
            task_id=str(todo.task_id) if todo.task_id else None,
            project_name=project_name,
            task_name=task_name,
            metadata=todo.extra_metadata,
            created_at=todo.created_at.isoformat() if todo.created_at else "",
            updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新待办事项失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新待办事项失败: {e!s}")


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """删除待办事项"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            todo_uuid = UUID(todo_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        todo = db.query(Todo).filter(Todo.id == todo_uuid, Todo.user_id == user_uuid).first()

        if not todo:
            raise HTTPException(status_code=404, detail="待办事项不存在")

        db.delete(todo)
        db.commit()

        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除待办事项失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除待办事项失败: {e!s}")


@router.patch("/{todo_id}/hide-from-report", response_model=TodoResponse)
async def hide_todo_from_report(
    todo_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)
):
    """从报告中隐藏待办事项（软删除）"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            todo_uuid = UUID(todo_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的待办ID")

        # 查找待办，不限制user_id，因为管理员可能为其他用户创建待办
        todo = db.query(Todo).filter(Todo.id == todo_uuid).first()

        if not todo:
            raise HTTPException(status_code=404, detail="待办事项不存在")

        # 更新metadata，设置report_visible为false
        if todo.extra_metadata is None:
            todo.extra_metadata = {}
        todo.extra_metadata["report_visible"] = False

        db.commit()
        db.refresh(todo)

        # 获取项目名称和任务名称
        project_name = None
        task_name = None
        if todo.project_id:
            from database.src.models.project_models import Project

            project = db.query(Project).filter(Project.id == todo.project_id).first()
            if project:
                project_name = project.name

        if todo.task_id:
            from database.src.models.project_models import Task

            task = db.query(Task).filter(Task.id == todo.task_id).first()
            if task:
                task_name = task.name

        return TodoResponse(
            id=str(todo.id),
            user_id=str(todo.user_id),
            title=todo.title,
            description=todo.description,
            category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
            priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
            status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
            due_date=todo.due_date.isoformat() if todo.due_date else None,
            completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
            project_id=str(todo.project_id) if todo.project_id else None,
            task_id=str(todo.task_id) if todo.task_id else None,
            project_name=project_name,
            task_name=task_name,
            metadata=todo.extra_metadata,
            created_at=todo.created_at.isoformat() if todo.created_at else "",
            updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"隐藏待办事项失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"隐藏待办事项失败: {e!s}")


@router.patch("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: str, db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """完成待办事项"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            todo_uuid = UUID(todo_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的ID")

        todo = db.query(Todo).filter(Todo.id == todo_uuid, Todo.user_id == user_uuid).first()

        if not todo:
            raise HTTPException(status_code=404, detail="待办事项不存在")

        todo.status = TodoStatus.COMPLETED
        todo.completed_at = datetime.now()

        db.commit()
        db.refresh(todo)

        # 获取项目名称和任务名称
        project_name = None
        task_name = None
        if todo.project_id:
            from database.src.models.project_models import Project

            project = db.query(Project).filter(Project.id == todo.project_id).first()
            if project:
                project_name = project.name

        if todo.task_id:
            from database.src.models.project_models import Task

            task = db.query(Task).filter(Task.id == todo.task_id).first()
            if task:
                task_name = task.name

        return TodoResponse(
            id=str(todo.id),
            user_id=str(todo.user_id),
            title=todo.title,
            description=todo.description,
            category=todo.category.value if hasattr(todo.category, "value") else str(todo.category),
            priority=todo.priority.value if hasattr(todo.priority, "value") else str(todo.priority),
            status=todo.status.value if hasattr(todo.status, "value") else str(todo.status),
            due_date=todo.due_date.isoformat() if todo.due_date else None,
            completed_at=todo.completed_at.isoformat() if todo.completed_at else None,
            project_id=str(todo.project_id) if todo.project_id else None,
            task_id=str(todo.task_id) if todo.task_id else None,
            project_name=project_name,
            task_name=task_name,
            metadata=todo.extra_metadata,
            created_at=todo.created_at.isoformat() if todo.created_at else "",
            updated_at=todo.updated_at.isoformat() if todo.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完成待办事项失败: {e!s}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"完成待办事项失败: {e!s}")


@router.get("/statistics/summary", response_model=TodoStatisticsResponse)
async def get_todo_statistics(db: Session = Depends(get_db), current_user: dict = Depends(require_auth)):
    """获取待办事项统计"""
    try:
        user_id = current_user.get("user_id")
        if not user_id or user_id == "anonymous":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")

        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的用户ID")

        from datetime import datetime

        from sqlalchemy import and_

        # 基础查询
        base_query = db.query(Todo).filter(Todo.user_id == user_uuid)

        # 统计总数
        total = base_query.count()

        # 按状态统计
        pending = base_query.filter(Todo.status == TodoStatus.PENDING).count()
        in_progress = base_query.filter(Todo.status == TodoStatus.IN_PROGRESS).count()
        completed = base_query.filter(Todo.status == TodoStatus.COMPLETED).count()
        cancelled = base_query.filter(Todo.status == TodoStatus.CANCELLED).count()

        # 过期待办事项
        overdue = base_query.filter(
            and_(
                Todo.due_date < datetime.now(), Todo.status != TodoStatus.COMPLETED, Todo.status != TodoStatus.CANCELLED
            )
        ).count()

        # 按优先级统计
        high_priority = base_query.filter(Todo.priority == TodoPriority.HIGH).count()
        medium_priority = base_query.filter(Todo.priority == TodoPriority.MEDIUM).count()
        low_priority = base_query.filter(Todo.priority == TodoPriority.LOW).count()

        return TodoStatisticsResponse(
            total=total,
            pending=pending,
            in_progress=in_progress,
            completed=completed,
            cancelled=cancelled,
            overdue=overdue,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待办事项统计失败: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取待办事项统计失败: {e!s}")

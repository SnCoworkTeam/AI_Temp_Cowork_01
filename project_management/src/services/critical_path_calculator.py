"""
关键路径计算服务
使用关键路径法（CPM - Critical Path Method）计算项目计划的关键路径
支持缓存和增量计算优化
"""

import hashlib
import logging
from collections import defaultdict, deque
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from database.src.models.project_models import ProjectPlanTask

logger = logging.getLogger(__name__)

# 简单的内存缓存（可以后续替换为Redis）
_critical_path_cache: dict[str, dict] = {}
_cache_timestamps: dict[str, float] = {}
CACHE_TTL_SECONDS = 300  # 缓存5分钟


class CriticalPathCalculator:
    """关键路径计算器"""

    # 依赖类型常量
    DEPENDENCY_TYPE_FS = "FS"  # Finish-to-Start（默认）
    DEPENDENCY_TYPE_SS = "SS"  # Start-to-Start
    DEPENDENCY_TYPE_FF = "FF"  # Finish-to-Finish
    DEPENDENCY_TYPE_SF = "SF"  # Start-to-Finish

    @classmethod
    def _get_cache_key(cls, plan_id: UUID, task_ids: list[UUID]) -> str:
        """生成缓存键"""
        task_ids_str = ",".join(sorted([str(tid) for tid in task_ids]))
        key_str = f"{plan_id}:{task_ids_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    @classmethod
    def _get_cached_result(cls, cache_key: str) -> dict | None:
        """获取缓存结果"""
        import time

        if cache_key in _critical_path_cache:
            if cache_key in _cache_timestamps:
                age = time.time() - _cache_timestamps[cache_key]
                if age < CACHE_TTL_SECONDS:
                    return _critical_path_cache[cache_key]
                # 缓存过期，删除
                del _critical_path_cache[cache_key]
                del _cache_timestamps[cache_key]
        return None

    @classmethod
    def _set_cached_result(cls, cache_key: str, result: dict):
        """设置缓存结果"""
        import time

        _critical_path_cache[cache_key] = result
        _cache_timestamps[cache_key] = time.time()

    @classmethod
    def invalidate_cache(cls, plan_id: UUID):
        """使缓存失效"""
        keys_to_delete = [k for k in _critical_path_cache if str(plan_id) in k]
        for key in keys_to_delete:
            _critical_path_cache.pop(key, None)
            _cache_timestamps.pop(key, None)
        logger.info(f"已清除计划 {plan_id} 的关键路径缓存")

    @classmethod
    def calculate_critical_path(cls, plan_id: UUID, db: Session, use_cache: bool = True) -> dict:
        """
        计算项目计划的关键路径（带缓存）

        Args:
            plan_id: 计划ID
            db: 数据库会话
            use_cache: 是否使用缓存

        Returns:
            {
                "critical_path": [task_id1, task_id2, ...],
                "critical_tasks": {task_id: {...}},
                "project_duration": days,
                "early_start": date,
                "late_finish": date
            }
        """
        # 获取所有计划任务
        tasks = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan_id).all()

        # 尝试从缓存获取
        if use_cache:
            task_ids = [task.id for task in tasks]
            cache_key = cls._get_cache_key(plan_id, task_ids)
            cached_result = cls._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"从缓存获取关键路径: {plan_id}")
                return cached_result

        if not tasks:
            return {
                "critical_path": [],
                "critical_tasks": {},
                "project_duration": 0,
                "early_start": None,
                "late_finish": None,
            }

        # 构建任务图
        task_dict = {str(task.id): task for task in tasks}
        graph = cls._build_dependency_graph(tasks)

        # 前向计算（Forward Pass）：计算最早开始和最早结束时间
        cls._forward_pass(tasks, task_dict, graph)

        # 后向计算（Backward Pass）：计算最晚开始和最晚结束时间
        cls._backward_pass(tasks, task_dict, graph)

        # 计算浮动时间
        cls._calculate_float(tasks)

        # 识别关键路径
        critical_path = cls._identify_critical_path(tasks, task_dict, graph)

        # 更新数据库中的关键路径信息
        cls._update_task_critical_info(tasks, db)

        # 计算项目总工期
        project_duration, early_start, late_finish = cls._calculate_project_duration(tasks)

        result = {
            "critical_path": critical_path,
            "critical_tasks": {
                str(task.id): {
                    "name": task.name,
                    "is_critical": task.is_critical,
                    "total_float": task.total_float,
                    "early_start": task.early_start.isoformat() if task.early_start else None,
                    "early_finish": task.early_finish.isoformat() if task.early_finish else None,
                    "late_start": task.late_start.isoformat() if task.late_start else None,
                    "late_finish": task.late_finish.isoformat() if task.late_finish else None,
                }
                for task in tasks
                if task.is_critical
            },
            "project_duration": project_duration,
            "early_start": early_start.isoformat() if early_start else None,
            "late_finish": late_finish.isoformat() if late_finish else None,
        }

        # 缓存结果
        if use_cache:
            task_ids = [task.id for task in tasks]
            cache_key = cls._get_cache_key(plan_id, task_ids)
            cls._set_cached_result(cache_key, result)

        return result

    @classmethod
    def _build_dependency_graph(cls, tasks: list[ProjectPlanTask]) -> dict[str, list[dict]]:
        """构建依赖关系图"""
        graph = defaultdict(list)

        for task in tasks:
            task_id = str(task.id)
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        predecessor_id = dep["task_id"]
                        dep_type = dep.get("type", cls.DEPENDENCY_TYPE_FS)
                        lag_days = dep.get("lag_days", 0)

                        graph[predecessor_id].append({"task_id": task_id, "type": dep_type, "lag_days": lag_days})

        return graph

    @classmethod
    def _forward_pass(cls, tasks: list[ProjectPlanTask], task_dict: dict, graph: dict):
        """前向计算：计算最早开始和最早结束时间"""
        # 找到所有没有前置任务的任务（起始任务）
        all_task_ids = {str(task.id) for task in tasks}
        tasks_with_predecessors = set()

        for task in tasks:
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        tasks_with_predecessors.add(str(task.id))

        start_tasks = [task for task in tasks if str(task.id) not in tasks_with_predecessors]

        # 使用拓扑排序处理任务
        in_degree = defaultdict(int)
        for task in tasks:
            task_id = str(task.id)
            if task.dependencies:
                in_degree[task_id] = len(task.dependencies)
            else:
                in_degree[task_id] = 0

        queue = deque([task for task in tasks if in_degree[str(task.id)] == 0])

        while queue:
            current_task = queue.popleft()
            current_id = str(current_task.id)

            # 计算最早开始时间（ES）
            if not current_task.dependencies:
                # 没有前置任务，使用计划开始日期或任务开始日期
                if current_task.start_date:
                    current_task.early_start = current_task.start_date
                else:
                    # 使用计划开始日期
                    plan = current_task.plan
                    if plan and plan.start_date:
                        current_task.early_start = plan.start_date
                    else:
                        current_task.early_start = date.today()
            else:
                # 有前置任务，ES = max(所有前置任务的EF) + lag_days
                max_early_finish = None
                for dep in current_task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        predecessor_id = dep["task_id"]
                        predecessor = task_dict.get(predecessor_id)
                        if predecessor and predecessor.early_finish:
                            lag_days = dep.get("lag_days", 0)
                            dep_type = dep.get("type", cls.DEPENDENCY_TYPE_FS)

                            if dep_type == cls.DEPENDENCY_TYPE_FS:
                                # Finish-to-Start: ES = EF + lag
                                ef_date = predecessor.early_finish + timedelta(days=lag_days)
                            elif dep_type == cls.DEPENDENCY_TYPE_SS:
                                # Start-to-Start: ES = ES + lag
                                ef_date = (
                                    predecessor.early_start + timedelta(days=lag_days)
                                    if predecessor.early_start
                                    else None
                                )
                            elif dep_type == cls.DEPENDENCY_TYPE_FF:
                                # Finish-to-Finish: ES = EF - duration + lag
                                if predecessor.early_finish and current_task.duration_days:
                                    ef_date = (
                                        predecessor.early_finish
                                        - timedelta(days=current_task.duration_days)
                                        + timedelta(days=lag_days)
                                    )
                                else:
                                    ef_date = (
                                        predecessor.early_finish + timedelta(days=lag_days)
                                        if predecessor.early_finish
                                        else None
                                    )
                            # Start-to-Finish: ES = ES - duration + lag
                            elif predecessor.early_start and current_task.duration_days:
                                ef_date = (
                                    predecessor.early_start
                                    - timedelta(days=current_task.duration_days)
                                    + timedelta(days=lag_days)
                                )
                            else:
                                ef_date = (
                                    predecessor.early_start + timedelta(days=lag_days)
                                    if predecessor.early_start
                                    else None
                                )

                            if ef_date and (max_early_finish is None or ef_date > max_early_finish):
                                max_early_finish = ef_date

                if max_early_finish:
                    current_task.early_start = max_early_finish
                elif current_task.start_date:
                    current_task.early_start = current_task.start_date
                else:
                    current_task.early_start = date.today()

            # 计算最早结束时间（EF = ES + duration）
            if current_task.duration_days:
                current_task.early_finish = current_task.early_start + timedelta(days=current_task.duration_days)
            elif current_task.end_date and current_task.early_start:
                # 如果没有duration，使用end_date
                current_task.early_finish = current_task.end_date
            else:
                current_task.early_finish = current_task.early_start

            # 处理后续任务
            if current_id in graph:
                for successor_info in graph[current_id]:
                    successor_id = successor_info["task_id"]
                    successor = task_dict.get(successor_id)
                    if successor:
                        in_degree[successor_id] -= 1
                        if in_degree[successor_id] == 0:
                            queue.append(successor)

    @classmethod
    def _backward_pass(cls, tasks: list[ProjectPlanTask], task_dict: dict, graph: dict):
        """后向计算：计算最晚开始和最晚结束时间"""
        # 找到所有没有后续任务的任务（结束任务）
        all_task_ids = {str(task.id) for task in tasks}
        tasks_with_successors = set()

        for task_id, successors in graph.items():
            tasks_with_successors.add(task_id)

        end_tasks = [task for task in tasks if str(task.id) not in tasks_with_successors]

        # 如果没有明确的结束任务，使用最晚的early_finish作为项目结束时间
        if end_tasks:
            project_end_date = max([task.early_finish for task in end_tasks if task.early_finish], default=None)
        else:
            project_end_date = max([task.early_finish for task in tasks if task.early_finish], default=None)

        if not project_end_date:
            project_end_date = date.today()

        # 初始化所有任务的最晚结束时间为项目结束日期
        for task in tasks:
            task.late_finish = project_end_date

        # 反向拓扑排序
        out_degree = defaultdict(int)
        reverse_graph = defaultdict(list)

        for task in tasks:
            task_id = str(task.id)
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        predecessor_id = dep["task_id"]
                        reverse_graph[task_id].append(
                            {
                                "predecessor_id": predecessor_id,
                                "type": dep.get("type", cls.DEPENDENCY_TYPE_FS),
                                "lag_days": dep.get("lag_days", 0),
                            }
                        )
                        out_degree[predecessor_id] += 1

        queue = deque(end_tasks)

        while queue:
            current_task = queue.popleft()
            current_id = str(current_task.id)

            # 计算最晚开始时间（LS = LF - duration）
            if current_task.duration_days:
                current_task.late_start = current_task.late_finish - timedelta(days=current_task.duration_days)
            elif current_task.end_date and current_task.late_finish:
                # 如果没有duration，使用end_date
                current_task.late_start = current_task.late_finish - timedelta(
                    days=(current_task.late_finish - current_task.end_date).days
                )
            else:
                current_task.late_start = current_task.late_finish

            # 更新前置任务的最晚结束时间
            if current_id in reverse_graph:
                for dep_info in reverse_graph[current_id]:
                    predecessor_id = dep_info["predecessor_id"]
                    predecessor = task_dict.get(predecessor_id)
                    if predecessor:
                        lag_days = dep_info["lag_days"]
                        dep_type = dep_info["type"]

                        if dep_type == cls.DEPENDENCY_TYPE_FS:
                            # Finish-to-Start: LF = LS - lag
                            lf_date = current_task.late_start - timedelta(days=lag_days)
                        elif dep_type == cls.DEPENDENCY_TYPE_SS:
                            # Start-to-Start: LF = LS - duration - lag
                            if current_task.late_start and current_task.duration_days:
                                lf_date = (
                                    current_task.late_start
                                    - timedelta(days=current_task.duration_days)
                                    - timedelta(days=lag_days)
                                )
                            else:
                                lf_date = (
                                    current_task.late_start - timedelta(days=lag_days)
                                    if current_task.late_start
                                    else None
                                )
                        elif dep_type == cls.DEPENDENCY_TYPE_FF:
                            # Finish-to-Finish: LF = LF - lag
                            lf_date = current_task.late_finish - timedelta(days=lag_days)
                        else:  # SF
                            # Start-to-Finish: LF = LS - lag
                            lf_date = (
                                current_task.late_start - timedelta(days=lag_days) if current_task.late_start else None
                            )

                        if lf_date and (predecessor.late_finish is None or lf_date < predecessor.late_finish):
                            predecessor.late_finish = lf_date

                        out_degree[predecessor_id] -= 1
                        if out_degree[predecessor_id] == 0:
                            queue.append(predecessor)

    @classmethod
    def _calculate_float(cls, tasks: list[ProjectPlanTask]):
        """计算浮动时间"""
        for task in tasks:
            if task.early_start and task.late_start:
                # 总浮动时间 = LS - ES = LF - EF
                total_float = (task.late_start - task.early_start).days
                task.total_float = float(total_float)
            else:
                task.total_float = None

            # 自由浮动时间 = min(后续任务的ES) - EF
            if task.early_finish:
                # 找到所有后续任务
                successors_early_start = []
                for other_task in tasks:
                    if other_task.dependencies:
                        for dep in other_task.dependencies:
                            if isinstance(dep, dict) and dep.get("task_id") == str(task.id):
                                if other_task.early_start:
                                    successors_early_start.append(other_task.early_start)

                if successors_early_start:
                    min_successor_es = min(successors_early_start)
                    free_float = (min_successor_es - task.early_finish).days
                    task.free_float = float(max(0, free_float))
                else:
                    task.free_float = task.total_float
            else:
                task.free_float = None

    @classmethod
    def _identify_critical_path(cls, tasks: list[ProjectPlanTask], task_dict: dict, graph: dict) -> list[str]:
        """识别关键路径"""
        critical_path = []

        # 关键任务：总浮动时间为0或负数的任务
        critical_tasks = [task for task in tasks if task.total_float is not None and task.total_float <= 0]

        # 标记关键任务
        for task in tasks:
            task.is_critical = task.total_float is not None and task.total_float <= 0

        # 构建关键路径：从起始关键任务到结束关键任务
        if not critical_tasks:
            return []

        # 找到起始关键任务（没有前置关键任务）
        start_critical_tasks = []
        for task in critical_tasks:
            has_critical_predecessor = False
            if task.dependencies:
                for dep in task.dependencies:
                    if isinstance(dep, dict) and "task_id" in dep:
                        predecessor_id = dep["task_id"]
                        predecessor = task_dict.get(predecessor_id)
                        if predecessor and predecessor.is_critical:
                            has_critical_predecessor = True
                            break
            if not has_critical_predecessor:
                start_critical_tasks.append(task)

        # 从起始关键任务开始，沿着关键任务链构建路径
        if start_critical_tasks:
            # 选择最早开始的起始关键任务
            start_task = min(start_critical_tasks, key=lambda t: t.early_start if t.early_start else date.max)
            current_task = start_task
            visited = set()

            while current_task and str(current_task.id) not in visited:
                visited.add(str(current_task.id))
                critical_path.append(str(current_task.id))

                # 找到下一个关键任务
                next_critical_task = None
                if str(current_task.id) in graph:
                    for successor_info in graph[str(current_task.id)]:
                        successor_id = successor_info["task_id"]
                        successor = task_dict.get(successor_id)
                        if successor and successor.is_critical and str(successor.id) not in visited:
                            if next_critical_task is None or (
                                successor.early_start
                                and next_critical_task.early_start
                                and successor.early_start < next_critical_task.early_start
                            ):
                                next_critical_task = successor

                current_task = next_critical_task

        return critical_path

    @classmethod
    def _update_task_critical_info(cls, tasks: list[ProjectPlanTask], db: Session):
        """更新任务的关键路径信息到数据库"""
        for task in tasks:
            db.merge(task)
        db.commit()

    @classmethod
    def _calculate_project_duration(cls, tasks: list[ProjectPlanTask]) -> tuple:
        """计算项目总工期"""
        if not tasks:
            return 0, None, None

        early_starts = [task.early_start for task in tasks if task.early_start]
        late_finishes = [task.late_finish for task in tasks if task.late_finish]

        if not early_starts or not late_finishes:
            return 0, None, None

        early_start = min(early_starts)
        late_finish = max(late_finishes)
        duration = (late_finish - early_start).days

        return duration, early_start, late_finish

    @classmethod
    def calculate_incremental(cls, plan_id: UUID, changed_task_ids: list[UUID], db: Session) -> dict:
        """
        增量计算：只重新计算受影响的任务

        Args:
            plan_id: 计划ID
            changed_task_ids: 变更的任务ID列表
            db: 数据库会话

        Returns:
            关键路径计算结果
        """
        # 获取所有任务
        all_tasks = db.query(ProjectPlanTask).filter(ProjectPlanTask.plan_id == plan_id).all()

        # 识别受影响的任务（依赖链）
        affected_task_ids = cls._get_affected_tasks(plan_id, changed_task_ids, db, all_tasks)

        # 重新计算受影响的任务
        for task_id in affected_task_ids:
            task = next((t for t in all_tasks if t.id == task_id), None)
            if task:
                # 重新计算该任务的时间
                cls._recalculate_task_times(task, all_tasks, db)

        # 更新关键路径
        return cls.calculate_critical_path(plan_id, db)

    @classmethod
    def _get_affected_tasks(
        cls, plan_id: UUID, changed_task_ids: list[UUID], db: Session, all_tasks: list[ProjectPlanTask]
    ) -> set[UUID]:
        """获取受影响的任务ID集合（包括后续任务）"""
        affected = set(changed_task_ids)
        task_dict = {task.id: task for task in all_tasks}

        # 使用BFS找到所有后续任务
        queue = deque(changed_task_ids)
        visited = set(changed_task_ids)

        while queue:
            current_id = queue.popleft()
            current_task = task_dict.get(current_id)

            if current_task:
                # 找到所有后续任务
                for task in all_tasks:
                    if task.dependencies:
                        for dep in task.dependencies:
                            if isinstance(dep, dict) and dep.get("task_id") == str(current_id):
                                if task.id not in visited:
                                    visited.add(task.id)
                                    affected.add(task.id)
                                    queue.append(task.id)

        return affected

    @classmethod
    def _recalculate_task_times(cls, task: ProjectPlanTask, all_tasks: list[ProjectPlanTask], db: Session):
        """重新计算单个任务的时间"""
        # 这里可以调用前向/后向计算的逻辑
        # 简化实现：直接重新计算整个计划
        # 实际实现中会调用相应的计算方法

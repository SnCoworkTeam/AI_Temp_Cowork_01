"""
智能体执行协调模型
提供并行、串行、流水线等多种执行模式的协调控制
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set, Callable, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import uuid
import logging
import heapq

from shared_libs.luminaos_common.schemas.agent_communication import (
    ExecutionMode, CoordinationState, SynchronizationPoint,
    ExecutionStartMessage, ExecutionCompleteMessage, ExecutionFailedMessage,
    AgentMessage, MessageHeader, MessageType
)

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """执行策略"""
    GREEDY = "greedy"                   # 贪心策略
    OPTIMIZED = "optimized"             # 优化策略
    FAIR_SHARE = "fair_share"           # 公平共享
    PRIORITY_BASED = "priority_based"   # 基于优先级
    RESOURCE_AWARE = "resource_aware"   # 资源感知


class NodeStatus(str, Enum):
    """节点状态"""
    IDLE = "idle"
    PREPARING = "preparing"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DependencyType(str, Enum):
    """依赖类型"""
    DATA = "data"                       # 数据依赖
    EXECUTION = "execution"             # 执行依赖
    RESOURCE = "resource"               # 资源依赖
    TIMING = "timing"                   # 时序依赖


@dataclass
class NodeDescriptor:
    """节点描述符"""
    node_id: str
    agent_id: str
    node_type: str
    priority: int = 0
    estimated_duration: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    input_ports: List[str] = field(default_factory=list)
    output_ports: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dependency:
    """依赖关系"""
    source_node: str
    target_node: str
    dependency_type: DependencyType
    dependency_data: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False
    timeout: Optional[int] = None


@dataclass
class ExecutionTask:
    """执行任务"""
    task_id: str
    node_id: str
    agent_id: str
    input_data: Dict[str, Any]
    configuration: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    scheduled_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: NodeStatus = NodeStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: str
    node_id: str
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.now)


class ExecutionGraph:
    """执行图"""

    def __init__(self):
        self.nodes: Dict[str, NodeDescriptor] = {}
        self.dependencies: List[Dependency] = []
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency_list: Dict[str, List[str]] = defaultdict(list)
        self.in_degrees: Dict[str, int] = defaultdict(int)

    def add_node(self, node: NodeDescriptor):
        """添加节点"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.in_degrees:
            self.in_degrees[node.node_id] = 0

    def add_dependency(self, dependency: Dependency):
        """添加依赖关系"""
        self.dependencies.append(dependency)
        self.adjacency_list[dependency.source_node].append(dependency.target_node)
        self.reverse_adjacency_list[dependency.target_node].append(dependency.source_node)
        self.in_degrees[dependency.target_node] += 1

    def get_ready_nodes(self, completed_nodes: Set[str]) -> List[str]:
        """获取就绪节点"""
        ready_nodes = []

        for node_id in self.nodes:
            if node_id in completed_nodes:
                continue

            # 检查所有依赖是否满足
            dependencies = self.reverse_adjacency_list.get(node_id, [])
            if all(dep_node in completed_nodes for dep_node in dependencies):
                ready_nodes.append(node_id)

        return ready_nodes

    def topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree_copy = self.in_degrees.copy()
        queue = deque([node for node, degree in in_degree_copy.items() if degree == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in self.adjacency_list[current]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)

        return result if len(result) == len(self.nodes) else []  # 检测环

    def get_parallel_groups(self) -> List[List[str]]:
        """获取可并行执行的节点组"""
        topo_order = self.topological_sort()
        if not topo_order:
            return []

        levels = {}
        for node in topo_order:
            dependencies = self.reverse_adjacency_list.get(node, [])
            if not dependencies:
                levels[node] = 0
            else:
                levels[node] = max(levels[dep] for dep in dependencies) + 1

        # 按级别分组
        groups = defaultdict(list)
        for node, level in levels.items():
            groups[level].append(node)

        return [groups[level] for level in sorted(groups.keys())]

    def find_critical_path(self) -> Tuple[List[str], float]:
        """查找关键路径"""
        # 简化的关键路径计算
        topo_order = self.topological_sort()
        if not topo_order:
            return [], 0.0

        # 计算最早开始时间
        earliest_start = {}
        for node in topo_order:
            dependencies = self.reverse_adjacency_list.get(node, [])
            if not dependencies:
                earliest_start[node] = 0.0
            else:
                max_finish_time = 0.0
                for dep in dependencies:
                    finish_time = earliest_start[dep] + self.nodes[dep].estimated_duration
                    max_finish_time = max(max_finish_time, finish_time)
                earliest_start[node] = max_finish_time

        # 找到项目完成时间
        project_duration = max(
            earliest_start[node] + self.nodes[node].estimated_duration
            for node in self.nodes
        )

        # 反向计算最晚开始时间
        latest_start = {}
        for node in reversed(topo_order):
            successors = self.adjacency_list.get(node, [])
            if not successors:
                latest_start[node] = project_duration - self.nodes[node].estimated_duration
            else:
                min_latest_start = float('inf')
                for successor in successors:
                    min_latest_start = min(min_latest_start, latest_start[successor])
                latest_start[node] = min_latest_start - self.nodes[node].estimated_duration

        # 找到关键路径上的节点（总时差为0的节点）
        critical_nodes = [
            node for node in self.nodes
            if abs(earliest_start[node] - latest_start[node]) < 1e-6
        ]

        return critical_nodes, project_duration

    def validate_graph(self) -> Tuple[bool, List[str]]:
        """验证图的有效性"""
        errors = []

        # 检查环
        if not self.topological_sort():
            errors.append("图中存在环形依赖")

        # 检查孤立节点
        for node_id in self.nodes:
            if (node_id not in self.adjacency_list and
                node_id not in self.reverse_adjacency_list):
                if len(self.nodes) > 1:  # 只有一个节点时不算孤立
                    errors.append(f"节点 {node_id} 是孤立节点")

        # 检查无效依赖
        for dep in self.dependencies:
            if dep.source_node not in self.nodes:
                errors.append(f"依赖源节点不存在: {dep.source_node}")
            if dep.target_node not in self.nodes:
                errors.append(f"依赖目标节点不存在: {dep.target_node}")

        return len(errors) == 0, errors


class SequentialExecutor:
    """串行执行器"""

    def __init__(self):
        self.current_task: Optional[ExecutionTask] = None
        self.execution_queue: deque = deque()
        self.completed_tasks: List[ExecutionResult] = []

    async def execute_workflow(
        self,
        execution_graph: ExecutionGraph,
        input_data: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """执行工作流"""
        # 拓扑排序获取执行顺序
        execution_order = execution_graph.topological_sort()
        if not execution_order:
            raise ValueError("工作流图包含环形依赖")

        results = []
        context_data = input_data.copy()

        for node_id in execution_order:
            node = execution_graph.nodes[node_id]
            task = ExecutionTask(
                task_id=str(uuid.uuid4()),
                node_id=node_id,
                agent_id=node.agent_id,
                input_data=context_data,
                configuration=node.configuration
            )

            result = await self._execute_task(task)
            results.append(result)

            # 更新上下文数据
            if result.success:
                context_data.update(result.output_data)
            else:
                # 串行执行中如果任务失败，停止执行
                logger.error(f"任务执行失败，停止工作流: {result.error_message}")
                break

        return results

    async def _execute_task(self, task: ExecutionTask) -> ExecutionResult:
        """执行单个任务"""
        start_time = datetime.now()
        task.status = NodeStatus.EXECUTING

        try:
            # 模拟任务执行
            await asyncio.sleep(0.1)  # 模拟执行时间

            # 这里应该调用实际的智能体执行
            output_data = {"result": f"executed_{task.node_id}"}

            execution_time = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=True,
                output_data=output_data,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class ParallelExecutor:
    """并行执行器"""

    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency
        self.running_tasks: Dict[str, ExecutionTask] = {}
        self.completed_tasks: Dict[str, ExecutionResult] = {}
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_workflow(
        self,
        execution_graph: ExecutionGraph,
        input_data: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """并行执行工作流"""
        parallel_groups = execution_graph.get_parallel_groups()
        if not parallel_groups:
            raise ValueError("无法生成并行执行组")

        all_results = []
        context_data = input_data.copy()

        for group in parallel_groups:
            # 并行执行当前组
            group_tasks = []
            for node_id in group:
                node = execution_graph.nodes[node_id]
                task = ExecutionTask(
                    task_id=str(uuid.uuid4()),
                    node_id=node_id,
                    agent_id=node.agent_id,
                    input_data=context_data.copy(),
                    configuration=node.configuration
                )
                group_tasks.append(task)

            # 等待当前组完成
            group_results = await self._execute_parallel_group(group_tasks)
            all_results.extend(group_results)

            # 更新上下文数据
            for result in group_results:
                if result.success:
                    context_data.update(result.output_data)

        return all_results

    async def _execute_parallel_group(self, tasks: List[ExecutionTask]) -> List[ExecutionResult]:
        """并行执行任务组"""
        async def execute_with_semaphore(task):
            async with self.semaphore:
                return await self._execute_task(task)

        # 创建协程
        coroutines = [execute_with_semaphore(task) for task in tasks]

        # 并行执行
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 创建失败结果
                failed_result = ExecutionResult(
                    task_id=tasks[i].task_id,
                    node_id=tasks[i].node_id,
                    success=False,
                    error_message=str(result)
                )
                final_results.append(failed_result)
            else:
                final_results.append(result)

        return final_results

    async def _execute_task(self, task: ExecutionTask) -> ExecutionResult:
        """执行单个任务"""
        start_time = datetime.now()
        task.status = NodeStatus.EXECUTING

        try:
            # 模拟任务执行
            await asyncio.sleep(0.1)  # 模拟执行时间

            output_data = {"result": f"parallel_executed_{task.node_id}"}
            execution_time = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=True,
                output_data=output_data,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class PipelineExecutor:
    """流水线执行器"""

    def __init__(self, buffer_size: int = 10):
        self.buffer_size = buffer_size
        self.stage_queues: Dict[str, asyncio.Queue] = {}
        self.stage_workers: Dict[str, asyncio.Task] = {}
        self.pipeline_running = False

    async def execute_workflow(
        self,
        execution_graph: ExecutionGraph,
        input_data: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """流水线执行工作流"""
        # 获取拓扑顺序作为流水线阶段
        pipeline_stages = execution_graph.topological_sort()
        if not pipeline_stages:
            raise ValueError("无法创建流水线：图中存在环")

        # 初始化阶段队列
        for stage in pipeline_stages:
            self.stage_queues[stage] = asyncio.Queue(maxsize=self.buffer_size)

        # 启动流水线
        self.pipeline_running = True
        results = []

        try:
            # 启动阶段工作器
            for i, stage in enumerate(pipeline_stages):
                node = execution_graph.nodes[stage]
                worker = asyncio.create_task(
                    self._stage_worker(
                        stage,
                        node,
                        self.stage_queues.get(pipeline_stages[i - 1]) if i > 0 else None,
                        self.stage_queues[stage],
                        results
                    )
                )
                self.stage_workers[stage] = worker

            # 输入初始数据
            first_stage = pipeline_stages[0]
            await self.stage_queues[first_stage].put(input_data)

            # 等待所有阶段完成
            await asyncio.gather(*self.stage_workers.values())

        finally:
            self.pipeline_running = False

        return results

    async def _stage_worker(
        self,
        stage_id: str,
        node: NodeDescriptor,
        input_queue: Optional[asyncio.Queue],
        output_queue: asyncio.Queue,
        results: List[ExecutionResult]
    ):
        """阶段工作器"""
        while self.pipeline_running:
            try:
                # 获取输入数据
                if input_queue:
                    data = await asyncio.wait_for(input_queue.get(), timeout=1.0)
                else:
                    # 第一个阶段，等待外部输入
                    data = await asyncio.wait_for(output_queue.get(), timeout=1.0)

                # 执行任务
                task = ExecutionTask(
                    task_id=str(uuid.uuid4()),
                    node_id=stage_id,
                    agent_id=node.agent_id,
                    input_data=data,
                    configuration=node.configuration
                )

                result = await self._execute_task(task)
                results.append(result)

                # 输出到下一阶段
                if result.success and output_queue:
                    await output_queue.put(result.output_data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"流水线阶段 {stage_id} 执行失败: {e}")
                break

    async def _execute_task(self, task: ExecutionTask) -> ExecutionResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 模拟流水线执行
            await asyncio.sleep(0.1)

            output_data = {
                "result": f"pipeline_executed_{task.node_id}",
                "processed_at": datetime.now().isoformat()
            }

            execution_time = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=True,
                output_data=output_data,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                task_id=task.task_id,
                node_id=task.node_id,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )


class SmartExecutor:
    """智能执行器"""

    def __init__(self):
        self.execution_strategy = ExecutionStrategy.OPTIMIZED
        self.resource_pool: Dict[str, Any] = {}
        self.node_performance_history: Dict[str, List[float]] = defaultdict(list)
        self.load_balancer = None

    async def execute_workflow(
        self,
        execution_graph: ExecutionGraph,
        input_data: Dict[str, Any],
        strategy: ExecutionStrategy = None
    ) -> List[ExecutionResult]:
        """智能执行工作流"""
        if strategy:
            self.execution_strategy = strategy

        # 分析图结构选择最优执行模式
        execution_mode = self._choose_execution_mode(execution_graph)

        if execution_mode == ExecutionMode.SEQUENTIAL:
            executor = SequentialExecutor()
        elif execution_mode == ExecutionMode.PARALLEL:
            executor = ParallelExecutor()
        elif execution_mode == ExecutionMode.PIPELINE:
            executor = PipelineExecutor()
        else:
            # 混合模式
            return await self._execute_hybrid_mode(execution_graph, input_data)

        return await executor.execute_workflow(execution_graph, input_data)

    def _choose_execution_mode(self, graph: ExecutionGraph) -> ExecutionMode:
        """选择执行模式"""
        # 分析图的特征
        node_count = len(graph.nodes)
        dependency_count = len(graph.dependencies)
        parallel_groups = graph.get_parallel_groups()
        max_parallelism = max(len(group) for group in parallel_groups) if parallel_groups else 1

        # 决策逻辑
        if node_count <= 3:
            return ExecutionMode.SEQUENTIAL

        if max_parallelism >= 3 and dependency_count / node_count < 0.5:
            return ExecutionMode.PARALLEL

        if len(parallel_groups) >= 3 and max_parallelism <= 2:
            return ExecutionMode.PIPELINE

        return ExecutionMode.PARALLEL  # 默认并行

    async def _execute_hybrid_mode(
        self,
        graph: ExecutionGraph,
        input_data: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """混合模式执行"""
        # 将图分割为子图，每个子图使用不同的执行模式
        subgraphs = self._partition_graph(graph)
        all_results = []

        for subgraph, mode in subgraphs:
            if mode == ExecutionMode.SEQUENTIAL:
                executor = SequentialExecutor()
            elif mode == ExecutionMode.PARALLEL:
                executor = ParallelExecutor()
            else:
                executor = PipelineExecutor()

            subgraph_results = await executor.execute_workflow(subgraph, input_data)
            all_results.extend(subgraph_results)

            # 更新输入数据为下一个子图
            for result in subgraph_results:
                if result.success:
                    input_data.update(result.output_data)

        return all_results

    def _partition_graph(self, graph: ExecutionGraph) -> List[Tuple[ExecutionGraph, ExecutionMode]]:
        """分割图为子图"""
        # 简化实现：返回原图
        return [(graph, ExecutionMode.PARALLEL)]

    def update_performance_metrics(self, node_id: str, execution_time: float):
        """更新性能指标"""
        self.node_performance_history[node_id].append(execution_time)

        # 保持历史记录大小
        if len(self.node_performance_history[node_id]) > 100:
            self.node_performance_history[node_id] = self.node_performance_history[node_id][-50:]

    def get_estimated_execution_time(self, graph: ExecutionGraph) -> float:
        """估算执行时间"""
        critical_path, duration = graph.find_critical_path()
        return duration

    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {}
        for node_id, times in self.node_performance_history.items():
            if times:
                stats[node_id] = {
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'execution_count': len(times)
                }
        return stats


# ==================== 使用示例 ====================

async def example_execution_coordination():
    """执行协调使用示例"""

    # 创建执行图
    graph = ExecutionGraph()

    # 添加节点
    nodes = [
        NodeDescriptor("node_1", "agent_1", "input", priority=1, estimated_duration=2.0),
        NodeDescriptor("node_2", "agent_2", "process", priority=2, estimated_duration=3.0),
        NodeDescriptor("node_3", "agent_3", "process", priority=2, estimated_duration=2.5),
        NodeDescriptor("node_4", "agent_4", "output", priority=3, estimated_duration=1.0),
    ]

    for node in nodes:
        graph.add_node(node)

    # 添加依赖关系
    dependencies = [
        Dependency("node_1", "node_2", DependencyType.DATA),
        Dependency("node_1", "node_3", DependencyType.DATA),
        Dependency("node_2", "node_4", DependencyType.DATA),
        Dependency("node_3", "node_4", DependencyType.DATA),
    ]

    for dep in dependencies:
        graph.add_dependency(dep)

    # 验证图
    is_valid, errors = graph.validate_graph()
    print(f"图验证结果: {is_valid}")
    if not is_valid:
        print(f"验证错误: {errors}")

    # 分析关键路径
    critical_path, duration = graph.find_critical_path()
    print(f"关键路径: {critical_path}")
    print(f"预估时间: {duration}秒")

    # 并行执行组
    parallel_groups = graph.get_parallel_groups()
    print(f"并行执行组: {parallel_groups}")

    # 执行工作流
    smart_executor = SmartExecutor()
    input_data = {"initial_data": "test"}

    results = await smart_executor.execute_workflow(graph, input_data)

    print("执行结果:")
    for result in results:
        status = "成功" if result.success else "失败"
        print(f"  {result.node_id}: {status} ({result.execution_time:.2f}s)")

if __name__ == "__main__":
    asyncio.run(example_execution_coordination())
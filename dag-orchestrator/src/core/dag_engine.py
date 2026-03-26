"""
DAG核心引擎
负责任务编排和执行
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

from ..models.dag_models import (
    DAGPlan,
    TaskNode,
    TaskType,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from ..core.task_decomposer import TaskDecomposer
from ..services.backend_clients import BackendClients

logger = logging.getLogger(__name__)


class DAGEngine:
    """DAG执行引擎"""
    
    def __init__(self):
        self.task_decomposer = TaskDecomposer()
        self.backend_clients = BackendClients()
        self.execution_store: Dict[str, ExecutionResult] = {}
    
    def _generate_execution_id(self) -> str:
        """生成执行ID"""
        return f"exec_{uuid.uuid4().hex[:16]}"
    
    async def execute_complex_task(self, request: ExecutionRequest) -> ExecutionResult:
        """
        执行复杂任务的核心流程
        
        Args:
            request: 执行请求
            
        Returns:
            执行结果
        """
        execution_id = self._generate_execution_id()
        start_time = datetime.now()
        
        # 创建执行结果对象
        execution_result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            results={}
        )
        self.execution_store[execution_id] = execution_result
        
        try:
            logger.info(f"Starting execution {execution_id} for task: {request.user_input[:100]}")
            
            # 1. 任务分解：生成DAG执行计划
            dag_plan = await self.task_decomposer.decompose_task(
                request.user_input,
                request.context
            )
            execution_result.dag_id = dag_plan.dag_id
            
            # 更新状态为运行中
            execution_result.status = ExecutionStatus.RUNNING
            execution_result.started_at = datetime.now()
            
            # 2. 执行DAG
            final_output = await self._execute_dag(
                dag_plan,
                execution_result,
                request.context
            )
            
            # 3. 更新执行结果
            execution_result.final_output = final_output
            execution_result.status = ExecutionStatus.COMPLETED
            execution_result.completed_at = datetime.now()
            execution_result.execution_time = (
                execution_result.completed_at - execution_result.started_at
            ).total_seconds()
            
            logger.info(
                f"Execution {execution_id} completed in {execution_result.execution_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {str(e)}", exc_info=True)
            execution_result.status = ExecutionStatus.FAILED
            execution_result.error_message = str(e)
            execution_result.completed_at = datetime.now()
            if execution_result.started_at:
                execution_result.execution_time = (
                    execution_result.completed_at - execution_result.started_at
                ).total_seconds()
        
        return execution_result
    
    async def _execute_dag(
        self,
        dag_plan: DAGPlan,
        execution_result: ExecutionResult,
        context: Dict[str, Any]
    ) -> Any:
        """
        执行DAG计划
        
        Args:
            dag_plan: DAG执行计划
            execution_result: 执行结果对象（用于更新状态）
            context: 上下文信息
            
        Returns:
            最终输出结果
        """
        # 拓扑排序，确定执行顺序
        execution_order = self._topological_sort(dag_plan)
        
        logger.info(f"Executing DAG {dag_plan.dag_id} with {len(execution_order)} levels")
        
        # 按层级执行节点（支持并行）
        for level_idx, level_nodes in enumerate(execution_order):
            logger.info(f"Executing level {level_idx + 1}/{len(execution_order)}: {level_nodes}")
            
            # 并行执行同一层级的无依赖节点
            tasks = []
            for node_id in level_nodes:
                node = dag_plan.task_nodes[node_id]
                task = self._execute_node(node, context, execution_result)
                tasks.append((node_id, task))
            
            # 等待当前层级所有节点完成
            level_results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 处理节点结果
            for (node_id, _), result in zip(tasks, level_results):
                if isinstance(result, Exception):
                    logger.error(f"Node {node_id} execution failed: {str(result)}")
                    execution_result.results[node_id] = {
                        "success": False,
                        "error": str(result)
                    }
                    # 错误处理策略：继续执行其他节点
                else:
                    execution_result.results[node_id] = {
                        "success": True,
                        "result": result
                    }
                    # 更新上下文，供后续节点使用
                    context[f"node_{node_id}"] = result
                    logger.info(f"Node {node_id} completed successfully")
        
        # 聚合最终结果
        return await self._aggregate_results(dag_plan, execution_result.results)
    
    def _topological_sort(self, dag_plan: DAGPlan) -> List[List[str]]:
        """
        拓扑排序，返回按层级组织的节点列表
        
        Args:
            dag_plan: DAG计划
            
        Returns:
            按层级组织的节点列表，每个层级可以并行执行
        """
        # 构建依赖图
        in_degree = {node_id: 0 for node_id in dag_plan.task_nodes}
        graph = defaultdict(list)
        
        for node_id, node in dag_plan.task_nodes.items():
            for dep in node.dependencies:
                if dep in dag_plan.task_nodes:
                    graph[dep].append(node_id)
                    in_degree[node_id] += 1
        
        # 层级排序
        levels = []
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        
        while queue:
            level = []
            level_size = len(queue)
            
            for _ in range(level_size):
                node_id = queue.popleft()
                level.append(node_id)
                
                # 更新依赖节点的入度
                for neighbor in graph[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            if level:
                levels.append(level)
        
        return levels
    
    async def _execute_node(
        self,
        node: TaskNode,
        context: Dict[str, Any],
        execution_result: ExecutionResult
    ) -> Any:
        """
        执行单个节点任务
        
        Args:
            node: 任务节点
            context: 上下文信息
            execution_result: 执行结果对象
            
        Returns:
            节点执行结果
        """
        logger.info(f"Executing node {node.node_id}: {node.name} (type: {node.task_type})")
        
        # 合并上下文到参数中
        parameters = {**node.parameters}
        # 将上下文中的节点结果注入到参数中
        for key, value in context.items():
            if key.startswith("node_"):
                parameters[key] = value
        
        try:
            # 根据节点类型调用相应的后端服务
            if node.task_type == TaskType.MCP_TOOL:
                result = await self.backend_clients.call_mcp_gateway(
                    node.action,
                    parameters,
                    timeout=node.timeout
                )
                return result
            
            elif node.task_type == TaskType.WORKFLOW:
                # 工作流需要input_data参数
                input_data = parameters.get("input_data", parameters)
                result = await self.backend_clients.call_workflow_engine(
                    node.action,
                    input_data,
                    timeout=node.timeout
                )
                return result
            
            elif node.task_type == TaskType.KNOWLEDGE:
                result = await self.backend_clients.call_knowledge_base(
                    node.action,
                    parameters,
                    timeout=node.timeout
                )
                return result
            
            elif node.task_type == TaskType.CALCULATION:
                # 简单计算，直接在当前服务中执行
                return self._execute_calculation(node, parameters, context)
            
            else:
                raise ValueError(f"Unsupported task type: {node.task_type}")
                
        except Exception as e:
            logger.error(f"Node {node.node_id} execution error: {str(e)}")
            raise
    
    def _execute_calculation(self, node: TaskNode, parameters: Dict, context: Dict) -> Any:
        """
        执行简单计算任务
        
        Args:
            node: 任务节点
            parameters: 参数
            context: 上下文
            
        Returns:
            计算结果
        """
        # 简单的计算逻辑，可以根据需要扩展
        action = node.action.lower()
        
        if action == "aggregate" or action == "sum":
            # 聚合操作
            values = parameters.get("values", [])
            return sum(values) if isinstance(values, list) else 0
        
        elif action == "format" or action == "format_output":
            # 格式化输出
            template = parameters.get("template", "{result}")
            data = parameters.get("data", {})
            return template.format(**data)
        
        else:
            # 默认返回参数本身
            return parameters
    
    async def _aggregate_results(
        self,
        dag_plan: DAGPlan,
        node_results: Dict[str, Any]
    ) -> str:
        """
        聚合所有节点的执行结果
        
        Args:
            dag_plan: DAG计划
            node_results: 节点执行结果
            
        Returns:
            聚合后的最终输出
        """
        # 收集所有成功节点的结果
        successful_results = []
        
        for node_id in dag_plan.exit_nodes:
            if node_id in node_results:
                result_data = node_results[node_id]
                if result_data.get("success", False):
                    successful_results.append(result_data.get("result"))
        
        # 如果没有出口节点，收集所有节点的结果
        if not successful_results:
            for node_id, result_data in node_results.items():
                if result_data.get("success", False):
                    successful_results.append(result_data.get("result"))
        
        # 格式化输出
        if len(successful_results) == 1:
            result = successful_results[0]
            if isinstance(result, dict):
                # 如果是字典，尝试提取有意义的内容
                if "result" in result:
                    return str(result["result"])
                elif "content" in result:
                    return str(result["content"])
                else:
                    return str(result)
            return str(result)
        else:
            # 多个结果，组合输出
            return "\n\n".join([str(r) for r in successful_results])
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """
        获取执行状态
        
        Args:
            execution_id: 执行ID
            
        Returns:
            执行结果对象，如果不存在返回None
        """
        return self.execution_store.get(execution_id)












































"""
动态工作流引擎
基于JSON配置构建和执行LangGraph工作流
"""
from typing import Dict, Any, Optional, List, TypedDict, AsyncGenerator
import logging
import uuid
from datetime import datetime
import asyncio
import os
import re
import ast

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "__end__"

try:
    from langgraph.checkpoint.memory import MemorySaver
    CHECKPOINT_AVAILABLE = True
    MemorySaver = MemorySaver
except ImportError:
    CHECKPOINT_AVAILABLE = False
    MemorySaver = None

# PostgresSaver是可选的，需要额外依赖
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    PostgresSaver = PostgresSaver
except ImportError:
    PostgresSaver = None

from pydantic import BaseModel, Field, ConfigDict

# 导入共享库中的State定义
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared_libs.luminaos_common.schemas.workflow_states import (
    WorkflowStateTypedDict,
    WorkflowStateModel, 
    WorkflowState,
    validate_workflow_state,
    create_workflow_state,
    AgentWorkflowState
)

from ..models.workflow_models import WorkflowDefinition
from .config_parser import WorkflowConfigParser
from .node_registry import node_registry

logger = logging.getLogger(__name__)

# 在logger初始化后记录LangGraph状态
def _log_langgraph_status():
    if LANGGRAPH_AVAILABLE:
        logger.info("LangGraph imported successfully")
    else:
        logger.warning("LangGraph not available, will use simulation mode for workflow execution")

# 延迟记录，确保logger已初始化
_log_langgraph_status()


class DynamicWorkflowEngine:
    """动态工作流引擎"""
    
    def __init__(self):
        self._workflows: Dict[str, Any] = {}  # CompiledGraph或None
        self._workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, Dict[str, Any]] = {}
        self._config_parser = WorkflowConfigParser()
        self.checkpointer = self._create_checkpointer()
    
    def _create_checkpointer(self):
        """创建状态检查点管理器"""
        if not CHECKPOINT_AVAILABLE:
            return None
        
        # 优先使用PostgreSQL，回退到内存
        database_url = os.getenv("DATABASE_URL")
        if database_url and PostgresSaver:
            try:
                logger.info("Initializing PostgreSQL checkpointer")
                return PostgresSaver.from_conn_string(database_url)
            except Exception as e:
                logger.warning(f"Failed to initialize PostgreSQL checkpointer: {e}. Using memory saver.")
        
        if MemorySaver:
            logger.info("Using memory checkpointer")
            return MemorySaver()
        
        return None
    
    def build_from_config(self, workflow_config: Dict[str, Any]) -> str:
        """
        从JSON配置构建工作流
        
        Args:
            workflow_config: 工作流JSON配置
        
        Returns:
            工作流ID
        
        Raises:
            ValueError: 如果配置无效
        """
        # 解析配置
        workflow_def = self._config_parser.parse(workflow_config)
        
        # 生成工作流ID
        workflow_id = f"wf-{uuid.uuid4().hex[:12]}"
        
        # 构建LangGraph图
        graph = None
        if LANGGRAPH_AVAILABLE:
            try:
                graph = self._build_langgraph(workflow_def)
            except Exception as e:
                logger.warning(f"Failed to build LangGraph, will use simulation: {str(e)}")
                graph = None
        else:
            logger.warning("LangGraph not available, will use simulation")
        
        # 保存工作流
        self._workflows[workflow_id] = graph
        self._workflow_definitions[workflow_id] = workflow_def
        
        logger.info(f"Built workflow from config: {workflow_def.name} (id: {workflow_id})")
        
        return workflow_id
    
    def _build_langgraph(self, workflow_def: WorkflowDefinition) -> Optional[Any]:
        """
        构建LangGraph图
        
        Args:
            workflow_def: 工作流定义
        
        Returns:
            编译后的LangGraph图
        """
        if not LANGGRAPH_AVAILABLE or StateGraph is None:
            return None
        
        # 创建状态图（使用字典类型以兼容LangGraph）
        workflow = StateGraph(dict)  # LangGraph需要字典类型
        
        # 创建节点实例
        node_instances = {}
        for node in workflow_def.nodes:
            try:
                node_config = {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                    "config": node.config,
                    "description": node.description
                }
                node_instance = node_registry.create_node(node_config)
                node_instances[node.id] = node_instance
            except Exception as e:
                logger.error(f"Failed to create node {node.id}: {str(e)}")
                raise
        
        # 添加节点到图
        for node_id, node_instance in node_instances.items():
            workflow.add_node(node_id, self._create_node_wrapper(node_instance))
        
        # 设置入口节点
        workflow.set_entry_point(workflow_def.start_node_id)
        
        # 添加边（连接）
        for connection in workflow_def.connections:
            source_id = connection.source.node_id
            target_id = connection.target.node_id
            
            if connection.condition:
                # 条件边
                workflow.add_conditional_edges(
                    source_id,
                    self._create_condition_function(connection.condition),
                    {
                        "true": target_id,
                        "false": END if END != "__end__" else target_id
                    }
                )
            else:
                # 普通边
                workflow.add_edge(source_id, target_id)
        
        # 设置结束节点
        end_marker = END if END != "__end__" else "__end__"
        if workflow_def.end_node_ids:
            for end_node_id in workflow_def.end_node_ids:
                workflow.add_edge(end_node_id, end_marker)
        else:
            # 如果没有指定结束节点，所有没有出边的节点都连接到END
            for node in workflow_def.nodes:
                has_outgoing = any(
                    conn.source.node_id == node.id
                    for conn in workflow_def.connections
                )
                if not has_outgoing and node.id != workflow_def.start_node_id:
                    workflow.add_edge(node.id, end_marker)
        
        # 配置interrupts（在需要用户输入的节点前中断）
        interrupt_nodes = self._get_interrupt_nodes(workflow_def)
        
        # 编译图（带checkpointer和interrupts）
        try:
            compile_kwargs = {}
            
            # 添加checkpointer
            if self.checkpointer:
                compile_kwargs["checkpointer"] = self.checkpointer
            
            # 添加interrupts
            if interrupt_nodes.get('before'):
                compile_kwargs["interrupt_before"] = interrupt_nodes['before']
            if interrupt_nodes.get('after'):
                compile_kwargs["interrupt_after"] = interrupt_nodes['after']
            
            # 注意：configurable在compile时不需要，它在执行时通过config参数传递
            compiled_graph = workflow.compile(**compile_kwargs)
            return compiled_graph
        except Exception as e:
            logger.error(f"Failed to compile workflow graph: {str(e)}")
            if LANGGRAPH_AVAILABLE:
                raise
            return None
    
    def _get_interrupt_nodes(self, workflow_def: WorkflowDefinition) -> Dict[str, List[str]]:
        """获取需要中断的节点列表"""
        interrupt_before = []
        interrupt_after = []
        
        for node in workflow_def.nodes:
            node_type = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
            
            # 在用户输入节点前中断
            if node_type in ['user_input', 'human_review', 'agent']:
                interrupt_before.append(node.id)
            
            # 在决策节点后中断（等待审核）
            if node_type in ['decision', 'approval', 'condition']:
                interrupt_after.append(node.id)
        
        return {
            'before': interrupt_before,
            'after': interrupt_after
        }
    
    def _create_node_wrapper(self, node_instance):
        """创建节点包装器（适配LangGraph）"""
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                result = await node_instance.execute(state)
                # 合并结果到状态
                state.update(result)
                return state
            except Exception as e:
                logger.error(f"Node execution error: {str(e)}", exc_info=True)
                state["error"] = str(e)
                state["failed_node"] = node_instance.name
                return state
        
        return wrapper
    
    def _create_condition_function(self, condition: str):
        """创建条件函数（用于条件边）- 使用安全的AST评估"""
        def condition_func(state: Dict[str, Any]) -> str:
            try:
                # 使用condition_node中的安全评估方法
                from ..nodes.condition_node import ConditionNode
                
                if not condition:
                    return "true"
                
                # 验证表达式安全性
                if not self._validate_condition_expression(condition):
                    logger.error(f"Unsafe condition expression: {condition}")
                    return "false"
                
                # 创建临时条件节点进行评估
                condition_node = ConditionNode(
                    name="temp_condition",
                    config={"condition": condition}
                )
                result = condition_node._evaluate_expression(condition, state)
                return "true" if result else "false"
            except Exception as e:
                logger.error(f"Condition evaluation failed for '{condition}': {e}")
                logger.debug(f"State context: { {k: type(v).__name__ for k, v in state.items()} }")
                return "false"
        
        return condition_func
    
    def _validate_condition_expression(self, expression: str) -> bool:
        """验证条件表达式是否安全"""
        # 不允许的操作符和函数
        forbidden_patterns = [
            r'__.*__',  # 魔术方法
            r'import\s+',  # import语句
            r'exec\s*\(',  # exec函数
            r'eval\s*\(',  # eval函数
            r'open\s*\(',  # 文件操作
            r'os\.',  # os模块
            r'subprocess\.',  # 子进程
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return False
        
        # 检查表达式复杂度
        try:
            # 使用AST分析表达式复杂度
            tree = ast.parse(expression, mode='eval')
            # 限制AST节点数量
            node_count = len(list(ast.walk(tree)))
            if node_count > 100:  # 限制复杂度
                return False
        except SyntaxError:
            return False
        
        return True
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行工作流（支持恢复）
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            timeout: 超时时间（秒）
            thread_id: 线程ID（用于恢复执行）
        
        Returns:
            执行结果
        
        Raises:
            ValueError: 如果工作流不存在
            TimeoutError: 如果执行超时
        """
        import time
        
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow with id '{workflow_id}' not found")
        
        workflow_def = self._workflow_definitions[workflow_id]
        graph = self._workflows[workflow_id]
        execution_id = str(uuid.uuid4())
        if not thread_id:
            thread_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(
            f"Executing workflow: {workflow_def.name} "
            f"(id: {workflow_id}, execution_id: {execution_id}, thread_id: {thread_id})"
        )
        
        try:
            # 初始化状态（使用WorkflowStateModel进行验证）
            state_model = WorkflowStateModel(
                input_data=input_data,
                node_results={},
                execution_history=[],
                metadata={
                    "workflow_id": workflow_id,
                    "start_time": datetime.utcnow().isoformat(),
                    "thread_id": thread_id
                },
                execution_id=execution_id,
                workflow_id=workflow_id,
                start_time=start_time
            )
            # 使用 Pydantic v2 的 model_dump() 方法
            # WorkflowState是TypedDict，不能直接实例化，应该使用字典
            state_dict = state_model.model_dump() if hasattr(state_model, 'model_dump') else state_model.dict()
            initial_state: WorkflowState = state_dict  # 类型注解，实际是字典
            
            # 执行工作流
            if graph is not None and LANGGRAPH_AVAILABLE:
                # 使用LangGraph执行（带checkpointer）
                try:
                    config = {"configurable": {"thread_id": thread_id}}
                    
                    if timeout:
                        result_state = await asyncio.wait_for(
                            graph.ainvoke(initial_state, config=config),
                            timeout=timeout
                        )
                    else:
                        result_state = await graph.ainvoke(initial_state, config=config)
                except Exception as e:
                    logger.warning(f"LangGraph execution failed, falling back to simulation: {str(e)}")
                    result_state = await self._simulate_execution(workflow_def, initial_state, timeout)
            else:
                # 模拟执行（当LangGraph不可用时）
                result_state = await self._simulate_execution(workflow_def, initial_state, timeout)
            
            execution_time = time.time() - start_time
            
            # 提取结果
            result = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_def.name,
                "thread_id": thread_id,
                "success": "error" not in result_state,
                "result": {k: v for k, v in result_state.items() if not k.startswith("_")},
                "execution_time": execution_time,
                "executed_at": datetime.now().isoformat()
            }
            
            if "error" in result_state:
                result["error"] = result_state["error"]
            
            # 保存执行记录
            self._executions[execution_id] = result
            
            logger.info(
                f"Workflow execution completed: {execution_id} "
                f"(time: {execution_time:.3f}s)"
            )
            
            return result
        
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Workflow execution timeout after {timeout}s"
            logger.error(f"Workflow execution timeout: {workflow_id}")
            
            result = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_def.name,
                "thread_id": thread_id,
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "executed_at": datetime.now().isoformat()
            }
            
            self._executions[execution_id] = result
            raise TimeoutError(error_msg)
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(f"Workflow execution error: {error_msg}", exc_info=True)
            
            result = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_def.name,
                "thread_id": thread_id,
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "executed_at": datetime.now().isoformat()
            }
            
            self._executions[execution_id] = result
            raise
    
    async def _simulate_execution(
        self,
        workflow_def: WorkflowDefinition,
        initial_state: Dict[str, Any],
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """模拟执行工作流（当LangGraph不可用时）"""
        logger.info(f"Starting simulation execution for workflow: {workflow_def.name}")
        logger.info(f"Start node ID: {workflow_def.start_node_id}")
        logger.info(f"Total nodes: {len(workflow_def.nodes)}, Total connections: {len(workflow_def.connections)}")
        
        state = initial_state.copy()
        current_node_id = workflow_def.start_node_id
        
        # 构建连接图
        from collections import defaultdict
        graph = defaultdict(list)
        for conn in workflow_def.connections:
            source_id = conn.source.node_id
            target_id = conn.target.node_id
            graph[source_id].append(target_id)
            logger.debug(f"Connection: {source_id} -> {target_id}")
        
        logger.info(f"Built connection graph with {len(graph)} source nodes")
        
        # 简单顺序执行
        visited = set()
        execution_count = 0
        while current_node_id and current_node_id not in visited:
            visited.add(current_node_id)
            execution_count += 1
            logger.info(f"[Simulation Step {execution_count}] Processing node ID: {current_node_id}")
            
            # 找到当前节点
            current_node = next(
                (n for n in workflow_def.nodes if n.id == current_node_id),
                None
            )
            
            if not current_node:
                logger.warning(f"Node with ID '{current_node_id}' not found in workflow definition")
                break
            
            logger.info(f"[Simulation Step {execution_count}] Found node: {current_node.name} (type: {current_node.node_type}, id: {current_node.id})")
            
            # 执行节点
            try:
                logger.info(f"[Simulation Step {execution_count}] Creating node instance for: {current_node.name}")
                node_config = {
                    "id": current_node.id,
                    "name": current_node.name,
                    "type": current_node.node_type.value if hasattr(current_node.node_type, 'value') else str(current_node.node_type),
                    "config": current_node.config or {}
                }
                logger.info(f"[Simulation Step {execution_count}] Node config: {node_config}")
                node_instance = node_registry.create_node(node_config)
                logger.info(f"[Simulation Step {execution_count}] Node instance created, executing with state keys: {list(state.keys())}")
                result = await node_instance.execute(state)
                logger.info(f"[Simulation Step {execution_count}] Node '{current_node.name}' executed successfully, result keys: {list(result.keys())}")
                state.update(result)
                logger.info(f"[Simulation Step {execution_count}] State updated, new state keys: {list(state.keys())}")
            except Exception as e:
                logger.error(f"[Simulation Step {execution_count}] Node execution error for '{current_node.name}': {str(e)}", exc_info=True)
                state["error"] = str(e)
                state["error_node"] = current_node.name
                state["error_node_id"] = current_node_id
                break
            
            # 移动到下一个节点
            next_nodes = graph.get(current_node_id, [])
            logger.info(f"[Simulation Step {execution_count}] Next nodes from '{current_node_id}': {next_nodes}")
            if next_nodes:
                current_node_id = next_nodes[0]
                logger.info(f"[Simulation Step {execution_count}] Moving to next node: {current_node_id}")
            else:
                logger.info(f"[Simulation Step {execution_count}] No more nodes to execute, ending simulation")
                break
        
        logger.info(f"Simulation execution completed. Executed {execution_count} nodes. Final state keys: {list(state.keys())}")
        return state
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self._workflow_definitions.get(workflow_id)
    
    def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行结果"""
        return self._executions.get(execution_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        return [
            {
                "id": workflow_id,
                "name": workflow_def.name,
                "description": workflow_def.description,
                "version": workflow_def.version,
                "node_count": len(workflow_def.nodes),
                "connection_count": len(workflow_def.connections)
            }
            for workflow_id, workflow_def in self._workflow_definitions.items()
        ]
    
    async def execute_workflow_stream(
        self, 
        workflow_id: str, 
        input_data: Dict, 
        thread_id: Optional[str] = None
    ) -> AsyncGenerator[Dict, None]:
        """流式执行工作流"""
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        try:
            # 获取编译的工作流图
            if workflow_id not in self._workflows:
                raise ValueError(f"Workflow with id '{workflow_id}' not found")
            
            graph = self._workflows[workflow_id]
            workflow_def = self._workflow_definitions[workflow_id]
            
            if not graph or not LANGGRAPH_AVAILABLE:
                raise ValueError("LangGraph not available for streaming")
            
            # 使用共享库创建标准状态
            state_model = create_workflow_state(
                workflow_id=workflow_id,
                input_data=input_data,
                thread_id=thread_id
            )
            # 转换为LangGraph兼容的字典
            initial_state = state_model.model_dump()
            
            # 流式执行
            config = {"configurable": {"thread_id": thread_id}}
            
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v1"
            ):
                yield self._format_stream_event(event, thread_id)
                
        except Exception as e:
            logger.error(f"Stream execution failed for workflow {workflow_id}: {e}")
            yield {
                "type": "error",
                "thread_id": thread_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_stream_event(self, event: Dict, thread_id: str) -> Dict:
        """格式化流式事件"""
        event_type = event.get("event")
        node_id = event.get("name")
        
        base_event = {
            "thread_id": thread_id,
            "event_type": event_type,
            "node_id": node_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if event_type == "on_chain_start":
            return {
                **base_event,
                "message": f"Starting node: {node_id}",
                "data": {"input": event.get("data", {}).get("input")}
            }
        elif event_type == "on_chain_end":
            return {
                **base_event,
                "message": f"Completed node: {node_id}",
                "data": {"output": event.get("data", {}).get("output")}
            }
        elif event_type == "on_tool_start":
            return {
                **base_event,
                "message": f"Executing tool: {node_id}",
                "data": {"tool_input": event.get("data", {}).get("input")}
            }
        elif event_type == "on_tool_end":
            return {
                **base_event,
                "message": f"Tool completed: {node_id}",
                "data": {"tool_output": event.get("data", {}).get("output")}
            }
        elif event_type == "on_llm_stream":
            # LLM流式输出
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, 'content'):
                return {
                    **base_event,
                    "type": "llm_chunk",
                    "data": {"content": chunk.content}
                }
        
        return base_event
    
    async def resume_workflow(
        self, 
        workflow_id: str, 
        thread_id: str, 
        user_input: Optional[Dict] = None
    ) -> Dict:
        """恢复中断的工作流"""
        try:
            if workflow_id not in self._workflows:
                raise ValueError(f"Workflow with id '{workflow_id}' not found")
            
            graph = self._workflows[workflow_id]
            workflow_def = self._workflow_definitions[workflow_id]
            
            if not graph or not LANGGRAPH_AVAILABLE or not self.checkpointer:
                raise ValueError("Workflow resumption requires LangGraph and checkpointer")
            
            # 获取当前状态
            config = {"configurable": {"thread_id": thread_id}}
            try:
                # 尝试从checkpointer获取状态
                from langgraph.checkpoint.base import Checkpoint
                checkpoint = await self.checkpointer.aget(config)
                if not checkpoint:
                    raise ValueError(f"No checkpoint found with thread_id: {thread_id}")
                
                current_state = checkpoint.get("channel_values", {})
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
                raise ValueError(f"No workflow found with thread_id: {thread_id}")
            
            # 如果有用户输入，更新状态
            if user_input:
                current_state.update(user_input)
            
            # 继续执行
            final_state = await graph.ainvoke(current_state, config=config)
            
            return self._format_execution_result(final_state, thread_id, workflow_def)
            
        except Exception as e:
            logger.error(f"Failed to resume workflow {workflow_id}: {e}")
            raise
    
    def _format_execution_result(
        self, 
        state: Dict, 
        thread_id: str, 
        workflow_def: WorkflowDefinition
    ) -> Dict:
        """格式化执行结果"""
        return {
            "thread_id": thread_id,
            "workflow_id": workflow_def.name if hasattr(workflow_def, 'name') else None,
            "success": "error" not in state,
            "result": {k: v for k, v in state.items() if not k.startswith("_")},
            "executed_at": datetime.now().isoformat()
        }
    
    def get_compiled_workflow(self, workflow_id: str) -> Optional[Any]:
        """获取编译的工作流图"""
        return self._workflows.get(workflow_id)
    
    def _validate_initial_state(self, state: Dict[str, Any]) -> bool:
        """验证初始状态"""
        return validate_workflow_state(state)
    
    def _create_agent_workflow_state(
        self, 
        workflow_id: str, 
        agent_id: str, 
        input_data: Dict[str, Any]
    ) -> AgentWorkflowState:
        """创建智能体工作流状态"""
        return AgentWorkflowState.create_agent_state(
            workflow_id=workflow_id,
            agent_id=agent_id,
            input_data=input_data
        )


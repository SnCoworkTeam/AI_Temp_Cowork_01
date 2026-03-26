"""
动态执行引擎
执行LLM设计的智能体网络，支持流式输出

增强版：支持状态持久化、智能体协作、性能分析
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from collections import defaultdict, deque
from datetime import datetime
import uuid

from .dynamic_workflow_designer import DynamicWorkflowDesigner
try:
    from .learning_workflow_designer import LearningWorkflowDesigner
except ImportError:
    LearningWorkflowDesigner = None
try:
    from .agents.agent_registry import AgentRegistry, AgentDiscoveryService
except ImportError:
    # 如果agent_registry不存在，创建占位类
    class AgentRegistry:
        def __init__(self): pass
        async def register_agent(self, *args, **kwargs): pass
        async def get_agent(self, *args, **kwargs): return None
        async def list_agents(self): return []
        async def get_agent_capabilities(self, *args, **kwargs): return None
        async def get_all_capabilities(self): return {}
        async def get_agent_metadata(self, *args, **kwargs): return None
    class AgentDiscoveryService:
        def __init__(self, *args, **kwargs): pass
        async def discover_agents(self, *args, **kwargs): return []

try:
    from .state_manager import StateManager, InMemoryStateStore, ExecutionState
except ImportError:
    # 如果state_manager不存在，创建占位类
    class StateManager:
        def __init__(self, *args, **kwargs): pass
        async def save_execution_state(self, *args, **kwargs): pass
        async def create_checkpoint(self, *args, **kwargs): pass
        async def resume_execution(self, *args, **kwargs): return None
        async def mark_execution_complete(self, *args, **kwargs): pass
        async def mark_execution_failed(self, *args, **kwargs): pass
    class InMemoryStateStore:
        pass
    class ExecutionState:
        def __init__(self, **kwargs): pass

try:
    from .performance_analyzer import PerformanceAnalyzer
except ImportError:
    # 如果performance_analyzer不存在，创建占位类
    class PerformanceAnalyzer:
        def __init__(self, *args, **kwargs): pass
        def get_performance_summary(self): return {}

# OS Core集成 - 行为数据收集器
BEHAVIOR_COLLECTOR_AVAILABLE = False
BehaviorCollector = None

# 先定义logger，因为后面会用到
logger = logging.getLogger(__name__)

try:
    import sys
    from pathlib import Path
    # 添加os-core目录到路径
    project_root = Path(__file__).parent.parent.parent.parent
    os_core_path = project_root / "os-core"
    if str(os_core_path) not in sys.path:
        sys.path.insert(0, str(os_core_path))
    
    from behavior_collector import BehaviorCollector
    BEHAVIOR_COLLECTOR_AVAILABLE = True
    logger.info("行为数据收集器模块加载成功")
except ImportError as e:
    BEHAVIOR_COLLECTOR_AVAILABLE = False
    logger.warning(f"行为数据收集器模块未找到，行为数据收集功能将不可用: {e}")
from .agents import (
    MCPToolAgent, WorkflowAgent, MetadataAgent, KnowledgeBaseAgent,
    DataQueryAgent, DataCleanAgent, DataValidationAgent, DataEnrichAgent,
    AnalysisAgent, InsightAgent, QualityCheckAgent,
    ContentAgent, FormatAgent, ResultSynthesisAgent, SAPODataAgent
)
from .agents.standardized_agent import StandardizedAgent
from .llm_integration import deepseek_llm

# logger已在上面定义


class DynamicExecutionEngine:
    """动态执行引擎 - 执行LLM设计的网络，支持流式输出"""
    
    def __init__(
        self,
        enable_learning: bool = True,
        enable_state_persistence: bool = True,
        state_store = None
    ):
        """
        初始化动态执行引擎
        
        Args:
            enable_learning: 是否启用学习功能
            enable_state_persistence: 是否启用状态持久化
            state_store: 状态存储（可选，默认使用内存存储）
        """
        # 使用学习型设计器（如果启用且可用）
        if enable_learning and LearningWorkflowDesigner:
            self.performance_analyzer = PerformanceAnalyzer()
            self.workflow_designer = LearningWorkflowDesigner(self.performance_analyzer)
        else:
            self.workflow_designer = DynamicWorkflowDesigner()
            self.performance_analyzer = PerformanceAnalyzer() if enable_learning else None
        
        # 初始化智能体注册表
        self.agent_registry = AgentRegistry()
        self.agent_discovery = AgentDiscoveryService(self.agent_registry)
        
        # 初始化状态管理器
        if enable_state_persistence:
            self.state_manager = StateManager(state_store or InMemoryStateStore())
        else:
            self.state_manager = None
        
        # 初始化智能体池（向后兼容）
        self.agent_pool = self._initialize_agent_pool()
        
        # 注册所有智能体到注册表（异步，延迟执行）
        # 注意：在FastAPI启动时调用await engine._register_agents_to_registry()
        self._agents_registered = False
        
        # 初始化行为数据收集器
        self.behavior_collector = None
        if BEHAVIOR_COLLECTOR_AVAILABLE and BehaviorCollector:
            try:
                self.behavior_collector = BehaviorCollector()
                logger.info("行为数据收集器初始化成功")
            except Exception as e:
                logger.warning(f"行为数据收集器初始化失败: {e}，行为数据收集功能将不可用")
                self.behavior_collector = None
        
        self.llm = deepseek_llm
    
    async def initialize(self):
        """初始化执行引擎（异步注册智能体）"""
        if not self._agents_registered:
            await self._register_agents_to_registry()
            self._agents_registered = True
    
    def _initialize_agent_pool(self) -> Dict[str, Any]:
        """初始化智能体池（向后兼容）"""
        mcp_tool_agent = MCPToolAgent()
        sap_odata_agent = SAPODataAgent()
        
        return {
            # 核心智能体
            "metadata_agent": MetadataAgent(),
            "mcp_tool_agent": mcp_tool_agent,
            "sap_odata_agent": sap_odata_agent,
            "workflow_agent": WorkflowAgent(),
            "knowledge_base_agent": KnowledgeBaseAgent(),
            # 数据智能体分支
            "data_query_agent": DataQueryAgent(mcp_tool_agent=mcp_tool_agent, sap_odata_agent=sap_odata_agent),
            "data_clean_agent": DataCleanAgent(),
            "data_validation_agent": DataValidationAgent(),
            "data_enrich_agent": DataEnrichAgent(),
            # 分析智能体分支
            "analysis_agent": AnalysisAgent(),
            "insight_agent": InsightAgent(),
            "quality_check_agent": QualityCheckAgent(),
            # 内容智能体分支
            "content_agent": ContentAgent(),
            "format_agent": FormatAgent(),
            # 结果合成
            "result_synthesis_agent": ResultSynthesisAgent(),
        }
    
    async def _register_agents_to_registry(self):
        """将所有智能体注册到注册表，并同步元数据到metadata-service"""
        from .agents.agent_adapter import AgentAdapter
        from .agents.standardized_agent import StandardizedAgent
        
        # 尝试导入metadata_client（可选，如果不可用则跳过元数据同步）
        try:
            from ..services.metadata_client import metadata_client
            sync_metadata = True
        except ImportError:
            logger.warning("metadata_client not available, skipping metadata sync")
            sync_metadata = False
            metadata_client = None
        
        for agent_id, agent in self.agent_pool.items():
            try:
                # 获取智能体基本信息
                agent_name = getattr(agent, 'name', agent_id)
                agent_description = getattr(agent, 'description', f"{agent_name}智能体")
                capabilities = getattr(agent, 'capabilities', {})
                
                # 转换capabilities为列表
                if isinstance(capabilities, dict):
                    capabilities_list = list(capabilities.keys()) + list(capabilities.values())
                elif isinstance(capabilities, list):
                    capabilities_list = capabilities
                else:
                    capabilities_list = [str(capabilities)]
                
                # 如果智能体已经是StandardizedAgent，直接注册
                if isinstance(agent, StandardizedAgent):
                    metadata = {
                        "source": "builtin",
                        "registered_at": datetime.utcnow().isoformat()
                    }
                    await self.agent_registry.register_agent(agent, metadata)
                    logger.info(f"Registered standardized agent: {agent_id}")
                else:
                    # 旧版智能体，使用适配器包装
                    adapter = AgentAdapter(agent)
                    metadata = {
                        "source": "builtin",
                        "legacy_agent": True,
                        "registered_at": datetime.utcnow().isoformat()
                    }
                    await self.agent_registry.register_agent(adapter, metadata)
                    # 同时更新agent_pool中的引用
                    self.agent_pool[agent_id] = adapter
                    logger.info(f"Registered legacy agent (via adapter): {agent_id}")
                
                # 同步元数据到metadata-service
                if sync_metadata and metadata_client:
                    try:
                        # 尝试获取智能体的增强元数据（如果支持）
                        if hasattr(agent, 'get_metadata_for_registration'):
                            agent_metadata = agent.get_metadata_for_registration()
                        else:
                            agent_metadata = {
                                "agent_id": agent_id,
                                "agent_name": agent_name,
                                "source": "dynamic_workflow_engine",
                                "builtin": True
                            }
                        
                        config = getattr(agent, 'config', {})
                        
                        # 注册为AI模型
                        await metadata_client.register_agent_as_ai_model(
                            agent_id=agent_id,
                            agent_name=agent_name,
                            agent_description=agent_description,
                            capabilities=capabilities_list,
                            config=config,
                            metadata=agent_metadata,
                            status="active"
                        )
                        
                        # 注册为业务实体
                        await metadata_client.register_agent_as_business_entity(
                            agent_id=agent_id,
                            agent_name=agent_name,
                            agent_description=agent_description,
                            capabilities=capabilities_list,
                            config=config,
                            metadata=agent_metadata,
                            status="active"
                        )
                        
                        logger.info(f"Synced agent metadata to metadata-service: {agent_id}")
                    except Exception as e:
                        logger.warning(f"Failed to sync agent {agent_id} metadata to metadata-service: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to register agent {agent_id}: {e}", exc_info=True)
    
    async def execute_dynamic_workflow(
        self,
        user_input: str,
        context: Dict[str, Any],
        stream: bool = True,
        execution_id: Optional[str] = None,
        resume: bool = False
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        执行动态工作流（支持流式输出、状态持久化、恢复）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            stream: 是否流式输出
            execution_id: 执行ID（可选，用于恢复）
            resume: 是否恢复执行
            
        Yields:
            执行过程的流式输出
        """
        # 生成或使用执行ID
        if not execution_id:
            execution_id = str(uuid.uuid4())
        
        execution_context = context.copy()
        execution_context["user_input"] = user_input
        execution_context["execution_id"] = execution_id
        
        # 如果启用状态持久化且需要恢复
        if resume and self.state_manager:
            saved_state = await self.state_manager.resume_execution(execution_id)
            if saved_state:
                yield {
                    "type": "execution",
                    "stage": "resuming",
                    "message": f"恢复执行 {execution_id}",
                    "execution_id": execution_id,
                    "progress": 0
                }
                # 从保存的状态恢复
                execution_context = saved_state.context
                network_design = saved_state.network_design
                agent_results = saved_state.agent_results
                start_layer = saved_state.current_layer
                
                # 继续执行
                async for chunk in self._execute_network_with_streaming(
                    network_design,
                    execution_context,
                    agent_results=agent_results,
                    start_layer=start_layer,
                    execution_id=execution_id
                ):
                    yield chunk
                return
        
        # 阶段1：设计智能体网络（流式输出思考过程）
        design_result = None
        async for design_chunk in self.workflow_designer.design_for_request(
            user_input, context, stream=True
        ):
            yield design_chunk
            # 保存最终设计结果
            if design_chunk.get("type") == "design_complete":
                design_result = design_chunk.get("design")
        
        if not design_result:
            yield {
                "type": "error",
                "stage": "design",
                "message": "无法设计智能体网络：设计结果为空",
                "error": "Design result is empty"
            }
            return
        
        # 保存初始状态
        if self.state_manager:
            await self.state_manager.save_execution_state(ExecutionState(
                execution_id=execution_id,
                user_input=user_input,
                context=execution_context,
                network_design=design_result,
                current_layer=0,
                agent_results={},
                status="running"
            ))
        
        # 阶段2：执行智能体网络（流式输出执行过程）
        start_time = datetime.utcnow()
        execution_success = True
        final_agent_results = {}
        
        try:
            async for execution_chunk in self._execute_network_with_streaming(
                design_result,
                execution_context,
                execution_id=execution_id
            ):
                yield execution_chunk
                
                # 更新执行状态和收集结果
                if execution_chunk.get("type") == "execution":
                    # 收集agent_results（从context中）
                    if execution_chunk.get("stage") == "agent_complete":
                        agent_id = execution_chunk.get("agent_id")
                        if agent_id and "_agent_results" in execution_context:
                            final_agent_results = execution_context.get("_agent_results", {})
                    
                    # 创建检查点
                    if execution_chunk.get("stage") == "layer_complete" and self.state_manager:
                        layer_num = execution_chunk.get("layer_number", 0)
                        await self.state_manager.create_checkpoint(
                            execution_id=execution_id,
                            user_input=user_input,
                            context=execution_context,
                            network_design=design_result,
                            current_layer=layer_num,
                            agent_results=execution_context.get("_agent_results", {})
                        )
                    
                    # 收集最终结果
                    if execution_chunk.get("stage") == "execution_complete":
                        final_result = execution_chunk.get("final_result", {})
                        execution_success = final_result.get("success", True)
                        final_agent_results = execution_context.get("_agent_results", {})
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            execution_success = False
            if self.state_manager:
                await self.state_manager.mark_execution_failed(execution_id, str(e))
            raise
        finally:
            # 记录执行历史（用于学习）
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # 启用LearningWorkflowDesigner的记录功能
            if self.performance_analyzer and LearningWorkflowDesigner and isinstance(self.workflow_designer, LearningWorkflowDesigner):
                try:
                    self.workflow_designer.record_execution(
                        execution_id=execution_id,
                        user_input=user_input,
                        network_design=design_result,
                        agent_results=final_agent_results,
                        execution_time=execution_time,
                        success=execution_success
                    )
                    logger.debug(f"已记录执行历史到LearningWorkflowDesigner: {execution_id}")
                except Exception as e:
                    logger.warning(f"记录执行历史失败: {e}")
            
            # 行为数据收集：收集工作流执行数据
            if self.behavior_collector:
                try:
                    # 构建执行步骤
                    steps = []
                    if design_result and "agents" in design_result:
                        for agent_spec in design_result.get("agents", []):
                            agent_id = agent_spec.get("id", "")
                            agent_result = final_agent_results.get(agent_id, {})
                            
                            # 提取执行元数据
                            execution_time = 0.0
                            success = True
                            if isinstance(agent_result, dict):
                                success = agent_result.get("execution_success", agent_result.get("success", True))
                                exec_metadata = agent_result.get("execution_metadata", {})
                                if isinstance(exec_metadata, dict):
                                    execution_time = exec_metadata.get("execution_time", 0.0)
                                elif hasattr(exec_metadata, "execution_time"):
                                    execution_time = exec_metadata.execution_time
                            
                            steps.append({
                                "agent_id": agent_id,
                                "agent_type": agent_spec.get("agent_type", ""),
                                "task": agent_spec.get("task", ""),
                                "success": success,
                                "execution_time": execution_time
                            })
                    
                    # 提取资源使用情况（从agent_results中）
                    resource_usage = []
                    for agent_id, result in final_agent_results.items():
                        if isinstance(result, dict):
                            # 从enhancements中提取资源信息
                            enhancements = result.get("enhancements_provided", {})
                            if "data_sources" in enhancements:
                                for source in enhancements["data_sources"]:
                                    if isinstance(source, dict):
                                        source_id = source.get("id") or source.get("name", "")
                                        if source_id:
                                            resource_usage.append(source_id)
                    
                    self.behavior_collector.collect_workflow_execution(
                        workflow_id=f"dynamic_workflow_{execution_id}",
                        workflow_name="动态工作流",
                        execution_id=execution_id,
                        steps=steps,
                        total_time=execution_time,
                        success=execution_success,
                        failure_point=None if execution_success else "agent_execution",
                        agent_usage=list(final_agent_results.keys()) if final_agent_results else [],
                        resource_usage=list(set(resource_usage)) if resource_usage else [],  # 去重
                        user_id=context.get("user_id"),
                        metadata={
                            "user_input": user_input,
                            "network_design": design_result,
                            "agent_count": len(final_agent_results) if final_agent_results else 0
                        }
                    )
                    logger.debug(f"已收集工作流执行数据: {execution_id}")
                except Exception as e:
                    logger.warning(f"收集工作流执行数据失败: {e}", exc_info=True)
            
            # 标记执行完成
            if self.state_manager:
                await self.state_manager.mark_execution_complete(
                    execution_id,
                    {"success": execution_success}
                )
    
    async def _execute_network_with_streaming(
        self,
        network_design: Dict[str, Any],
        context: Dict[str, Any],
        execution_id: Optional[str] = None,
        agent_results: Optional[Dict[str, Any]] = None,
        start_layer: int = 0
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行智能体网络"""
        
        agents = network_design.get("agents", [])
        execution_layers = network_design.get("execution_layers", [])
        
        if not agents or not execution_layers:
            yield {
                "type": "error",
                "stage": "execution",
                "message": "无效的网络设计：缺少智能体或执行层",
                "error": "Invalid network design: missing agents or execution layers"
            }
            return
        
        # 初始化执行结果（如果提供了则使用，否则创建新的）
        if agent_results is None:
            agent_results = {}
        
        total_layers = len(execution_layers)
        
        # 从指定层开始执行
        layers_to_execute = execution_layers[start_layer:] if start_layer > 0 else execution_layers
        
        yield {
            "type": "execution",
            "stage": "execution_start",
            "message": f"开始执行智能体网络：{len(agents)}个智能体，{total_layers}个执行层",
            "total_agents": len(agents),
            "total_layers": total_layers,
            "progress": 0
        }
        
        # 按层执行
        for relative_idx, layer_agent_ids in enumerate(layers_to_execute):
            layer_idx = start_layer + relative_idx
            layer_num = layer_idx + 1
            
            yield {
                "type": "execution",
                "stage": "layer_start",
                "message": f"执行第 {layer_num}/{total_layers} 层：{len(layer_agent_ids)}个智能体",
                "layer_number": layer_num,
                "total_layers": total_layers,
                "agents_in_layer": layer_agent_ids,
                "progress": int((layer_idx / total_layers) * 100)
            }
            
            # 并行执行这一层的智能体
            layer_tasks = {}
            for agent_id in layer_agent_ids:
                agent_spec = next((a for a in agents if a.get("id") == agent_id), None)
                if not agent_spec:
                    logger.warning(f"Agent spec not found for {agent_id}")
                    continue
                
                agent_type = agent_spec.get("agent_type")
                
                # 优先从注册表获取（支持动态发现）
                agent = await self.agent_registry.get_agent(agent_type)
                if not agent:
                    # 降级到agent_pool（向后兼容）
                    agent = self.agent_pool.get(agent_type)
                
                if not agent:
                    logger.warning(f"Agent {agent_type} not found in pool or registry")
                    yield {
                        "type": "execution",
                        "stage": "agent_error",
                        "message": f"智能体 {agent_type} 未找到",
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "error": f"Agent {agent_type} not found"
                    }
                    continue
                
                # 准备输入数据
                input_data = self._prepare_agent_input(agent_spec, agent_results, context)
                
                # 将依赖结果也添加到context中，方便智能体访问
                dependencies = agent_spec.get("dependencies", [])
                for dep_id in dependencies:
                    dep_result = agent_results.get(dep_id, {})
                    if dep_result:
                        dep_output_key = f"{dep_id}_result"
                        # 如果input_data中已经有这个key，也添加到context
                        if dep_output_key in input_data:
                            context[dep_output_key] = input_data[dep_output_key]
                
                # 创建执行任务
                # 如果智能体是StandardizedAgent，使用标准化接口
                from .agents.standardized_agent import StandardizedAgent
                if isinstance(agent, StandardizedAgent):
                    from .agents.protocols import StandardTask, TaskPriority
                    standard_task = StandardTask(
                        task_id=f"{execution_id}_{agent_id}",
                        task_type=agent_spec.get("agent_type", "unknown"),
                        description=agent_spec.get("task", ""),
                        input_data=input_data,
                        context=context,
                        priority=TaskPriority.MEDIUM
                    )
                    layer_tasks[agent_id] = agent.execute_with_tracking(standard_task)
                else:
                    # 旧版智能体，使用旧接口
                    layer_tasks[agent_id] = agent.execute_with_tracking(input_data, context)
                
                yield {
                    "type": "execution",
                    "stage": "agent_start",
                    "message": f"开始执行智能体：{agent_spec.get('task', agent_id)}",
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "agent_task": agent_spec.get("task", ""),
                    "progress": int((layer_idx / total_layers) * 100) + 5
                }
            
            # 等待这一层完成
            if layer_tasks:
                layer_results = await asyncio.gather(
                    *layer_tasks.values(),
                    return_exceptions=True
                )
                
                # 收集结果
                for agent_id, result in zip(layer_tasks.keys(), layer_results):
                    if isinstance(result, Exception):
                        logger.error(f"Agent {agent_id} execution failed: {result}", exc_info=True)
                        # 确保错误消息不为空
                        error_msg = str(result) if result and str(result) else f"智能体 {agent_id} 执行时发生未知错误"
                        error_type = type(result).__name__ if result else "UnknownError"
                        
                        agent_results[agent_id] = {
                            "success": False,
                            "error": error_msg,
                            "error_type": error_type
                        }
                        
                        # 构建详细的错误信息
                        error_details = {
                            "error_type": error_type,
                            "error_message": error_msg,
                            "agent_id": agent_id,
                            "agent_type": agent_spec.get("agent_type", "unknown"),
                            "suggestion": self._generate_error_suggestion(error_type, agent_id, agent_spec)
                        }
                        
                        yield {
                            "type": "execution",
                            "stage": "agent_error",
                            "message": f"智能体 {agent_id} 执行失败：{error_msg}",
                            "agent_id": agent_id,
                            "error": error_msg,
                            "error_type": error_type,
                            "error_details": error_details,
                            "progress": int((layer_idx / total_layers) * 100) + 10
                        }
                        
                        # 动态调整：如果关键智能体失败，可能需要调整后续计划
                        if await self._is_critical_agent(agent_id, network_design):
                            yield {
                                "type": "execution",
                                "stage": "recovery_needed",
                                "message": f"关键智能体 {agent_id} 失败，需要调整执行计划",
                                "agent_id": agent_id
                            }
                    else:
                        agent_results[agent_id] = result
                        
                        # 从execute_with_tracking返回的结果中提取实际结果
                        # 支持StandardResult和旧版格式
                        from .agents.protocols import StandardResult
                        if isinstance(result, StandardResult):
                            actual_result = result.output
                            # 提取artifacts
                            if result.artifacts:
                                context[f"{agent_id}_artifacts"] = [a.to_dict() for a in result.artifacts]
                        else:
                            actual_result = result.get("result", result)
                        
                        output_key = next(
                            (a.get("output_key") for a in agents if a.get("id") == agent_id),
                            f"{agent_id}_result"
                        )
                        # 确保存储到context的值可以序列化（不存储StandardResult对象）
                        from .agents.protocols import StandardResult
                        if isinstance(actual_result, StandardResult):
                            # 如果actual_result是StandardResult，存储其output
                            context[output_key] = actual_result.output
                        else:
                            context[output_key] = actual_result
                        
                        # 保存agent_results到context（用于检查点，但需要清理StandardResult）
                        # 注意：这里保存的是原始结果，但智能体访问时应该通过output_key获取
                        # 为了避免序列化问题，不直接保存StandardResult到context
                        cleaned_agent_results = {}
                        for aid, res in agent_results.items():
                            if isinstance(res, StandardResult):
                                cleaned_agent_results[aid] = res.to_dict()
                            else:
                                cleaned_agent_results[aid] = res
                        context["_agent_results"] = cleaned_agent_results
                        
                        # 提取执行元数据（支持StandardResult和旧版格式）
                        from .agents.protocols import StandardResult
                        if isinstance(result, StandardResult):
                            execution_metadata = result.execution_metadata
                            success = result.success
                            execution_time = execution_metadata.execution_time if execution_metadata else 0.0
                        else:
                            execution_metadata = result.get("execution_metadata", {})
                            # 优先使用 execution_success，如果不存在则使用 success，如果都不存在则默认为 True
                            if "execution_success" in result:
                                success = result["execution_success"]
                            elif "success" in result:
                                success = result["success"]
                            else:
                                success = True
                            execution_time = execution_metadata.get("execution_time", 0) if isinstance(execution_metadata, dict) else 0.0
                        
                        yield {
                            "type": "execution",
                            "stage": "agent_complete",
                            "message": f"智能体 {agent_id} 执行完成",
                            "agent_id": agent_id,
                            "agent_result": {
                                "success": success,
                                "execution_time": execution_time,
                                "confidence": result.confidence if isinstance(result, StandardResult) else 1.0,
                                "quality_score": result.quality_score if isinstance(result, StandardResult) else None
                            },
                            "progress": int(((layer_idx + 1) / total_layers) * 100)
                        }
            
            yield {
                "type": "execution",
                "stage": "layer_complete",
                "message": f"第 {layer_num}/{total_layers} 层执行完成",
                "layer_number": layer_num,
                "total_layers": total_layers,
                "progress": int(((layer_idx + 1) / total_layers) * 100)
            }
        
        # 阶段3：结果合成（使用结果合成智能体）
        yield {
            "type": "execution",
            "stage": "synthesizing",
            "message": "正在合成最终结果...",
            "progress": 95
        }
        
        # 记录agent_results信息用于调试
        logger.info(f"[Result Synthesis] Starting synthesis with {len(agent_results)} agent results")
        logger.info(f"[Result Synthesis] Agent IDs: {list(agent_results.keys())}")
        
        # 检查是否有结果合成智能体
        synthesis_agent = self.agent_pool.get("result_synthesis_agent")
        if synthesis_agent:
            logger.info("[Result Synthesis] Using result_synthesis_agent for synthesis")
            try:
                # 准备agent_results，确保StandardResult被正确转换
                prepared_agent_results = {}
                for agent_id, result in agent_results.items():
                    from .agents.protocols import StandardResult
                    if isinstance(result, StandardResult):
                        # 转换StandardResult为字典格式
                        prepared_agent_results[agent_id] = {
                            "agent_type": "standardized",
                            "execution_success": result.success,
                            "result": result.output,
                            "confidence": result.confidence,
                            "quality_score": result.quality_score,
                            "artifacts": [a.to_dict() for a in result.artifacts] if result.artifacts else []
                        }
                    elif isinstance(result, dict):
                        prepared_agent_results[agent_id] = result
                    else:
                        # 其他类型，转换为字典
                        prepared_agent_results[agent_id] = {
                            "agent_type": "unknown",
                            "execution_success": True,
                            "result": result
                        }
                
                logger.info(f"[Result Synthesis] Prepared {len(prepared_agent_results)} agent results for synthesis")
                
                # 检查是否是标准化智能体（StandardizedAgent或AgentAdapter）
                from .agents.standardized_agent import StandardizedAgent
                from .agents.protocols import StandardTask, TaskPriority
                
                if isinstance(synthesis_agent, StandardizedAgent):
                    # 使用标准化接口
                    standard_task = StandardTask(
                        task_id=f"{execution_id}_synthesis",
                        task_type="result_synthesis",
                        description=context.get("user_input", "合成智能体执行结果"),
                        input_data={
                            "agent_results": prepared_agent_results,
                            "task": context.get("user_input", ""),
                            "synthesis_plan": None
                        },
                        context=context,
                        priority=TaskPriority.HIGH
                    )
                    # 添加超时保护，避免合成过程时间过长
                    synthesis_result = await asyncio.wait_for(
                        synthesis_agent.execute(standard_task),
                        timeout=90.0  # 90秒超时
                    )
                else:
                    # 使用旧接口（向后兼容）
                    synthesis_result = await asyncio.wait_for(
                        synthesis_agent.execute({
                            "agent_results": prepared_agent_results,
                            "task": context.get("user_input", ""),
                            "synthesis_plan": None
                        }, context),
                        timeout=90.0  # 90秒超时
                    )
                
                logger.info(f"[Result Synthesis] Synthesis agent returned: type={type(synthesis_result)}, keys={list(synthesis_result.keys()) if isinstance(synthesis_result, dict) else 'N/A'}")
                
                # 支持StandardResult和旧版格式
                from .agents.protocols import StandardResult
                if isinstance(synthesis_result, StandardResult):
                    if synthesis_result.success:
                        final_result = synthesis_result.output if isinstance(synthesis_result.output, dict) else {"formatted_output": synthesis_result.output}
                        # 提取格式化的输出
                        if synthesis_result.artifacts:
                            for artifact in synthesis_result.artifacts:
                                if artifact.artifact_type == "formatted_text":
                                    final_result["formatted_output"] = artifact.content
                                    break
                        if "formatted_output" not in final_result:
                            final_result["formatted_output"] = final_result.get("formatted_output") or str(synthesis_result.output)
                    else:
                        # StandardResult失败，降级到简单合成
                        final_result = await self._synthesize_final_result(
                            agent_results,
                            network_design,
                            context
                        )
                elif isinstance(synthesis_result, dict) and synthesis_result.get("execution_success"):
                    final_result = synthesis_result.get("final_result", {})
                    # 提取格式化的输出（尝试多种可能的字段）
                    formatted_output = (final_result.get("formatted_output") or 
                                      final_result.get("synthesized_result", {}).get("main_content", "") or
                                      final_result.get("synthesized_result", {}).get("formatted_output", "") or
                                      final_result.get("synthesis_report", "") or
                                      str(final_result.get("synthesized_result", {})))
                    
                    # 确保所有必要的字段都存在
                    final_result["formatted_output"] = formatted_output
                    final_result["final_output"] = formatted_output  # 添加 final_output 作为别名
                    final_result["output"] = formatted_output  # 添加 output 作为别名
                    
                    # 如果 synthesized_result 存在，也保留它
                    if "synthesized_result" in final_result:
                        final_result["synthesized_result"] = final_result["synthesized_result"]
                else:
                    # 降级到简单合成
                    final_result = await self._synthesize_final_result(
                        agent_results,
                        network_design,
                        context
                    )
            except asyncio.TimeoutError:
                logger.warning("[Result Synthesis] Result synthesis agent timed out, falling back to simple synthesis")
                final_result = await self._synthesize_final_result(
                    agent_results,
                    network_design,
                    context
                )
            except Exception as e:
                logger.error(f"[Result Synthesis] Result synthesis agent failed: {e}", exc_info=True)
                logger.info("[Result Synthesis] Falling back to simple synthesis")
                final_result = await self._synthesize_final_result(
                    agent_results,
                    network_design,
                    context
                )
        else:
            # 如果没有结果合成智能体，使用简单合成
            logger.warning("[Result Synthesis] result_synthesis_agent not found in agent_pool, using simple synthesis")
            final_result = await self._synthesize_final_result(
                agent_results,
                network_design,
                context
            )
        
        # 确保最终结果包含所有必要的字段（统一结构）
        if isinstance(final_result, dict):
            # 确保有 formatted_output 字段
            if "formatted_output" not in final_result:
                formatted_output = (final_result.get("final_output") or 
                                  final_result.get("output") or 
                                  final_result.get("synthesized_result", {}).get("main_content", "") or
                                  final_result.get("synthesized_result", {}).get("formatted_output", "") or
                                  final_result.get("synthesis_report", "") or
                                  str(final_result))
                final_result["formatted_output"] = formatted_output
            
            # 确保有 final_output 字段（作为 formatted_output 的别名）
            if "final_output" not in final_result:
                final_result["final_output"] = final_result.get("formatted_output", "")
            
            # 确保有 output 字段（作为 formatted_output 的别名）
            if "output" not in final_result:
                final_result["output"] = final_result.get("formatted_output", "")
            
            # 确保有 metadata 字段（包含执行元数据）
            if "metadata" not in final_result:
                # 统计智能体执行情况
                success_count = sum(1 for r in agent_results.values() 
                                  if isinstance(r, dict) and r.get("execution_success", True))
                failure_count = len(agent_results) - success_count
                
                final_result["metadata"] = {
                    "agents_used": list(agent_results.keys()),
                    "execution_time": (datetime.utcnow() - start_time).total_seconds() if 'start_time' in locals() else 0,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "total_agents": len(agent_results)
                }
            
            # 如果formatted_output仍然为空，尝试从agent_results中提取
            if not final_result.get("formatted_output"):
                logger.warning("[Result Synthesis] formatted_output is empty, trying to extract from agent_results")
                # 尝试从最后一个智能体的结果中提取
                if agent_results:
                    last_agent_id = list(agent_results.keys())[-1]
                    last_result = agent_results[last_agent_id]
                    from .agents.protocols import StandardResult
                    if isinstance(last_result, StandardResult):
                        if last_result.artifacts:
                            for artifact in last_result.artifacts:
                                if artifact.artifact_type == "formatted_text":
                                    final_result["formatted_output"] = artifact.content
                                    break
                        if not final_result.get("formatted_output"):
                            final_result["formatted_output"] = str(last_result.output)
                    elif isinstance(last_result, dict):
                        # 特殊处理 format_agent 的结果结构
                        if last_result.get("agent_type") == "format":
                            formatted_content = last_result.get("formatted_content", {})
                            if isinstance(formatted_content, dict):
                                final_result["formatted_output"] = formatted_content.get("formatted_text")
                        
                        # 如果还没有提取到，尝试从 result 字段中提取
                        if not final_result.get("formatted_output"):
                            result_data = last_result.get("result", last_result)
                            if isinstance(result_data, dict):
                                # 再次检查 format_agent 结构
                                if result_data.get("agent_type") == "format":
                                    formatted_content = result_data.get("formatted_content", {})
                                    if isinstance(formatted_content, dict):
                                        final_result["formatted_output"] = formatted_content.get("formatted_text")
                                # 如果还没有，尝试其他字段
                                if not final_result.get("formatted_output"):
                                    final_result["formatted_output"] = (result_data.get("formatted_text") or
                                                                       result_data.get("formatted_output") or
                                                                       (result_data.get("formatted_content", {}).get("formatted_text") if isinstance(result_data.get("formatted_content"), dict) else None) or
                                                                       result_data.get("generated_content") or
                                                                       str(result_data))
                            else:
                                final_result["formatted_output"] = (last_result.get("formatted_output") or
                                                                   last_result.get("output") or
                                                                   str(result_data))
                    else:
                        final_result["formatted_output"] = str(last_result)
            
            logger.info(f"[Result Synthesis] Final result prepared: keys={list(final_result.keys())}, "
                       f"has_formatted_output={'formatted_output' in final_result}, "
                       f"formatted_output_length={len(str(final_result.get('formatted_output', '')))}, "
                       f"formatted_output_preview={str(final_result.get('formatted_output', ''))[:100]}")
            
            # 确保 formatted_output 不为空
            if not final_result.get("formatted_output"):
                logger.warning("[Result Synthesis] formatted_output is empty, generating fallback")
                # 尝试从其他字段提取
                fallback_output = (final_result.get("final_output") or 
                                 final_result.get("output") or 
                                 final_result.get("synthesized_result", {}).get("main_content", "") if isinstance(final_result.get("synthesized_result"), dict) else "" or
                                 str(final_result))
                final_result["formatted_output"] = fallback_output
                final_result["final_output"] = fallback_output
                final_result["output"] = fallback_output
        else:
            logger.warning(f"[Result Synthesis] Final result is not a dict: type={type(final_result)}")
            # 转换为字典格式
            final_result = {
                "formatted_output": str(final_result),
                "final_output": str(final_result),
                "output": str(final_result),
                "success": True
            }
        
        # 最终检查：确保 formatted_output 不为空
        if not final_result.get("formatted_output"):
            logger.error("[Result Synthesis] formatted_output is still empty after all attempts, using default message")
            final_result["formatted_output"] = "执行完成，但未能生成输出内容。请检查智能体执行结果。"
            final_result["final_output"] = final_result["formatted_output"]
            final_result["output"] = final_result["formatted_output"]
        
        logger.info(f"[Result Synthesis] Sending execution_complete chunk: has_final_result={bool(final_result)}, "
                   f"formatted_output_length={len(str(final_result.get('formatted_output', '')))}, "
                   f"formatted_output_preview={str(final_result.get('formatted_output', ''))[:100]}")
        
        yield {
            "type": "execution",
            "stage": "execution_complete",
            "message": "智能体网络执行完成",
            "final_result": final_result,
            "progress": 100
        }
    
    def _prepare_agent_input(
        self,
        agent_spec: Dict[str, Any],
        agent_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备智能体输入数据（确保StandardResult被正确转换）"""
        
        input_data = agent_spec.get("input", {}).copy()
        
        # 解析依赖的输出
        dependencies = agent_spec.get("dependencies", [])
        from .agents.protocols import StandardResult
        for dep_id in dependencies:
            dep_result = agent_results.get(dep_id, {})
            
            # 支持StandardResult和旧版格式
            if isinstance(dep_result, StandardResult):
                dep_output_key = f"{dep_id}_result"
                # 将依赖结果添加到输入（提取output，确保可序列化）
                if dep_output_key in context:
                    context_value = context[dep_output_key]
                    # 如果context中的值也是StandardResult，需要转换
                    if isinstance(context_value, StandardResult):
                        input_data[dep_output_key] = context_value.output
                    else:
                        input_data[dep_output_key] = context_value
                else:
                    # 提取output，确保可序列化
                    input_data[dep_output_key] = dep_result.output
            elif isinstance(dep_result, dict):
                dep_output_key = dep_result.get("output_key", f"{dep_id}_result")
                
                # 将依赖结果添加到输入
                if dep_output_key in context:
                    context_value = context[dep_output_key]
                    # 如果context中的值是StandardResult，需要转换
                    if isinstance(context_value, StandardResult):
                        input_data[dep_output_key] = context_value.output
                    else:
                        input_data[dep_output_key] = context_value
                elif isinstance(dep_result, dict) and "result" in dep_result:
                    result_value = dep_result["result"]
                    # 如果result是StandardResult，需要转换
                    if isinstance(result_value, StandardResult):
                        input_data[dep_output_key] = result_value.output
                    else:
                        input_data[dep_output_key] = result_value
        
        # 添加任务描述
        if "task" not in input_data:
            input_data["task"] = agent_spec.get("task", context.get("user_input", ""))
        
        # 添加执行计划（如果有）
        if agent_spec.get("agent_type") == "mcp_tool_agent":
            input_data["execution_plan"] = agent_spec.get("execution_plan")
        elif agent_spec.get("agent_type") == "workflow_agent":
            input_data["workflow_decision"] = agent_spec.get("workflow_decision")
        elif agent_spec.get("agent_type") == "metadata_agent":
            input_data["enhancement_plan"] = agent_spec.get("enhancement_plan")
        
        # 清理input_data，确保所有值都可以序列化
        input_data = self._clean_data_for_serialization(input_data)
        
        return input_data
    
    def _clean_data_for_serialization(self, data: Any) -> Any:
        """
        清理数据，确保可以JSON序列化（移除StandardResult等不可序列化对象）
        
        Args:
            data: 要清理的数据
            
        Returns:
            清理后的数据
        """
        from .agents.protocols import StandardResult
        
        if isinstance(data, StandardResult):
            # 转换StandardResult为字典
            return data.to_dict()
        elif isinstance(data, dict):
            # 递归清理字典
            cleaned = {}
            for key, value in data.items():
                cleaned[key] = self._clean_data_for_serialization(value)
            return cleaned
        elif isinstance(data, list):
            # 清理列表中的元素
            return [self._clean_data_for_serialization(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            # 基本类型，可以直接序列化
            return data
        else:
            # 其他类型，尝试转换为字符串
            try:
                import json
                json.dumps(data, ensure_ascii=False)
                return data
            except (TypeError, ValueError):
                return str(data)
    
    def _generate_error_suggestion(
        self,
        error_type: str,
        agent_id: str,
        agent_spec: Dict[str, Any]
    ) -> str:
        """生成错误建议"""
        agent_type = agent_spec.get("agent_type", "unknown")
        
        suggestions = {
            "TimeoutError": f"智能体 {agent_id} 执行超时，建议：1) 检查数据量是否过大 2) 优化查询条件 3) 增加超时时间",
            "ConnectionError": f"智能体 {agent_id} 连接失败，建议：1) 检查网络连接 2) 检查服务是否可用 3) 重试操作",
            "ValueError": f"智能体 {agent_id} 参数错误，建议：1) 检查输入参数格式 2) 验证必需参数是否存在",
            "KeyError": f"智能体 {agent_id} 缺少必需字段，建议：1) 检查上下文数据 2) 验证前置智能体输出",
            "AttributeError": f"智能体 {agent_id} 对象属性错误，建议：1) 检查对象类型 2) 验证方法调用",
        }
        
        # 根据智能体类型提供特定建议
        if agent_type == "data_query":
            return suggestions.get(error_type, f"数据查询智能体失败，建议检查数据源连接和查询条件")
        elif agent_type == "metadata":
            return suggestions.get(error_type, f"元数据智能体失败，建议检查元数据服务是否可用")
        elif agent_type == "format":
            return suggestions.get(error_type, f"格式化智能体失败，建议检查输入数据格式")
        else:
            return suggestions.get(error_type, f"智能体执行失败，建议检查日志获取详细信息")
    
    async def _is_critical_agent(
        self,
        agent_id: str,
        network_design: Dict[str, Any]
    ) -> bool:
        """判断是否是关键智能体"""
        
        agents = network_design.get("agents", [])
        agent_spec = next((a for a in agents if a.get("id") == agent_id), None)
        
        if not agent_spec:
            return False
        
        # 检查是否有其他智能体依赖它
        agent_type = agent_spec.get("agent_type")
        
        # 元数据智能体通常是关键的
        if agent_type == "metadata_agent":
            return True
        
        # 检查依赖关系
        for agent in agents:
            if agent_id in agent.get("dependencies", []):
                return True
        
        return False
    
    async def _synthesize_final_result(
        self,
        agent_results: Dict[str, Any],
        network_design: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合成最终结果"""
        
        # 收集所有成功的结果
        from .agents.protocols import StandardResult
        successful_results = {}
        for agent_id, result in agent_results.items():
            if isinstance(result, StandardResult):
                if result.success:
                    successful_results[agent_id] = result
            elif isinstance(result, dict):
                # 优先使用 execution_success，如果不存在则使用 success，如果都不存在则默认为 True（成功）
                # 因为如果智能体没有明确返回失败，说明它执行成功了
                is_success = True
                if "execution_success" in result:
                    is_success = result["execution_success"]
                elif "success" in result:
                    is_success = result["success"]
                # 如果都不存在，默认为成功
                if is_success:
                    successful_results[agent_id] = result
        
        # 收集所有失败的结果
        failed_results = {}
        for agent_id, result in agent_results.items():
            if isinstance(result, StandardResult):
                if not result.success:
                    failed_results[agent_id] = result
            elif isinstance(result, dict):
                # 优先使用 execution_success，如果不存在则使用 success，如果都不存在则默认为 True（成功）
                # 因为如果智能体没有明确返回失败，说明它执行成功了
                is_success = True
                if "execution_success" in result:
                    is_success = result["execution_success"]
                elif "success" in result:
                    is_success = result["success"]
                # 如果都不存在，默认为成功（不添加到失败结果中）
                if not is_success:
                    failed_results[agent_id] = result
        
        # 提取最终输出（通常是最后一个智能体的输出）
        agents = network_design.get("agents", [])
        execution_layers = network_design.get("execution_layers", [])
        
        final_output = None
        if execution_layers:
            last_layer = execution_layers[-1]
            for agent_id in reversed(last_layer):
                if agent_id in successful_results:
                    result = successful_results[agent_id]
                    
                    # 支持StandardResult和旧版格式
                    from .agents.protocols import StandardResult
                    if isinstance(result, StandardResult):
                        actual_result = result.output
                        # 优先使用formatted_output（如果有）
                        if result.artifacts:
                            for artifact in result.artifacts:
                                if artifact.artifact_type == "formatted_text":
                                    final_output = artifact.content
                                    break
                        if not final_output:
                            if isinstance(actual_result, dict):
                                # 尝试多种可能的字段（按优先级）
                                final_output = (actual_result.get("formatted_text") or 
                                              actual_result.get("formatted_output") or
                                              actual_result.get("formatted_content") or
                                              actual_result.get("generated_content") or
                                              actual_result.get("content") or
                                              actual_result.get("text") or
                                              actual_result.get("message") or
                                              actual_result.get("output") or
                                              actual_result.get("main_content") or
                                              None)
                                # 如果还是没有，尝试从sections中提取
                                if not final_output and actual_result.get("sections"):
                                    sections = actual_result.get("sections", [])
                                    if sections and isinstance(sections, list):
                                        # 合并所有sections的内容
                                        section_texts = []
                                        for section in sections:
                                            if isinstance(section, dict):
                                                section_texts.append(section.get("content", ""))
                                        if section_texts:
                                            final_output = "\n\n".join(section_texts)
                                # 如果还是没有，转换为字符串
                                if not final_output:
                                    final_output = str(actual_result)
                            else:
                                final_output = str(actual_result) if actual_result else None
                    else:
                        # 旧版格式
                        actual_result = result.get("result", result)
                        if isinstance(actual_result, dict):
                            # 特殊处理 format_agent 的结果结构
                            if actual_result.get("agent_type") == "format":
                                formatted_content = actual_result.get("formatted_content", {})
                                if isinstance(formatted_content, dict):
                                    final_output = formatted_content.get("formatted_text")
                                if not final_output:
                                    final_output = actual_result.get("formatted_text")
                            
                            # 尝试多种可能的字段（按优先级）
                            if not final_output:
                                final_output = (actual_result.get("formatted_text") or 
                                              actual_result.get("formatted_output") or
                                              actual_result.get("formatted_content") or
                                              actual_result.get("generated_content") or
                                              actual_result.get("content") or
                                              actual_result.get("text") or
                                              actual_result.get("message") or
                                              actual_result.get("insights") or
                                              actual_result.get("analysis_result") or
                                              actual_result.get("output") or
                                              actual_result.get("main_content") or
                                              None)
                            
                            # 如果 formatted_content 是字典，尝试提取 formatted_text
                            if not final_output and isinstance(actual_result.get("formatted_content"), dict):
                                final_output = actual_result.get("formatted_content", {}).get("formatted_text")
                            # 如果还是没有，尝试从sections中提取
                            if not final_output and actual_result.get("sections"):
                                sections = actual_result.get("sections", [])
                                if sections and isinstance(sections, list):
                                    # 合并所有sections的内容
                                    section_texts = []
                                    for section in sections:
                                        if isinstance(section, dict):
                                            section_texts.append(section.get("content", ""))
                                    if section_texts:
                                        final_output = "\n\n".join(section_texts)
                            # 如果还是没有，转换为字符串
                            if not final_output:
                                final_output = str(actual_result)
                        else:
                            final_output = str(actual_result) if actual_result else None
                    
                    if final_output:
                        logger.info(f"Found final output from agent {agent_id}: {str(final_output)[:100]}")
                        break
        
        # 如果没有找到最终输出，尝试从上下文获取
        if not final_output:
            for key in reversed(list(context.keys())):
                if key.endswith("_result") or key == "result":
                    context_value = context[key]
                    # 如果上下文值是 format_agent 的结果，提取 formatted_text
                    if isinstance(context_value, dict) and context_value.get("agent_type") == "format":
                        formatted_content = context_value.get("formatted_content", {})
                        if isinstance(formatted_content, dict):
                            final_output = formatted_content.get("formatted_text")
                    if not final_output:
                        final_output = context_value
                    logger.info(f"Found final output from context key {key}")
                    break
        
        # 如果还是没有找到，尝试从所有成功结果中提取
        if not final_output and successful_results:
            logger.warning("Final output not found in last layer, trying all successful results")
            for agent_id, result in reversed(list(successful_results.items())):
                from .agents.protocols import StandardResult
                # 尝试提取格式化输出
                if isinstance(result, StandardResult):
                    if result.artifacts:
                        for artifact in result.artifacts:
                            if artifact.artifact_type == "formatted_text":
                                final_output = artifact.content
                                if final_output:
                                    logger.info(f"Found final output from agent {agent_id} artifacts")
                                    break
                    if not final_output and result.output:
                        if isinstance(result.output, dict):
                            final_output = (result.output.get("formatted_output") or 
                                          result.output.get("formatted_text") or
                                          result.output.get("main_content") or
                                          str(result.output))
                        else:
                            final_output = str(result.output)
                elif isinstance(result, dict):
                    # 尝试从字典结果中提取
                    actual_result = result.get("result", result)
                    if isinstance(actual_result, dict):
                        final_output = (actual_result.get("formatted_output") or 
                                      actual_result.get("formatted_text") or
                                      actual_result.get("main_content") or
                                      actual_result.get("output") or
                                      str(actual_result))
                    else:
                        final_output = str(actual_result) if actual_result else None
                
                if final_output:
                    logger.info(f"Found final output from agent {agent_id}: {str(final_output)[:100]}")
                    break
                if isinstance(result, StandardResult):
                    actual_result = result.output
                    if isinstance(actual_result, dict):
                        final_output = (actual_result.get("formatted_text") or 
                                      actual_result.get("formatted_output") or
                                      actual_result.get("generated_content") or
                                      str(actual_result))
                    else:
                        final_output = str(actual_result) if actual_result else None
                else:
                    actual_result = result.get("result", result)
                    if isinstance(actual_result, dict):
                        # 特殊处理 format_agent 的结果结构
                        if actual_result.get("agent_type") == "format":
                            formatted_content = actual_result.get("formatted_content", {})
                            if isinstance(formatted_content, dict):
                                final_output = formatted_content.get("formatted_text")
                        if not final_output:
                            final_output = (actual_result.get("formatted_text") or 
                                          actual_result.get("formatted_output") or
                                          (actual_result.get("formatted_content", {}).get("formatted_text") if isinstance(actual_result.get("formatted_content"), dict) else None) or
                                          actual_result.get("generated_content") or
                                          str(actual_result))
                    else:
                        final_output = str(actual_result) if actual_result else None
                
                if final_output:
                    logger.info(f"Found final output from agent {agent_id}: {str(final_output)[:100]}")
                    break
        
        # 如果还是没有找到输出，使用降级方案：从所有智能体结果中生成摘要
        if not final_output:
            logger.warning("[Result Synthesis] No final output found, generating fallback summary")
            # 尝试从所有成功结果中生成一个摘要
            summary_parts = []
            for agent_id, result in successful_results.items():
                from .agents.protocols import StandardResult
                if isinstance(result, StandardResult):
                    if result.output:
                        summary_parts.append(f"**{agent_id}**: {str(result.output)[:200]}")
                elif isinstance(result, dict):
                    result_data = result.get("result", result)
                    if result_data:
                        summary_parts.append(f"**{agent_id}**: {str(result_data)[:200]}")
            
            if summary_parts:
                final_output = "\n\n".join(summary_parts)
            else:
                # 最后的降级：生成一个基本响应，包含失败原因和建议
                user_input = context.get("user_input", "查询")
                
                # 收集失败原因
                failure_reasons = []
                for agent_id, result in failed_results.items():
                    error_msg = ""
                    if isinstance(result, dict):
                        error_msg = result.get("error", result.get("reason", "未知错误"))
                    failure_reasons.append(f"- {agent_id}: {error_msg}")
                
                if failure_reasons:
                    final_output = f"执行完成，但遇到以下问题：\n\n" + \
                                 f"**执行摘要**：\n" + \
                                 f"- 总智能体数：{len(agent_results)}\n" + \
                                 f"- 成功：{len(successful_results)}\n" + \
                                 f"- 失败：{len(failed_results)}\n\n" + \
                                 f"**失败原因**：\n" + "\n".join(failure_reasons) + "\n\n" + \
                                 f"**建议**：\n" + \
                                 f"1. 检查失败智能体的错误信息\n" + \
                                 f"2. 验证输入数据和上下文是否正确\n" + \
                                 f"3. 检查相关服务是否可用\n" + \
                                 f"4. 如问题持续，请联系系统管理员"
                else:
                    final_output = f"已成功执行{len(successful_results)}个智能体任务。\n\n" + \
                                 f"执行了{len(agent_results)}个智能体，其中{len(successful_results)}个成功，{len(failed_results)}个失败。"
        
        # 确保同时提供 final_output 和 formatted_output 字段（前端兼容性）
        formatted_output = final_output
        if isinstance(final_output, dict):
            # 如果 final_output 是字典，尝试提取文本内容
            formatted_output = (final_output.get("formatted_output") or 
                              final_output.get("formatted_text") or
                              final_output.get("content") or
                              final_output.get("text") or
                              final_output.get("main_content") or
                              str(final_output))
        elif not isinstance(final_output, str) and final_output is not None:
            # 如果不是字符串，转换为字符串
            formatted_output = str(final_output)
        elif final_output is None:
            # 如果仍然是None，使用默认消息
            formatted_output = "执行完成，但未生成输出内容。"
        
        logger.info(f"[Result Synthesis] Final result prepared: has_output={bool(final_output)}, "
                   f"output_length={len(str(formatted_output)) if formatted_output else 0}, "
                   f"output_preview={str(formatted_output)[:100] if formatted_output else 'None'}")
        
        return {
            "success": len(failed_results) == 0,
            "final_output": final_output,
            "formatted_output": formatted_output,  # 添加 formatted_output 字段以兼容前端
            "output": formatted_output,  # 添加 output 字段作为别名
            "agent_results": {
                "successful": len(successful_results),
                "failed": len(failed_results),
                "total": len(agent_results)
            },
            "execution_summary": {
                "total_agents": len(agents),
                "executed_agents": len(agent_results),
                "success_rate": len(successful_results) / len(agent_results) if agent_results else 0.0
            },
            "details": {
                "successful_agents": list(successful_results.keys()),
                "failed_agents": list(failed_results.keys())
            }
        }

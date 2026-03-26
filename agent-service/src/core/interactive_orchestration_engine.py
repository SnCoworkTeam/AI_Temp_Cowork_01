"""
交互式编排引擎
支持实时交互、执行控制、用户反馈
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .orchestration_engine import OrchestrationEngine, ExecutionStrategy
from .task_classifier import RoutingDecision
from .websocket_manager.websocket_manager import websocket_manager
from ..models.prompt_models import (
    InteractiveMessage, InteractionType, ExecutionStatus, 
    ExecutionState, UserAction
)

logger = logging.getLogger(__name__)


class InteractiveOrchestrationEngine(OrchestrationEngine):
    """交互式编排引擎 - 扩展基础编排引擎，添加交互能力"""
    
    def __init__(self):
        super().__init__()
        self.execution_states: Dict[str, ExecutionState] = {}
        self._execution_futures: Dict[str, asyncio.Future] = {}
        self._confirmation_waiters: Dict[str, asyncio.Future] = {}
        self._input_waiters: Dict[str, asyncio.Future] = {}
        self._register_websocket_handlers()
    
    def _register_websocket_handlers(self):
        """注册WebSocket消息处理器"""
        websocket_manager.register_handler("pause_execution", self._handle_pause)
        websocket_manager.register_handler("resume_execution", self._handle_resume)
        websocket_manager.register_handler("cancel_execution", self._handle_cancel)
        websocket_manager.register_handler("confirm_action", self._handle_confirmation)
        websocket_manager.register_handler("provide_input", self._handle_user_input)
        logger.info("WebSocket handlers registered for interactive orchestration")
    
    async def orchestrate_interactive(
        self, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        交互式编排执行
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            编排结果
        """
        execution_id = self._generate_execution_id()
        session_id = context.get('session_id', 'default')
        
        # 初始化执行状态
        execution_state = ExecutionState(
            execution_id=execution_id,
            session_id=session_id,
            status=ExecutionStatus.PENDING,
            user_input=user_input,
            context=context
        )
        self.execution_states[execution_id] = execution_state
        
        try:
            # 发送开始消息
            await self._send_execution_start(execution_id, session_id, user_input)
            
            # 更新状态为运行中
            execution_state.status = ExecutionStatus.RUNNING
            execution_state.updated_at = datetime.now()
            
            # 执行编排流程（支持暂停和取消）
            result = await self._execute_with_control(execution_id, user_input, context)
            
            # 更新状态为完成
            execution_state.status = ExecutionStatus.COMPLETED
            execution_state.progress = 1.0
            execution_state.updated_at = datetime.now()
            
            # 发送完成消息
            await self._send_execution_complete(execution_id, session_id, result)
            
            return result
            
        except asyncio.CancelledError:
            execution_state.status = ExecutionStatus.CANCELLED
            execution_state.updated_at = datetime.now()
            await self._send_execution_cancelled(execution_id, session_id)
            raise
        except Exception as e:
            execution_state.status = ExecutionStatus.ERROR
            execution_state.updated_at = datetime.now()
            await self._send_execution_error(execution_id, session_id, str(e))
            raise
        finally:
            # 清理等待器
            self._confirmation_waiters.pop(execution_id, None)
            self._input_waiters.pop(execution_id, None)
            self._execution_futures.pop(execution_id, None)
    
    async def _execute_with_control(
        self, 
        execution_id: str, 
        user_input: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """支持控制的执行流程"""
        state = self.execution_states[execution_id]
        
        # 1. 任务理解（可暂停点）
        await self._check_pause_or_cancel(execution_id)
        await self._send_progress(execution_id, state.session_id, "分析用户意图", 0.1)
        
        # 构建提示词上下文
        from ..models.prompt_models import PromptContext
        prompt_context = None
        if self.prompt_engine:
            try:
                prompt_context = PromptContext(
                    user_id=context.get('user_id'),
                    session_id=context.get('session_id'),
                    conversation_history=context.get('history', []),
                    user_profile=context.get('user_profile'),
                    task_context=context.get('task_context'),
                    available_tools=context.get('available_tools', [])
                )
            except Exception as e:
                logger.warning(f"Failed to create prompt context: {e}")
        
        intent_analysis = await self.conversation_agent.understand_conversation(
            user_input, 
            context.get('history'), 
            {k: v for k, v in context.items() if k not in ['history', 'available_agents']},
            prompt_engine=self.prompt_engine,
            prompt_context=prompt_context
        )
        
        # 2. 任务分类（可暂停点）
        await self._check_pause_or_cancel(execution_id)
        await self._send_progress(execution_id, state.session_id, "分类任务类型", 0.3)
        
        routing_decision = await self.task_classifier.classify_and_route(
            intent_analysis, context.get('available_agents')
        )
        
        # 3. 执行策略（支持复杂交互）
        if routing_decision.strategy == ExecutionStrategy.ORCHESTRATION:
            return await self._execute_complex_with_interaction(
                execution_id, user_input, context, routing_decision, prompt_context
            )
        else:
            return await self._execute_simple_with_progress(
                execution_id, user_input, context, routing_decision, intent_analysis, prompt_context
            )
    
    async def _execute_simple_with_progress(
        self,
        execution_id: str,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        intent_analysis: Optional[Any] = None,
        prompt_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """带进度反馈的简单任务执行"""
        state = self.execution_states[execution_id]
        session_id = state.session_id
        
        await self._send_progress(execution_id, session_id, "执行任务", 0.5)
        
        # 使用基础编排引擎的执行方法
        execution_methods = {
            ExecutionStrategy.DIRECT_LLM: self._handle_direct_llm,
            ExecutionStrategy.TOOL_CALL: lambda ui, ctx, rd, pc: self._handle_tool_execution(ui, ctx, rd, intent_analysis, pc),
            ExecutionStrategy.WORKFLOW_EXECUTION: self._handle_workflow,
            ExecutionStrategy.SERVICE_DELEGATION: self._handle_service_delegation,
        }
        
        handler = execution_methods.get(decision.strategy, self._handle_direct_llm)
        result = await handler(user_input, context, decision, prompt_context)
        
        await self._send_progress(execution_id, session_id, "任务完成", 1.0)
        
        return result
    
    async def _execute_complex_with_interaction(
        self, 
        execution_id: str, 
        user_input: str, 
        context: Dict[str, Any],
        decision: RoutingDecision,
        prompt_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """带交互的复杂任务执行"""
        state = self.execution_states[execution_id]
        session_id = state.session_id
        
        # 发送任务分解步骤
        await self._send_execution_step(
            execution_id, session_id, 
            "complex_task_decomposition", 
            "正在分解复杂任务...",
            {"strategy": decision.strategy.value}
        )
        
        # 执行DAG分解
        try:
            decomposition_result = await self.service_clients.dag_orchestrator.decompose_task(
                user_input=user_input,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to decompose task: {e}")
            # 降级到简单执行
            return await self._execute_simple_with_progress(
                execution_id, user_input, context, decision, prompt_context
            )
        
        if not decomposition_result or not hasattr(decomposition_result, 'subtasks'):
            logger.warning("Decomposition result invalid, falling back to simple execution")
            return await self._execute_simple_with_progress(
                execution_id, user_input, context, decision, prompt_context
            )
        
        # 更新总步骤数
        subtasks = decomposition_result.subtasks if hasattr(decomposition_result, 'subtasks') else []
        state.total_steps = len(subtasks)
        state.current_step = 0
        
        # 发送分解结果给用户
        await self._send_execution_step(
            execution_id, session_id,
            "task_decomposed",
            f"任务已分解为 {state.total_steps} 个子任务",
            {"subtasks": [st.get('name', 'unknown') if isinstance(st, dict) else getattr(st, 'name', 'unknown') for st in subtasks]}
        )
        
        # 执行每个子任务（带进度反馈）
        results = []
        for i, subtask in enumerate(subtasks):
            await self._check_pause_or_cancel(execution_id)
            
            state.current_step = i + 1
            progress = (i + 1) / state.total_steps if state.total_steps > 0 else 1.0
            
            subtask_name = subtask.get('name', f'Subtask {i+1}') if isinstance(subtask, dict) else getattr(subtask, 'name', f'Subtask {i+1}')
            
            await self._send_progress(
                execution_id, session_id, 
                f"执行子任务: {subtask_name}", 
                progress
            )
            
            # 执行子任务
            try:
                result = await self._execute_subtask(subtask, context, execution_id)
                results.append(result)
                
                # 发送步骤完成通知
                await self._send_execution_step(
                    execution_id, session_id,
                    "subtask_completed",
                    f"完成: {subtask_name}",
                    {"subtask_index": i, "result_preview": str(result)[:100]}
                )
            except Exception as e:
                logger.error(f"Subtask {i+1} failed: {e}")
                results.append({"success": False, "error": str(e)})
        
        # 整合结果
        final_result = await self._aggregate_results(results, decomposition_result)
        return final_result
    
    async def _execute_subtask(
        self, 
        subtask: Any, 
        context: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """执行单个子任务（支持用户交互）"""
        # 解析子任务信息
        if isinstance(subtask, dict):
            subtask_type = subtask.get('type', 'unknown')
            subtask_name = subtask.get('name', 'unknown')
            subtask_params = subtask.get('parameters', {})
        else:
            subtask_type = getattr(subtask, 'type', 'unknown')
            subtask_name = getattr(subtask, 'name', 'unknown')
            subtask_params = getattr(subtask, 'parameters', {})
        
        # 如果需要用户确认
        if self._requires_confirmation(subtask):
            confirmation = await self._request_confirmation(execution_id, subtask_name, subtask)
            if not confirmation:
                raise Exception("用户取消了操作")
        
        # 如果需要用户输入
        if self._requires_user_input(subtask):
            user_input = await self._request_user_input(execution_id, subtask_name, subtask)
            # 使用用户输入更新任务参数
            if isinstance(subtask_params, dict):
                subtask_params.update(user_input)
        
        # 执行具体任务
        if subtask_type == "mcp_tool" or "tool" in subtask_type.lower():
            tool_name = subtask_params.get('tool_name') or subtask_name
            return await self.service_clients.mcp_gateway.execute_tool(
                tool_name, subtask_params
            )
        elif subtask_type == "knowledge" or "search" in subtask_type.lower():
            query = subtask_params.get('query', '')
            return await self.service_clients.knowledge_base.semantic_search(
                query, subtask_params.get('filters', {})
            )
        else:
            # 默认使用LLM处理
            return await self._handle_direct_llm(
                str(subtask_params.get('input', subtask_name)),
                context,
                RoutingDecision(
                    strategy=ExecutionStrategy.DIRECT_LLM,
                    target_service="chat-service",
                    reasoning="Default LLM handling"
                )
            )
    
    def _requires_confirmation(self, subtask: Any) -> bool:
        """检查是否需要用户确认"""
        if isinstance(subtask, dict):
            return subtask.get('requires_confirmation', False)
        return getattr(subtask, 'requires_confirmation', False)
    
    def _requires_user_input(self, subtask: Any) -> bool:
        """检查是否需要用户输入"""
        if isinstance(subtask, dict):
            return subtask.get('requires_user_input', False)
        return getattr(subtask, 'requires_user_input', False)
    
    async def _request_confirmation(
        self, 
        execution_id: str, 
        subtask_name: str,
        subtask: Any
    ) -> bool:
        """请求用户确认"""
        state = self.execution_states[execution_id]
        session_id = state.session_id
        
        # 发送确认请求
        confirmation_message = {
            "type": InteractionType.CONFIRMATION_REQUIRED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "subtask": subtask_name,
                "description": str(subtask.get('description', '') if isinstance(subtask, dict) else getattr(subtask, 'description', '')),
                "actions_required": subtask.get('actions_required', []) if isinstance(subtask, dict) else getattr(subtask, 'actions_required', [])
            },
            "actions": ["confirm", "cancel"]
        }
        
        await websocket_manager.send_execution_update(confirmation_message)
        
        # 设置等待状态
        state.waiting_for_input = "confirmation"
        state.status = ExecutionStatus.WAITING_FOR_INPUT
        state.updated_at = datetime.now()
        
        # 创建等待Future
        future = asyncio.Future()
        self._confirmation_waiters[execution_id] = future
        
        # 等待用户响应（带超时）
        try:
            return await asyncio.wait_for(future, timeout=30.0)  # 30秒超时
        except asyncio.TimeoutError:
            logger.warning(f"Confirmation timeout for execution {execution_id}")
            return False  # 超时默认取消
    
    async def _request_user_input(
        self, 
        execution_id: str, 
        subtask_name: str,
        subtask: Any
    ) -> Dict[str, Any]:
        """请求用户输入"""
        state = self.execution_states[execution_id]
        session_id = state.session_id
        
        # 发送输入请求
        input_message = {
            "type": InteractionType.USER_INTERACTION_REQUIRED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "subtask": subtask_name,
                "required_parameters": subtask.get('required_parameters', []) if isinstance(subtask, dict) else getattr(subtask, 'required_parameters', []),
                "input_description": subtask.get('input_description', '') if isinstance(subtask, dict) else getattr(subtask, 'input_description', '')
            },
            "actions": ["provide_input", "cancel"]
        }
        
        await websocket_manager.send_execution_update(input_message)
        
        # 设置等待状态
        state.waiting_for_input = "user_input"
        state.status = ExecutionStatus.WAITING_FOR_INPUT
        state.updated_at = datetime.now()
        
        # 创建等待Future
        future = asyncio.Future()
        self._input_waiters[execution_id] = future
        
        # 等待用户输入（带超时）
        try:
            return await asyncio.wait_for(future, timeout=60.0)  # 60秒超时
        except asyncio.TimeoutError:
            logger.warning(f"User input timeout for execution {execution_id}")
            raise Exception("用户输入超时")
    
    async def _check_pause_or_cancel(self, execution_id: str):
        """检查暂停或取消状态"""
        state = self.execution_states.get(execution_id)
        if not state:
            return
        
        if state.cancelled:
            raise asyncio.CancelledError("执行已被取消")
        
        while state.paused:
            await asyncio.sleep(0.1)  # 短暂等待
            if state.cancelled:
                raise asyncio.CancelledError("执行已被取消")
    
    # WebSocket消息处理
    async def _handle_pause(self, action: UserAction, session_id: str):
        """处理暂停请求"""
        execution_id = action.execution_id
        if execution_id in self.execution_states:
            state = self.execution_states[execution_id]
            state.paused = True
            state.status = ExecutionStatus.PAUSED
            state.updated_at = datetime.now()
            await self._send_execution_paused(execution_id, session_id)
            logger.info(f"Execution {execution_id} paused")
    
    async def _handle_resume(self, action: UserAction, session_id: str):
        """处理继续请求"""
        execution_id = action.execution_id
        if execution_id in self.execution_states:
            state = self.execution_states[execution_id]
            state.paused = False
            state.status = ExecutionStatus.RUNNING
            state.updated_at = datetime.now()
            await self._send_execution_resumed(execution_id, session_id)
            logger.info(f"Execution {execution_id} resumed")
    
    async def _handle_cancel(self, action: UserAction, session_id: str):
        """处理取消请求"""
        execution_id = action.execution_id
        if execution_id in self.execution_states:
            state = self.execution_states[execution_id]
            state.cancelled = True
            state.status = ExecutionStatus.CANCELLED
            state.updated_at = datetime.now()
            await self._send_execution_cancelled(execution_id, session_id)
            logger.info(f"Execution {execution_id} cancelled")
    
    async def _handle_confirmation(self, action: UserAction, session_id: str):
        """处理确认响应"""
        execution_id = action.execution_id
        if execution_id in self._confirmation_waiters:
            confirmed = action.parameters.get('confirmed', False)
            future = self._confirmation_waiters[execution_id]
            if not future.done():
                future.set_result(confirmed)
            
            # 更新状态
            if execution_id in self.execution_states:
                state = self.execution_states[execution_id]
                state.waiting_for_input = None
                state.status = ExecutionStatus.RUNNING
                state.updated_at = datetime.now()
    
    async def _handle_user_input(self, action: UserAction, session_id: str):
        """处理用户输入响应"""
        execution_id = action.execution_id
        if execution_id in self._input_waiters:
            user_input = action.parameters.get('input', {})
            future = self._input_waiters[execution_id]
            if not future.done():
                future.set_result(user_input)
            
            # 更新状态
            if execution_id in self.execution_states:
                state = self.execution_states[execution_id]
                state.waiting_for_input = None
                state.status = ExecutionStatus.RUNNING
                state.updated_at = datetime.now()
    
    # 消息发送辅助方法
    async def _send_execution_start(self, execution_id: str, session_id: str, user_input: str):
        """发送执行开始消息"""
        message = {
            "type": InteractionType.EXECUTION_START.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {"user_input": user_input},
            "actions": ["pause", "cancel"]
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_progress(
        self, 
        execution_id: str, 
        session_id: str, 
        message: str, 
        progress: float
    ):
        """发送进度更新"""
        state = self.execution_states.get(execution_id)
        if state:
            state.progress = progress
            state.updated_at = datetime.now()
        
        message_obj = {
            "type": InteractionType.EXECUTION_PROGRESS.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": message,
                "current_step": state.current_step if state else 0,
                "total_steps": state.total_steps if state else 0
            },
            "progress": progress,
            "actions": ["pause", "cancel"]
        }
        await websocket_manager.send_execution_update(message_obj)
    
    async def _send_execution_step(
        self, 
        execution_id: str, 
        session_id: str, 
        step_type: str, 
        description: str, 
        data: Dict[str, Any]
    ):
        """发送执行步骤消息"""
        message = {
            "type": InteractionType.EXECUTION_STEP.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "step_type": step_type,
                "description": description,
                **data
            }
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_execution_complete(self, execution_id: str, session_id: str, result: Dict[str, Any]):
        """发送执行完成消息"""
        message = {
            "type": InteractionType.EXECUTION_COMPLETED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": result,
            "progress": 1.0
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_execution_paused(self, execution_id: str, session_id: str):
        """发送执行暂停消息"""
        message = {
            "type": InteractionType.EXECUTION_PAUSED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "actions": ["resume", "cancel"]
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_execution_resumed(self, execution_id: str, session_id: str):
        """发送执行继续消息"""
        message = {
            "type": InteractionType.EXECUTION_RESUMED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "actions": ["pause", "cancel"]
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_execution_cancelled(self, execution_id: str, session_id: str):
        """发送执行取消消息"""
        message = {
            "type": InteractionType.EXECUTION_CANCELLED.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        await websocket_manager.send_execution_update(message)
    
    async def _send_execution_error(self, execution_id: str, session_id: str, error: str):
        """发送执行错误消息"""
        message = {
            "type": InteractionType.EXECUTION_ERROR.value,
            "execution_id": execution_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "data": {"error": error}
        }
        await websocket_manager.send_execution_update(message)
    
    async def _aggregate_results(self, results: list, decomposition_result: Any) -> Dict[str, Any]:
        """整合子任务结果"""
        # 使用基础引擎的聚合方法
        return {
            "success": True,
            "output": "任务执行完成",
            "results": results,
            "total_subtasks": len(results),
            "completed_subtasks": sum(1 for r in results if r.get('success', False))
        }
    
    def _generate_execution_id(self) -> str:
        """生成执行ID"""
        return str(uuid.uuid4())
    
    def get_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        """获取执行状态"""
        return self.execution_states.get(execution_id)
    
    def list_active_executions(self, session_id: Optional[str] = None) -> list:
        """列出活跃的执行"""
        if session_id:
            return [
                state for state in self.execution_states.values()
                if state.session_id == session_id and state.status in [
                    ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED
                ]
            ]
        return [
            state for state in self.execution_states.values()
            if state.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]
        ]





















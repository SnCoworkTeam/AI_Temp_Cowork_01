"""
智能体工作流节点
将智能体作为工作流节点执行，支持对话、工具调用、上下文管理等功能

关键特性：
- 接口一致性：与现有工作流节点（ToolNode、LLMNode）保持一致的输入输出格式
- 错误处理：健全的重试机制（指数退避）和降级策略
- 性能优化：超时控制、异步执行、资源管理
- 状态管理：对话状态和工作流状态的正确同步
"""
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime
import time
import uuid

from .base_node import BaseNode, NodeExecutionError
from shared_libs.luminaos_common.schemas.agent_schemas import (
    AgentNodeInput,
    AgentNodeOutput,
    AgentContext,
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    AgentExecutionState,
    ConversationMessage,
    ConversationRole
)
from shared_libs.luminaos_common.common.agent_error_handling import (
    AgentErrorCode,
    ERROR_RETRY_POLICIES,
    ERROR_FALLBACK_POLICIES,
    get_error_category,
    AgentErrorCategory
)

# 导入数据库会话
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import SessionLocal
from ..routes.agent_service import AgentService
from ..core.context_manager import ContextManager
from .agent_node_cache import HybridCache, generate_cache_key

logger = logging.getLogger(__name__)


class AgentNode(BaseNode):
    """智能体工作流节点 - 将智能体作为工作流节点执行"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        
        # 从配置中获取智能体ID（必需）
        self.agent_id = self.config.get("agent_id")
        if not self.agent_id:
            raise ValueError(f"AgentNode '{name}' requires 'agent_id' in config")
        
        # 节点配置
        self.input_mapping = self.config.get("input_mapping", {})
        self.output_mapping = self.config.get("output_mapping", {})
        self.retry_count = self.config.get("retry_count", 3)
        self.retry_delay = self.config.get("retry_delay", 5)
        self.enable_streaming = self.config.get("enable_streaming", False)
        self.context_window_size = self.config.get("context_window_size", 10)
        self.preserve_conversation = self.config.get("preserve_conversation", True)
        
        # 性能配置
        self.timeout = self.config.get("timeout", 300)  # 默认5分钟超时
        self.enable_fallback = self.config.get("enable_fallback", True)  # 是否启用降级
        self.fallback_response = self.config.get("fallback_response", "智能体暂时不可用")
        
        # 重试策略（指数退避）
        self.retry_backoff_multiplier = self.config.get("retry_backoff_multiplier", 2.0)
        self.max_retry_delay = self.config.get("max_retry_delay", 60)  # 最大重试延迟60秒
        
        # 第一阶段执行模式
        self.execution_mode = self.config.get("execution_mode", "sync")  # sync/async
        
        # 缓存策略
        self.enable_cache = self.config.get("enable_cache", True)  # 是否启用缓存
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 缓存TTL（秒）
        self.cache_strategy = HybridCache(
            memory_cache_size=self.config.get("memory_cache_size", 1000),
            default_ttl=self.cache_ttl
        ) if self.enable_cache else None
        
        # 延迟初始化AgentService和ContextManager（需要数据库会话）
        self._agent_service: Optional[AgentService] = None
        self._context_manager: Optional[ContextManager] = None
        self._db_session = None
    
    def _get_agent_service(self) -> AgentService:
        """获取AgentService实例（延迟初始化）"""
        if self._agent_service is None:
            # 创建数据库会话
            self._db_session = SessionLocal()
            self._agent_service = AgentService(self._db_session)
        return self._agent_service
    
    def _get_context_manager(self) -> ContextManager:
        """获取ContextManager实例（延迟初始化）"""
        if self._context_manager is None:
            if self._db_session is None:
                self._db_session = SessionLocal()
            self._context_manager = ContextManager(self._db_session)
        return self._context_manager
    
    def _close_db_session(self):
        """关闭数据库会话"""
        if self._db_session:
            try:
                self._db_session.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")
            finally:
                self._db_session = None
                self._agent_service = None
                self._context_manager = None
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体节点（带超时控制和重试机制）
        
        Args:
            state: 当前工作流状态
            
        Returns:
            更新后的状态
        """
        start_time = time.time()
        retry_count = 0
        last_error = None
        last_error_code = None
        
        while retry_count <= self.retry_count:
            try:
                # 检查超时
                elapsed_time = time.time() - start_time
                if elapsed_time >= self.timeout:
                    raise TimeoutError(f"AgentNode execution timeout after {elapsed_time:.2f}s")
                
                # 1. 获取或创建会话ID
                session_id = state.get('session_id') or state.get('conversation_id') or state.get('execution_id') or f"session_{uuid.uuid4()}"
                
                # 2. 构建输入数据（应用输入映射）
                input_data = await self._build_input_data(state)
                
                # 3. 检查缓存（第一阶段：同步执行模式）
                if self.enable_cache and self.cache_strategy and self.execution_mode == "sync":
                    cache_key = self._generate_cache_key(input_data, state)
                    cached_result = await self.cache_strategy.get(cache_key)
                    if cached_result:
                        logger.info(f"AgentNode '{self.name}' cache hit, returning cached result")
                        return self._build_cached_response(cached_result, state)
                
                # 4. 加载持久化上下文
                context_manager = self._get_context_manager()
                persisted_context = None
                if self.preserve_conversation:
                    persisted_context = context_manager.load_context(
                        conversation_id=session_id,
                        agent_id=self.agent_id,
                        node_id=self.node_id
                    )
                    if persisted_context:
                        logger.debug(
                            f"AgentNode '{self.name}' loaded persisted context: "
                            f"{len(persisted_context.messages)} messages"
                        )
                
                # 5. 构建执行上下文（合并持久化和当前状态）
                execution_context = await self._build_execution_context(state, persisted_context)
                
                # 6. 创建执行请求
                execution_request = ExecuteAgentRequest(
                    agent_id=self.agent_id,
                    input_data=input_data,
                    context=execution_context,
                    stream=self.enable_streaming
                )
                
                # 7. 获取用户ID（从状态或配置中）
                user_id = state.get("user_id") or self.config.get("user_id") or "system"
                
                # 8. 调用AgentService执行智能体（第一阶段：同步执行）
                agent_service = self._get_agent_service()
                
                # 计算剩余超时时间
                remaining_timeout = self.timeout - elapsed_time
                if remaining_timeout <= 0:
                    raise TimeoutError("No time remaining for execution")
                
                try:
                    # 第一阶段：使用同步执行（execute_agent已经是同步的）
                    execution_result = await asyncio.wait_for(
                        agent_service.execute_agent(
                            agent_id=self.agent_id,
                            request=execution_request,
                            user_id=user_id
                        ),
                        timeout=remaining_timeout
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Agent execution timeout after {remaining_timeout:.2f}s")
                
                # 9. 确保上下文已保存（AgentService 已经保存，这里确保状态同步）
                if execution_result.context and self.preserve_conversation:
                    # 确保上下文已持久化（AgentService 应该已经保存，这里做双重保险）
                    context_manager.save_context(execution_result.context)
                    logger.debug(f"AgentNode '{self.name}' context persisted")
                
                # 10. 处理执行结果
                updated_state = await self._process_execution_result(execution_result, state)
                
                # 11. 更新状态中的会话ID和对话历史
                updated_state['session_id'] = session_id
                updated_state['conversation_id'] = execution_result.context.conversation_id if execution_result.context else session_id
                if execution_result.context and execution_result.context.messages:
                    # 保持内存中的最新对话历史（用于工作流状态同步）
                    updated_state['conversation_history'] = [
                        {
                            "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                            "content": msg.content,
                            "tool_calls": msg.tool_calls or [],
                            "metadata": msg.metadata or {},
                            "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp)
                        }
                        for msg in execution_result.context.messages
                    ]
                
                # 12. 缓存结果（第一阶段：同步执行模式）
                if self.enable_cache and self.cache_strategy and self.execution_mode == "sync":
                    cache_key = self._generate_cache_key(input_data, state)
                    cache_data = {
                        "output_data": execution_result.output_data.dict() if execution_result.output_data else None,
                        "execution_id": execution_result.execution_id,
                        "success": execution_result.success
                    }
                    await self.cache_strategy.set(cache_key, cache_data, ttl=self.cache_ttl)
                    logger.debug(f"AgentNode '{self.name}' result cached: {cache_key}")
                
                # 13. 关闭数据库会话
                self._close_db_session()
                
                logger.info(
                    f"AgentNode '{self.name}' (agent_id: {self.agent_id}) "
                    f"executed successfully in {time.time() - start_time:.2f}s"
                )
                
                return updated_state
                
            except TimeoutError as e:
                last_error = e
                last_error_code = AgentErrorCode.EXECUTION_TIMEOUT
                logger.warning(
                    f"AgentNode '{self.name}' execution timeout: {str(e)}"
                )
                
                # 超时错误：检查是否启用降级
                if self.enable_fallback and retry_count >= self.retry_count:
                    logger.info(f"Applying fallback for timeout error in AgentNode '{self.name}'")
                    self._close_db_session()
                    return await self._apply_fallback(state, AgentErrorCode.EXECUTION_TIMEOUT)
                
                # 超时错误通常不重试（除非配置了重试）
                if retry_count < self.retry_count:
                    retry_count += 1
                    delay = min(
                        self.retry_delay * (self.retry_backoff_multiplier ** (retry_count - 1)),
                        self.max_retry_delay
                    )
                    logger.info(f"Retrying after {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    break
                    
            except Exception as e:
                last_error = e
                # 尝试识别错误代码
                last_error_code = self._identify_error_code(e)
                retry_count += 1
                
                # 检查错误是否可重试
                error_category = get_error_category(last_error_code)
                is_retryable = (
                    error_category in [AgentErrorCategory.TEMPORARY, AgentErrorCategory.NETWORK] and
                    retry_count <= self.retry_count
                )
                
                if is_retryable:
                    # 计算重试延迟（指数退避）
                    delay = min(
                        self.retry_delay * (self.retry_backoff_multiplier ** (retry_count - 1)),
                        self.max_retry_delay
                    )
                    logger.warning(
                        f"AgentNode '{self.name}' execution failed (attempt {retry_count}/{self.retry_count}): "
                        f"{str(e)}. Retrying after {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # 不可重试的错误或重试次数用完
                    if retry_count > self.retry_count:
                        logger.error(
                            f"AgentNode '{self.name}' execution failed after {self.retry_count} retries: {str(e)}",
                            exc_info=True
                        )
                    break
        
        # 所有重试都失败，尝试降级或返回错误
        self._close_db_session()
        
        # 如果启用降级，尝试应用降级策略
        if self.enable_fallback and last_error_code:
            fallback_result = await self._apply_fallback(state, last_error_code)
            if fallback_result:
                return fallback_result
        
        # 返回错误状态
        return await self._handle_execution_error(last_error, state, last_error_code)
    
    async def _build_input_data(self, state: Dict[str, Any]) -> AgentNodeInput:
        """
        构建智能体输入数据（应用输入映射）
        
        Args:
            state: 工作流状态
            
        Returns:
            AgentNodeInput对象
        """
        # 如果没有输入映射，使用默认映射
        if not self.input_mapping:
            content = state.get("input", state.get("message", ""))
            if not content:
                # 尝试从状态中提取文本内容
                content = str(state.get("data", {}).get("content", ""))
        else:
            # 应用输入映射
            content = self._apply_input_mapping(state)
        
        return AgentNodeInput(
            content=content or "",
            context=state.get("context", {}),
            variables=state.get("variables", {}),
            conversation_id=state.get("conversation_id"),
            user_id=state.get("user_id"),
            metadata={
                "workflow_id": state.get("workflow_id"),
                "execution_id": state.get("execution_id"),
                "node_id": self.node_id,
                "node_name": self.name
            }
        )
    
    def _apply_input_mapping(self, state: Dict[str, Any]) -> str:
        """
        应用输入映射规则（支持状态变量引用，与ToolNode一致）
        
        Args:
            state: 工作流状态
            
        Returns:
            映射后的输入内容
        """
        if not self.input_mapping:
            # 如果没有映射，尝试从常见字段获取
            for key in ["input", "message", "content", "data.content"]:
                value = self.get_state_value(state, key, "")
                if value:
                    return str(value)
            return ""
        
        # 支持简单的字段映射
        # 例如: {"content": "data.message"} 表示从 state["data"]["message"] 获取
        mapped_content = ""
        
        for target_field, source_path in self.input_mapping.items():
            if target_field == "content":
                # 从状态中获取值（支持嵌套键和状态变量引用）
                value = self.get_state_value(state, source_path, "")
                if value:
                    # 如果值是字符串，尝试解析模板变量
                    if isinstance(value, str):
                        mapped_content = self.resolve_template(value, state)
                    else:
                        mapped_content = str(value)
                    break
        
        return mapped_content or state.get("input", "")
    
    def _generate_cache_key(self, input_data: AgentNodeInput, state: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            input_data: 输入数据
            state: 工作流状态
            
        Returns:
            缓存键
        """
        # 构建上下文哈希（用于区分不同上下文）
        context_hash = None
        if self.preserve_conversation:
            conversation_id = state.get("conversation_id")
            if conversation_id:
                context_hash = conversation_id
        
        return generate_cache_key(
            agent_id=self.agent_id,
            input_data=input_data.dict(),
            context_hash=context_hash
        )
    
    def _build_cached_response(self, cached_result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建缓存响应
        
        Args:
            cached_result: 缓存的结果
            state: 当前工作流状态
            
        Returns:
            更新后的状态
        """
        updated_state = state.copy()
        
        # 从缓存中恢复输出数据
        if cached_result.get("output_data"):
            output_data_dict = cached_result["output_data"]
            output_key = f"{self.name}_output"
            updated_state[output_key] = output_data_dict
            
            # 也添加到根级别
            updated_state[f"{self.name}_result"] = output_data_dict.get("content", "")
            updated_state[f"{self.name}_success"] = cached_result.get("success", True)
            updated_state["output"] = output_data_dict.get("content", "")
            updated_state["message"] = output_data_dict.get("content", "")
            
            # 标记为缓存结果
            updated_state[f"{self.name}_cached"] = True
            updated_state[f"{self.name}_execution_id"] = cached_result.get("execution_id", "")
        
        logger.info(f"AgentNode '{self.name}' returning cached result")
        return updated_state
    
    async def _build_execution_context(
        self,
        state: Dict[str, Any],
        persisted_context: Optional[AgentContext] = None
    ) -> AgentContext:
        """
        构建智能体执行上下文（合并持久化和当前状态）
        
        Args:
            state: 工作流状态
            persisted_context: 持久化的上下文（可选）
            
        Returns:
            AgentContext对象
        """
        # 获取或创建对话ID
        conversation_id = state.get("conversation_id") or state.get("execution_id") or state.get("session_id") or str(self.node_id)
        
        # 如果有持久化上下文，使用它作为基础
        if persisted_context:
            context = persisted_context
            # 更新对话ID（确保一致性）
            context.conversation_id = conversation_id
            context.agent_id = self.agent_id
            context.node_id = self.node_id
        else:
            # 构建新的上下文
            messages = []
            if self.preserve_conversation:
                conversation_history = state.get("conversation_history", [])
                for msg in conversation_history[-self.context_window_size:]:
                    if isinstance(msg, dict):
                        messages.append(ConversationMessage(
                            role=ConversationRole(msg.get("role", "user")),
                            content=msg.get("content", ""),
                            tool_calls=msg.get("tool_calls", []),
                            metadata=msg.get("metadata", {})
                        ))
            
            context = AgentContext(
                conversation_id=conversation_id,
                agent_id=self.agent_id,
                node_id=self.node_id,
                messages=messages,
                current_state=AgentExecutionState.PENDING,
                variables=state.get("variables", {}),
                shared_memory=state.get("shared_memory", {})
            )
        
        # 合并当前状态的变量和共享内存（当前状态优先）
        current_variables = state.get("variables", {})
        current_shared_memory = state.get("shared_memory", {})
        
        if current_variables:
            context.variables = {**context.variables, **current_variables}
        if current_shared_memory:
            context.shared_memory = {**context.shared_memory, **current_shared_memory}
        
        # 限制消息数量（避免上下文窗口过大）
        if len(context.messages) > self.context_window_size:
            context.messages = context.messages[-self.context_window_size:]
        
        return context
    
    def _merge_contexts(
        self,
        persisted_context: Optional[AgentContext],
        current_context: AgentContext
    ) -> AgentContext:
        """
        合并持久化上下文和当前上下文
        
        Args:
            persisted_context: 持久化的上下文
            current_context: 当前上下文
            
        Returns:
            合并后的上下文
        """
        if not persisted_context:
            return current_context
        
        # 合并消息（持久化的消息 + 当前消息）
        merged_messages = persisted_context.messages.copy()
        
        # 添加当前上下文中的新消息（避免重复）
        current_message_ids = {msg.id for msg in merged_messages if hasattr(msg, 'id')}
        for msg in current_context.messages:
            if not hasattr(msg, 'id') or msg.id not in current_message_ids:
                merged_messages.append(msg)
        
        # 限制消息数量
        if len(merged_messages) > self.context_window_size:
            merged_messages = merged_messages[-self.context_window_size:]
        
        # 合并变量和共享内存（当前上下文优先）
        merged_variables = {**persisted_context.variables, **current_context.variables}
        merged_shared_memory = {**persisted_context.shared_memory, **current_context.shared_memory}
        
        # 创建合并后的上下文
        merged_context = AgentContext(
            conversation_id=current_context.conversation_id or persisted_context.conversation_id,
            agent_id=current_context.agent_id or persisted_context.agent_id,
            node_id=current_context.node_id or persisted_context.node_id,
            messages=merged_messages,
            current_state=current_context.current_state,
            variables=merged_variables,
            shared_memory=merged_shared_memory,
            execution_count=persisted_context.execution_count + current_context.execution_count,
            total_tokens=persisted_context.total_tokens + current_context.total_tokens,
            total_execution_time=persisted_context.total_execution_time + current_context.total_execution_time,
            created_at=persisted_context.created_at,
            updated_at=datetime.now(),
            expires_at=current_context.expires_at or persisted_context.expires_at
        )
        
        return merged_context
    
    async def _process_execution_result(
        self,
        result: ExecuteAgentResponse,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理智能体执行结果（保持与现有节点接口一致性）
        
        Args:
            result: 执行结果
            state: 当前工作流状态
            
        Returns:
            更新后的状态
        """
        updated_state = state.copy()
        
        # 应用输出映射
        if result.output_data:
            if self.output_mapping:
                # 应用输出映射规则
                for target_field, source_field in self.output_mapping.items():
                    source_value = getattr(result.output_data, source_field, None)
                    if source_value is not None:
                        self.set_state_value(updated_state, target_field, source_value)
            else:
                # 默认映射：保持与ToolNode和LLMNode一致的输出格式
                output_key = f"{self.name}_output"
                updated_state[output_key] = {
                    "content": result.output_data.content,
                    "metadata": result.output_data.metadata,
                    "tool_calls": result.output_data.tool_calls,
                    "reasoning_steps": result.output_data.reasoning_steps,
                    "confidence_score": result.output_data.confidence_score,
                    "execution_time": result.output_data.execution_time,
                    "tokens_used": result.output_data.tokens_used,
                    "agent_id": self.agent_id,
                    "node_name": self.name,
                    "execution_id": result.execution_id
                }
                
                # 也添加到根级别（与ToolNode/LLMNode保持一致）
                updated_state[f"{self.name}_result"] = result.output_data.content
                updated_state[f"{self.name}_success"] = True
                
                # 将内容直接添加到output和message字段（便于后续节点使用）
                updated_state["output"] = result.output_data.content
                updated_state["message"] = result.output_data.content
        
        # 更新对话历史（状态同步）
        if result.context and self.preserve_conversation:
            conversation_history = updated_state.get("conversation_history", [])
            
            # 添加用户输入
            if result.execution_record.input_data:
                input_data = result.execution_record.input_data
                if isinstance(input_data, dict):
                    conversation_history.append({
                        "role": "user",
                        "content": input_data.get("content", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 添加助手响应
            if result.output_data:
                conversation_history.append({
                    "role": "assistant",
                    "content": result.output_data.content,
                    "tool_calls": result.output_data.tool_calls,
                    "metadata": result.output_data.metadata,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 限制上下文窗口大小
            if len(conversation_history) > self.context_window_size:
                conversation_history = conversation_history[-self.context_window_size:]
            
            updated_state["conversation_history"] = conversation_history
        
        # 更新上下文（状态同步）
        if result.context:
            updated_state["agent_context"] = result.context.dict()
            updated_state["conversation_id"] = result.context.conversation_id
            
            # 同步共享内存
            if result.context.shared_memory:
                updated_state["shared_memory"] = result.context.shared_memory
        
        # 添加执行元数据（与现有节点格式一致）
        updated_state[f"{self.name}_execution_id"] = result.execution_id
        updated_state[f"{self.name}_success"] = result.success
        updated_state[f"{self.name}_execution_time"] = (
            result.output_data.execution_time if result.output_data else 0.0
        )
        
        return updated_state
    
    def _identify_error_code(self, error: Exception) -> AgentErrorCode:
        """
        识别错误代码
        
        Args:
            error: 异常对象
            
        Returns:
            错误代码
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        if isinstance(error, TimeoutError) or "timeout" in error_msg:
            return AgentErrorCode.EXECUTION_TIMEOUT
        elif "not found" in error_msg or "不存在" in error_msg:
            return AgentErrorCode.AGENT_NOT_FOUND
        elif "permission" in error_msg or "权限" in error_msg:
            return AgentErrorCode.INSUFFICIENT_PERMISSIONS
        elif "database" in error_msg or "数据库" in error_msg:
            return AgentErrorCode.DATABASE_ERROR
        elif "network" in error_msg or "网络" in error_msg or "connection" in error_msg:
            return AgentErrorCode.NETWORK_ERROR
        elif "model" in error_msg and ("unavailable" in error_msg or "overloaded" in error_msg):
            return AgentErrorCode.AI_MODEL_UNAVAILABLE
        else:
            return AgentErrorCode.EXECUTION_FAILED
    
    async def _apply_fallback(
        self,
        state: Dict[str, Any],
        error_code: AgentErrorCode
    ) -> Optional[Dict[str, Any]]:
        """
        应用降级策略
        
        Args:
            state: 当前工作流状态
            error_code: 错误代码
            
        Returns:
            降级后的状态，如果无法降级则返回None
        """
        fallback_policy = ERROR_FALLBACK_POLICIES.get(error_code)
        
        if not fallback_policy or not fallback_policy.enabled:
            return None
        
        logger.info(
            f"Applying fallback for error {error_code.value} in AgentNode '{self.name}'"
        )
        
        # 创建降级响应
        fallback_state = state.copy()
        fallback_state[f"{self.name}_output"] = {
            "content": fallback_policy.fallback_response,
            "metadata": {
                "fallback": True,
                "error_code": error_code.value,
                "original_error": "智能体执行失败，已应用降级策略"
            },
            "node_name": self.name,
            "agent_id": self.agent_id
        }
        fallback_state[f"{self.name}_result"] = fallback_policy.fallback_response
        fallback_state[f"{self.name}_success"] = False
        fallback_state[f"{self.name}_fallback"] = True
        
        # 将降级响应添加到output字段
        fallback_state["output"] = fallback_policy.fallback_response
        fallback_state["message"] = fallback_policy.fallback_response
        
        return fallback_state
    
    async def _handle_execution_error(
        self,
        error: Exception,
        state: Dict[str, Any],
        error_code: Optional[AgentErrorCode] = None
    ) -> Dict[str, Any]:
        """
        处理执行错误（保持与现有节点错误处理一致）
        
        Args:
            error: 异常对象
            state: 当前工作流状态
            error_code: 错误代码（可选）
            
        Returns:
            包含错误信息的状态
        """
        if error_code is None:
            error_code = self._identify_error_code(error)
        
        error_state = state.copy()
        
        # 与BaseNode的错误处理格式保持一致
        error_state["error"] = str(error)
        error_state["error_type"] = type(error).__name__
        error_state["error_node"] = self.name
        error_state["error_time"] = datetime.now().isoformat()
        error_state["agent_execution_failed"] = True
        
        # 记录错误详情（与现有节点格式一致）
        error_state[f"{self.name}_error"] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_code": error_code.value,
            "agent_id": self.agent_id,
            "node_id": self.node_id
        }
        
        # 确保输出字段存在（即使失败）
        error_state[f"{self.name}_output"] = {
            "content": "",
            "error": str(error),
            "success": False,
            "node_name": self.name,
            "agent_id": self.agent_id
        }
        error_state[f"{self.name}_success"] = False
        
        logger.error(
            f"AgentNode '{self.name}' (agent_id: {self.agent_id}) execution failed: {str(error)}",
            exc_info=True
        )
        
        return error_state
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        验证输入状态（重写基类方法）
        
        Args:
            state: 工作流状态
            
        Returns:
            是否通过验证
        """
        # 调用基类验证
        if not super().validate_input(state):
            return False
        
        # 检查智能体ID是否配置
        if not self.agent_id:
            logger.error(f"AgentNode '{self.name}' missing agent_id in config")
            return False
        
        return True
    
    def __del__(self):
        """析构函数：确保数据库会话被关闭"""
        self._close_db_session()


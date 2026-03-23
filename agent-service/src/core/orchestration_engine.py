"""
智能编排引擎
在agent-service内部统一编排处理入口
"""
import logging
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime

from .conversation_agent import conversation_agent, IntentAnalysis, TaskType
from .task_classifier import task_classifier, ExecutionStrategy, RoutingDecision
from .service_clients import service_clients
from .llm_integration import deepseek_llm
from .prompt_engine.prompt_engine import PromptEngine
from .prompt_templates.base_templates import TaskCategory
from ..models.prompt_models import PromptContext

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """智能编排引擎 - 在agent-service内部"""
    
    def __init__(self):
        self.conversation_agent = conversation_agent
        self.task_classifier = task_classifier
        self.service_clients = service_clients
        # ✅ 初始化提示词引擎
        try:
            self.prompt_engine = PromptEngine()
            logger.info("Prompt engine initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize prompt engine: {e}, will use basic prompts")
            self.prompt_engine = None
    
    async def orchestrate_request(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        统一编排处理入口
        
        Args:
            user_input: 用户输入
            context: 上下文信息（包含user_id, session_id, history, available_agents等）
            
        Returns:
            编排结果
        """
        execution_path = []
        used_services = []
        overall_start_time = datetime.now()
        execution_id = None
        
        try:
            # 创建执行记录（用于元数据收集）
            from .state_manager import state_manager
            execution_id = await state_manager.create_execution(
                task=user_input,
                context=context,
                metadata={
                    "user_input": user_input[:500],  # 限制长度
                    "user_id": context.get('user_id'),
                    "session_id": context.get('session_id')
                }
            )
            
            # 1. 任务理解
            history = context.get('history', [])
            user_context = {k: v for k, v in context.items() if k not in ['history', 'available_agents']}
            
            # ✅ 构建提示词上下文
            prompt_context = None
            if self.prompt_engine:
                try:
                    prompt_context = PromptContext(
                        user_id=context.get('user_id'),
                        session_id=context.get('session_id'),
                        conversation_history=history,
                        user_profile=context.get('user_profile'),
                        task_context=context.get('task_context'),
                        available_tools=context.get('available_tools', [])
                    )
                except Exception as e:
                    logger.warning(f"Failed to create prompt context: {e}")
            
            intent_analysis = await self.conversation_agent.understand_conversation(
                user_input, 
                history, 
                user_context,
                prompt_engine=self.prompt_engine,  # ✅ 传入提示词引擎
                prompt_context=prompt_context  # ✅ 传入提示词上下文
            )
            
            execution_path.append({
                "step": "intent_analysis",
                "result": {
                    "task_type": intent_analysis.task_type.value,
                    "confidence": intent_analysis.confidence
                }
            })
            
            logger.info(
                f"Intent analysis: type={intent_analysis.task_type.value}, "
                f"confidence={intent_analysis.confidence:.2f}"
            )

            # 2. 任务分类和路由决策
            available_agents = context.get('available_agents', [])

            # 检查是否是SAP相关查询，如果是，优先查找SAP查询智能体
            # 仅当意图识别为工具执行时才进入SAP路由，避免普通闲聊被误路由
            sap_keywords = ["sap", "销售订单", "采购订单", "物料", "客户", "供应商", "erp"]
            lower_input = user_input.lower()
            has_sap_keyword = any(kw in lower_input for kw in ["sap", "erp"]) or any(
                kw in user_input for kw in ["销售订单", "采购订单", "物料", "客户", "供应商"]
            )
            if "sap_query" in intent_analysis.required_tools and not has_sap_keyword:
                intent_analysis.task_type = TaskType.SIMPLE_QUERY
                intent_analysis.required_tools = []
                intent_analysis.required_services = []
                intent_analysis.reasoning = f"{intent_analysis.reasoning} | override: non-SAP query"
            is_sap_query = (
                intent_analysis.task_type == TaskType.TOOL_EXECUTION
                and has_sap_keyword
            )
            
            sap_agent = None
            if is_sap_query and available_agents:
                # 查找SAP查询智能体
                for agent_info in available_agents:
                    agent_name = agent_info.get("name", "")
                    agent_id = agent_info.get("id", "")
                    if "SAP" in agent_name or "sap" in agent_name.lower():
                        sap_agent = {"id": agent_id, "name": agent_name}
                        logger.info(f"Found SAP agent: {agent_name} ({agent_id})")
                        break
            
            # 如果找到SAP智能体，使用智能体执行
            if sap_agent:
                from .agent_manager import agent_manager
                from ..models.agent_models import AgentStatus
                
                target_agent = await agent_manager.get_agent(sap_agent["id"])
                if target_agent and target_agent.status == AgentStatus.ACTIVE:
                    logger.info(f"Routing SAP query to agent: {target_agent.name} ({sap_agent['id']})")
                    
                    # 使用智能体执行
                    agent_result = await agent_manager.execute_agent(
                        sap_agent["id"],
                        user_input,
                        {**context, "preferred_tools": ["sap_query"]}
                    )
                    
                    execution_path.append({
                        "step": "agent_execution",
                        "result": {
                            "agent_id": sap_agent["id"],
                            "agent_name": target_agent.name,
                            "output": agent_result.get("output", "")
                        }
                    })
                    
                    overall_execution_time = (datetime.now() - overall_start_time).total_seconds()
                    
                    return {
                        "success": agent_result.get("success", False),
                        "final_response": agent_result.get("output", ""),
                        "execution_path": execution_path,
                        "used_services": ["agent-service", "mcp-gateway"],
                        "intent_analysis": {
                            "task_type": intent_analysis.task_type.value,
                            "confidence": intent_analysis.confidence,
                            "reasoning": intent_analysis.reasoning,
                        },
                        "orchestration_metadata": {
                            "execution_timestamp": datetime.now().isoformat(),
                            "execution_time_seconds": overall_execution_time,
                            "user_input_preview": user_input[:100] + ("..." if len(user_input) > 100 else ""),
                            "session_id": context.get('session_id'),
                            "user_id": context.get('user_id'),
                            "agent_used": sap_agent["id"]
                        },
                        "raw_result": agent_result
                    }
            
            routing_decision = await self.task_classifier.classify_and_route(
                intent_analysis, available_agents
            )
            
            # 使用元数据增强路由决策（阶段2）
            try:
                from .metadata_driven_executor import metadata_driven_executor
                routing_decision = await metadata_driven_executor.enhance_with_metadata(
                    user_input=user_input,
                    intent_analysis=intent_analysis,
                    routing_decision=routing_decision,
                    context=context
                )
                logger.debug("Routing decision enhanced with metadata")
            except Exception as e:
                logger.debug(f"Failed to enhance routing decision with metadata: {e}, using original decision")
            
            execution_path.append({
                "step": "routing_decision",
                "result": {
                    "strategy": routing_decision.strategy.value,
                    "target_service": routing_decision.target_service,
                    "reasoning": routing_decision.reasoning
                }
            })
            
            # 记录完整的路由决策日志
            logger.info(
                f"Orchestration Decision - "
                f"Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''} | "
                f"Intent: {intent_analysis.task_type.value} | "
                f"Confidence: {intent_analysis.confidence:.2f} | "
                f"Strategy: {routing_decision.strategy.value} | "
                f"Target: {routing_decision.target_service} | "
                f"Reasoning: {routing_decision.reasoning}"
            )
            
            # 3. 执行协调（使用策略映射表）
            execution_methods = {
                ExecutionStrategy.DIRECT_LLM: self._handle_direct_llm,
                ExecutionStrategy.TOOL_CALL: lambda ui, ctx, rd, pc: self._handle_tool_execution(ui, ctx, rd, intent_analysis, pc),
                ExecutionStrategy.WORKFLOW_EXECUTION: self._handle_workflow,
                ExecutionStrategy.ORCHESTRATION: self._handle_complex_orchestration,
                ExecutionStrategy.SERVICE_DELEGATION: self._handle_service_delegation,
            }
            
            handler = execution_methods.get(
                routing_decision.strategy,
                self._handle_direct_llm  # 默认降级处理
            )
            
            # 记录执行开始
            execution_start_time = datetime.now()
            logger.info(f"Executing strategy: {routing_decision.strategy.value}")
            
            # ✅ 传递提示词上下文给handler
            result = await handler(user_input, context, routing_decision, prompt_context)
            
            # 记录执行完成
            execution_time = (datetime.now() - execution_start_time).total_seconds()
            logger.info(f"Execution completed: strategy={routing_decision.strategy.value}, time={execution_time:.2f}s")
            
            # 收集使用的服务
            if routing_decision.strategy == ExecutionStrategy.DIRECT_LLM:
                used_services.append("llm")
            elif routing_decision.strategy == ExecutionStrategy.TOOL_CALL:
                used_services.append("mcp-gateway")
            elif routing_decision.strategy == ExecutionStrategy.WORKFLOW_EXECUTION:
                used_services.append("workflow-engine")
            elif routing_decision.strategy == ExecutionStrategy.ORCHESTRATION:
                used_services.extend(result.get("used_services", []))
            elif routing_decision.strategy == ExecutionStrategy.SERVICE_DELEGATION:
                if routing_decision.target_service:
                    used_services.append(routing_decision.target_service)
            
            # 构建最终结果（包含完整的编排元数据）
            overall_execution_time = (datetime.now() - overall_start_time).total_seconds()
            
            # 获取最终响应，优先使用output，然后是response，最后是result
            final_response = result.get("output") or result.get("response") or result.get("result") or ""
            
            # 如果final_response是None或空字符串，尝试从raw_result获取
            if not final_response:
                raw_result = result.get("raw_result", {})
                if isinstance(raw_result, dict):
                    final_response = raw_result.get("output") or raw_result.get("response") or raw_result.get("result") or ""
            
            # 如果还是没有，使用默认消息
            if not final_response:
                final_response = "处理完成，但未返回具体内容。"
            
            final_result = {
                "success": result.get("success", False),
                "final_response": final_response,
                "execution_path": execution_path,
                "used_services": list(set(used_services)),  # 去重
                "intent_analysis": {
                    "task_type": intent_analysis.task_type.value,
                    "confidence": intent_analysis.confidence,
                    "reasoning": intent_analysis.reasoning,
                    "extracted_context": intent_analysis.extracted_context,
                    "required_tools": intent_analysis.required_tools,
                    "required_services": intent_analysis.required_services
                },
                "routing_decision": {
                    "strategy": routing_decision.strategy.value,
                    "target_service": routing_decision.target_service,
                    "target_agent_id": routing_decision.target_agent_id,
                    "required_tools": routing_decision.required_tools,
                    "reasoning": routing_decision.reasoning,
                    "execution_params": routing_decision.execution_params
                },
                "orchestration_metadata": {
                    "execution_timestamp": datetime.now().isoformat(),
                    "execution_time_seconds": overall_execution_time,
                    "strategy_execution_time_seconds": execution_time,
                    "user_input_preview": user_input[:100] + ("..." if len(user_input) > 100 else ""),
                    "session_id": context.get('session_id'),
                    "user_id": context.get('user_id')
                },
                "raw_result": result
            }
            
            # 更新执行记录，保存完整的元数据
            if execution_id:
                try:
                    from .state_manager import ExecutionState
                    await state_manager.update_execution_state(
                        execution_id,
                        ExecutionState.COMPLETED if final_result["success"] else ExecutionState.FAILED,
                        result=final_result,
                        error=None if final_result["success"] else final_result.get("error")
                    )
                    # 添加执行步骤
                    await state_manager.add_execution_step(execution_id, "intent_analysis", {
                        "task_type": intent_analysis.task_type.value,
                        "confidence": intent_analysis.confidence
                    })
                    await state_manager.add_execution_step(execution_id, "routing_decision", {
                        "strategy": routing_decision.strategy.value,
                        "target_service": routing_decision.target_service
                    })
                except Exception as e:
                    logger.warning(f"Failed to update execution record: {e}")
            
            # 异步保存对话元数据到metadata-service（不阻塞响应）
            try:
                from ..services.metadata_client import metadata_client
                # 在后台任务中保存，不阻塞主流程
                import asyncio
                asyncio.create_task(
                    metadata_client.save_conversation_metadata(
                        user_input=user_input,
                        ai_response=final_response,
                        intent_analysis=final_result.get("intent_analysis", {}),
                        routing_decision=final_result.get("routing_decision", {}),
                        execution_metadata={
                            **final_result.get("orchestration_metadata", {}),
                            "success": final_result.get("success", False),
                            "execution_id": execution_id
                        },
                        session_id=context.get('session_id'),
                        user_id=context.get('user_id')
                    )
                )
                logger.info(f"Queued conversation metadata save for execution {execution_id}")
            except Exception as e:
                logger.warning(f"Failed to queue conversation metadata save: {e}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            
            # 更新执行记录为失败状态
            if execution_id:
                try:
                    from .state_manager import ExecutionState
                    await state_manager.update_execution_state(
                        execution_id,
                        ExecutionState.FAILED,
                        result=None,
                        error=str(e)
                    )
                except Exception as update_error:
                    logger.warning(f"Failed to update execution record on error: {update_error}")
            
            return {
                "success": False,
                "final_response": f"处理失败: {str(e)}",
                "execution_path": execution_path,
                "used_services": used_services,
                "error": str(e)
            }
    
    async def _handle_direct_llm(
        self,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        prompt_context: Optional[PromptContext] = None
    ) -> Dict[str, Any]:
        """处理直接LLM调用 - 支持优化提示词"""
        try:
            # ✅ 使用优化提示词（如果可用）
            if self.prompt_engine and prompt_context:
                try:
                    optimized_prompt = await self.prompt_engine.get_optimized_prompt(
                        TaskCategory.DIRECT_CHAT,
                        user_input,
                        prompt_context
                    )
                    
                    # 检查LLM是否已初始化
                    if not deepseek_llm.llm:
                        logger.error("LLM not initialized, attempting to initialize...")
                        await deepseek_llm._load_config_async()
                        if not deepseek_llm.llm:
                            error_msg = "LLM服务未初始化。请检查OPENAI_API_KEY和LLM_BASE_URL配置。"
                            logger.error(error_msg)
                            return {
                                "success": False,
                                "output": error_msg,
                                "response": error_msg,
                                "error": error_msg,
                                "strategy": "direct_llm"
                            }
                    
                    # 使用优化提示词调用LLM
                    response = await deepseek_llm.chat(
                        messages=optimized_prompt.messages,
                        temperature=optimized_prompt.temperature,
                        max_tokens=optimized_prompt.max_tokens
                    )
                    
                    # 确保response不是None或空
                    if not response:
                        logger.warning("LLM returned empty response")
                        response = "抱歉，我暂时无法生成回复。请稍后再试。"
                    
                    logger.info(f"Optimized LLM response length: {len(response) if response else 0}, "
                               f"template: {optimized_prompt.template_name}")
                    
                    return {
                        "success": True,
                        "output": response,
                        "response": response,
                        "strategy": "direct_llm",
                        "prompt_template": optimized_prompt.template_name,
                        "execution_method": "optimized_direct_llm"
                    }
                except Exception as e:
                    logger.warning(f"Optimized prompt failed, falling back to basic: {e}")
            
            # 降级到基础方法
            messages = []
            
            # 添加对话历史
            history = context.get('history', [])
            if history:
                messages.extend(history[-20:])  # 增加到20条，保持更长的对话上下文
            
            # 添加当前消息
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # 检查LLM是否已初始化
            if not deepseek_llm.llm:
                logger.error("LLM not initialized, attempting to initialize...")
                await deepseek_llm._load_config_async()
                if not deepseek_llm.llm:
                    error_msg = "LLM服务未初始化。请检查OPENAI_API_KEY和LLM_BASE_URL配置。"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "output": error_msg,
                        "response": error_msg,
                        "error": error_msg,
                        "strategy": "direct_llm"
                    }
            
            # 调用LLM
            response = await deepseek_llm.chat(
                messages=messages,
                system_prompt="你是一个有用的AI助手。"
            )
            
            # 确保response不是None或空
            if not response:
                logger.warning("LLM returned empty response")
                response = "抱歉，我暂时无法生成回复。请稍后再试。"
            
            logger.info(f"Direct LLM response length: {len(response) if response else 0}")
            
            return {
                "success": True,
                "output": response,
                "response": response,
                "strategy": "direct_llm"
            }
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}", exc_info=True)
            error_msg = f"LLM调用失败: {str(e)}"
            return {
                "success": False,
                "output": error_msg,
                "response": error_msg,
                "error": str(e),
                "strategy": "direct_llm"
            }
    
    async def _handle_tool_execution(
        self,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        intent_analysis: Optional[IntentAnalysis] = None,
        prompt_context: Optional[PromptContext] = None
    ) -> Dict[str, Any]:
        """处理工具执行"""
        try:
            # 获取工具ID - 优先使用元数据识别结果
            tool_id = None
            
            # 1. 优先使用RoutingDecision中的required_tools（来自元数据识别）
            if decision.required_tools:
                tool_id = decision.required_tools[0]
                logger.info(f"Using tool from routing decision: {tool_id}")
            # 2. 如果没有，尝试从IntentAnalysis中获取
            elif intent_analysis and intent_analysis.required_tools:
                tool_id = intent_analysis.required_tools[0]
                logger.info(f"Using tool from intent analysis: {tool_id}")
            # 3. 如果还没有，尝试从execution_params中获取
            elif decision.execution_params.get("context", {}).get("required_tools"):
                tool_list = decision.execution_params["context"]["required_tools"]
                if isinstance(tool_list, list) and tool_list:
                    tool_id = tool_list[0]
                    logger.info(f"Using tool from execution params: {tool_id}")
            # 4. 如果还是没有，尝试通过MCP Gateway搜索工具（基于语义搜索）
            if not tool_id:
                try:
                    logger.info("No tool found in decision, searching via MCP Gateway...")
                    tools = await self.service_clients.mcp_gateway.search_tools(user_input)
                    if tools and len(tools) > 0:
                        # 检查返回格式：可能是列表或字典
                        if isinstance(tools, list):
                            tool_id = tools[0].get("name") or tools[0].get("id")
                        elif isinstance(tools, dict) and "tools" in tools:
                            tool_list = tools.get("tools", [])
                            if tool_list:
                                tool_id = tool_list[0].get("name") or tool_list[0].get("id")
                        if tool_id:
                            logger.info(f"Found tool via MCP Gateway search: {tool_id}")
                except Exception as e:
                    logger.warning(f"Tool search via MCP Gateway failed: {e}")
            
            # 5. 如果仍然没有找到工具，返回错误（不再使用硬编码的fallback）
            if not tool_id:
                logger.error(
                    f"No tool identified for request. "
                    f"Decision required_tools: {decision.required_tools}, "
                    f"Intent required_tools: {intent_analysis.required_tools if intent_analysis else None}, "
                    f"User input: {user_input[:100]}"
                )
                return {
                    "success": False,
                    "error": "未找到合适的工具来处理您的请求",
                    "output": "抱歉，我无法识别需要使用的工具。请确保您的请求描述清晰，或者联系管理员检查工具配置。"
                }
            
            # 提取参数
            # 优先从intent_analysis中获取参数（LLM提取的参数）
            parameters = {}
            if intent_analysis and intent_analysis.extracted_context:
                parameters = intent_analysis.extracted_context.get("parameters", {})
            
            # 如果没有，尝试从execution_params中获取
            if not parameters:
                parameters = decision.execution_params.get("context", {}).get("parameters", {})
            
            # 如果仍然没有参数，根据工具类型尝试从用户输入中提取
            if not parameters:
                # 对于邮件发送，尝试从用户输入中提取邮件参数
                if tool_id == "send_email" or "email" in tool_id.lower():
                    parameters = self._extract_email_parameters(user_input, intent_analysis)
                    logger.info(f"Extracted parameters for email: {parameters}")
                # 对于SAP查询，尝试提取表名和查询条件
                elif tool_id == "sap_query" or "sap" in tool_id.lower():
                    # 优先从意图分析中提取表名
                    extracted_params = intent_analysis.extracted_context.get("parameters", {})
                    table = extracted_params.get("table")
                    
                    # 如果没有表名，尝试从用户输入中推断
                    if not table:
                        user_lower = user_input.lower()
                        # 根据关键词推断表名
                        if "采购订单" in user_input or "purchase" in user_lower:
                            table = "I_PurchaseOrder"
                        elif "销售订单" in user_input or "sales" in user_lower:
                            table = "I_SalesOrder"
                        elif "物料" in user_input or "material" in user_lower:
                            table = "I_Material"
                        elif "客户" in user_input or "customer" in user_lower:
                            table = "I_Customer"
                        elif "供应商" in user_input or "vendor" in user_lower:
                            table = "I_Vendor"
                        else:
                            # 默认查询销售订单表
                            table = "I_SalesOrder"
                    
                    parameters = {
                        "table": table,
                        "query": user_input
                    }
                    logger.info(f"Extracted parameters for SAP query: {parameters}")
                else:
                    # 对于其他工具，尝试从用户输入中提取通用参数
                    logger.warning(f"No parameters extracted for tool {tool_id}, using empty dict")
            
            # 执行工具
            result = await self.service_clients.mcp_gateway.execute_tool(
                tool_id, parameters, context
            )
            
            # 处理工具执行结果
            raw_result = result.get("result") or result.get("output") or {}
            success = result.get("success", False)
            
            # 如果执行失败，提供友好的错误信息（根据实际使用的工具）
            if not success:
                error_msg = result.get("error", "工具执行失败")
                # 根据工具类型提供不同的错误信息
                if tool_id == "send_email" or "email" in tool_id.lower():
                    output = f"抱歉，发送邮件时遇到问题：{error_msg}\n\n请检查：\n1. 邮件配置是否正确\n2. 收件人邮箱地址是否有效\n3. 网络连接是否正常"
                elif tool_id == "sap_query" or "sap" in tool_id.lower():
                    output = f"抱歉，执行SAP查询时遇到问题：{error_msg}\n\n如果您想查询销售订单，请确保：\n1. SAP系统连接正常\n2. 您有相应的权限\n3. 查询条件正确"
                else:
                    output = f"抱歉，执行工具 '{tool_id}' 时遇到问题：{error_msg}"
            else:
                # 格式化工具执行结果为可读文本
                formatted_result = self._format_tool_result(raw_result, tool_id)
                
                # 检查用户是否要求分析（包含"分析"、"总结"、"评估"等关键词）
                analysis_keywords = ["分析", "总结", "评估", "解读", "说明", "解释", "insight", "analyze", "summary", "evaluate"]
                requires_analysis = any(keyword in user_input for keyword in analysis_keywords)
                
                if requires_analysis and deepseek_llm.llm:
                    # 使用LLM对结果进行分析
                    try:
                        logger.info("User requested analysis, generating LLM analysis...")
                        
                        # 先返回查询结果，让用户知道数据已获取
                        output = formatted_result + "\n\n---\n\n🔄 **正在使用AI分析数据，请稍候...**\n\n"
                        
                        # 智能截断：保留开头和结尾，确保关键信息不丢失
                        max_result_length = 8000  # 增加长度限制
                        if len(formatted_result) > max_result_length:
                            # 保留开头和结尾，中间省略
                            truncated_result = (
                                formatted_result[:max_result_length//2] + 
                                "\n\n... (数据已截断，显示关键部分) ...\n\n" + 
                                formatted_result[-max_result_length//2:]
                            )
                        else:
                            truncated_result = formatted_result
                        
                        analysis_prompt = f"""你是一个业务数据分析专家。请基于以下查询结果，提供深入的分析和洞察。

用户查询：{user_input}

查询结果：
{truncated_result}

请提供：
1. **数据概览**：总结数据的基本情况（记录数、主要字段等）
2. **关键发现**：识别数据中的主要趋势、模式或异常
3. **业务洞察**：从业务角度解读数据的意义
4. **建议**：基于分析结果提供可行的建议或行动项

请用中文回答，语言要专业但易懂，使用清晰的段落和要点。"""
                        
                        analysis = await deepseek_llm.chat(
                            messages=[{"role": "user", "content": analysis_prompt}],
                            system_prompt="你是一个专业的业务数据分析师，擅长从数据中提取洞察并提供有价值的建议。你的分析应该客观、深入、实用。",
                            temperature=0.7
                        )
                        
                        # 组合原始结果和分析（替换"正在分析"提示）
                        output = f"{formatted_result}\n\n---\n\n## 📊 数据分析\n\n{analysis}"
                        logger.info("LLM analysis completed successfully")
                    except Exception as e:
                        logger.error(f"Failed to generate LLM analysis: {e}", exc_info=True)
                        # 如果分析失败，仍然返回原始结果
                        output = formatted_result + "\n\n（注：数据分析功能暂时不可用，已返回原始查询结果）"
                else:
                    # 不需要分析，直接返回格式化结果
                    output = formatted_result
            
            return {
                "success": success,
                "output": output,
                "response": output,  # 添加response字段以兼容chat-service
                "tool_id": tool_id,
                "raw_result": result,
                "error": result.get("error") if not success else None
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            error_msg = f"工具执行失败: {str(e)}"
            return {
                "success": False,
                "error": str(e),
                "output": error_msg,
                "response": error_msg
            }
    
    async def _handle_workflow(
        self,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        prompt_context: Optional[PromptContext] = None
    ) -> Dict[str, Any]:
        """处理工作流执行"""
        try:
            # 从上下文或决策中获取工作流ID
            workflow_id = context.get("workflow_id") or decision.execution_params.get("workflow_id")
            
            if not workflow_id:
                return {
                    "success": False,
                    "error": "Workflow ID not specified"
                }
            
            # 准备输入数据
            input_data = context.get("input", {})
            
            # 执行工作流
            result = await self.service_clients.workflow_engine.execute_workflow(
                workflow_id, input_data, context
            )
            
            return {
                "success": result.get("success", False),
                "output": result.get("result") or result.get("output"),
                "workflow_id": workflow_id,
                "raw_result": result
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_complex_orchestration(
        self,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        prompt_context: Optional[PromptContext] = None
    ) -> Dict[str, Any]:
        """处理复杂编排任务"""
        try:
            # 使用DAG编排器进行任务分解
            # DAGClient.decompose_task接受(task: str, context: Optional[Dict])参数
            decomposition_result = await self.service_clients.dag_orchestrator.decompose_task(
                user_input,
                context
            )
            
            if not decomposition_result:
                return {
                    "success": False,
                    "error": "Task decomposition failed"
                }
            
            # DAG分解结果包含task_nodes结构
            task_nodes = decomposition_result.get("task_nodes", {})
            if not task_nodes:
                # 如果没有子任务，直接返回
                return {
                    "success": True,
                    "output": "任务已分解，但无需执行子任务",
                    "decomposition": decomposition_result
                }
            
            # 执行分解后的任务节点
            execution_results = []
            used_services = []
            
            # 按依赖顺序执行任务节点（简化版本：按entry_nodes开始）
            entry_nodes = decomposition_result.get("entry_nodes", [])
            processed_nodes = set()
            
            # 简单的拓扑排序执行（实际应该使用更复杂的DAG执行逻辑）
            nodes_to_process = list(entry_nodes)
            
            while nodes_to_process:
                node_id = nodes_to_process.pop(0)
                if node_id in processed_nodes:
                    continue
                
                node = task_nodes.get(node_id)
                if not node:
                    continue
                
                # 检查依赖是否已处理
                dependencies = node.get("dependencies", [])
                if dependencies and not all(dep in processed_nodes for dep in dependencies):
                    # 依赖未完成，稍后处理
                    nodes_to_process.append(node_id)
                    continue
                
                try:
                    task_type = node.get("task_type")
                    target_service = node.get("target_service")
                    action = node.get("action")
                    parameters = node.get("parameters", {})
                    
                    if task_type == "mcp_tool" or target_service == "mcp-gateway":
                        # 工具执行
                        result = await self.service_clients.mcp_gateway.execute_tool(
                            action,  # tool_name
                            parameters
                        )
                        used_services.append("mcp-gateway")
                    
                    elif task_type == "knowledge" or target_service == "knowledge-base":
                        # 知识库搜索
                        query = action if isinstance(action, str) else parameters.get("query", "")
                        result = await self.service_clients.knowledge_base.search(
                            query,
                            parameters.get("filters")
                        )
                        used_services.append("knowledge-base")
                        result = {
                            "success": True,
                            "result": result
                        }
                    
                    elif task_type == "workflow" or target_service == "workflow-engine":
                        # 工作流执行
                        workflow_id = action
                        result = await self.service_clients.workflow_engine.execute_workflow(
                            workflow_id,
                            parameters.get("input_data", {})
                        )
                        used_services.append("workflow-engine")
                    
                    else:
                        # 其他类型，尝试使用chat-service处理
                        prompt = node.get("description", user_input)
                        result = await self.service_clients.chat_service.process_message(
                            prompt,
                            context
                        )
                        used_services.append("chat-service")
                    
                    execution_results.append({
                        "node_id": node_id,
                        "node": node,
                        "result": result
                    })
                    
                    processed_nodes.add(node_id)
                    
                    # 添加依赖此节点的后续节点
                    for next_node_id, next_node in task_nodes.items():
                        if next_node_id not in processed_nodes and next_node_id not in nodes_to_process:
                            if node_id in next_node.get("dependencies", []):
                                nodes_to_process.append(next_node_id)
                    
                except Exception as e:
                    logger.error(f"Node {node_id} execution failed: {e}")
                    execution_results.append({
                        "node_id": node_id,
                        "node": node,
                        "result": {
                            "success": False,
                            "error": str(e)
                        }
                    })
                    processed_nodes.add(node_id)
            
            # 结果整合
            aggregated_result = await self._aggregate_results(execution_results, decomposition_result)
            
            return {
                "success": aggregated_result.get("success", True),
                "output": aggregated_result.get("final_output"),
                "subtasks_results": execution_results,
                "used_services": list(set(used_services)),
                "decomposition": decomposition_result
            }
            
        except Exception as e:
            logger.error(f"Complex orchestration failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_service_delegation(
        self,
        user_input: str,
        context: Dict[str, Any],
        decision: RoutingDecision,
        prompt_context: Optional[PromptContext] = None
    ) -> Dict[str, Any]:
        """处理服务委托"""
        target_service = decision.target_service
        
        try:
            if target_service == "knowledge-base":
                # 知识库搜索
                results = await self.service_clients.knowledge_base.search(
                    user_input,
                    limit=10,
                    filters=context.get("filters")
                )
                return {
                    "success": True,
                    "output": results,
                    "service": "knowledge-base"
                }
            elif target_service == "dag-orchestrator":
                # DAG任务分解和执行
                decomposition = await self.service_clients.dag_orchestrator.decompose_task(
                    user_input, context
                )
                if decomposition:
                    return {
                        "success": True,
                        "output": decomposition,
                        "service": "dag-orchestrator"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Task decomposition failed"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown service: {target_service}"
                }
        except Exception as e:
            logger.error(f"Service delegation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _aggregate_results(
        self,
        execution_results: List[Dict[str, Any]],
        decomposition_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """整合执行结果"""
        # 简单的结果整合：将所有成功的结果合并
        successful_results = [
            r["result"].get("output") or r["result"].get("result")
            for r in execution_results
            if r["result"].get("success", False)
        ]
        
        # 如果有失败的结果，记录错误
        failed_results = [
            r["result"].get("error")
            for r in execution_results
            if not r["result"].get("success", False)
        ]
        
        # 构建最终输出
        if successful_results:
            final_output = "\n\n".join([
                str(result) for result in successful_results if result
            ])
        else:
            final_output = "所有子任务执行失败"
        
        if failed_results:
            final_output += f"\n\n注意：部分任务执行失败：{', '.join(failed_results)}"
        
        return {
            "success": len(successful_results) > 0,
            "final_output": final_output,
            "successful_count": len(successful_results),
            "failed_count": len(failed_results)
        }
    
    async def orchestrate_stream(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式编排处理
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Yields:
            步骤结果
        """
        execution_path = []
        used_services = []
        overall_start_time = datetime.now()
        
        try:
            # 1. 任务理解
            history = context.get('history', [])
            user_context = {k: v for k, v in context.items() if k not in ['history', 'available_agents']}
            
            # ✅ 构建提示词上下文
            prompt_context = None
            if self.prompt_engine:
                try:
                    prompt_context = PromptContext(
                        user_id=context.get('user_id'),
                        session_id=context.get('session_id'),
                        conversation_history=history,
                        user_profile=context.get('user_profile'),
                        task_context=context.get('task_context'),
                        available_tools=context.get('available_tools', [])
                    )
                except Exception as e:
                    logger.warning(f"Failed to create prompt context: {e}")
            
            intent_analysis = await self.conversation_agent.understand_conversation(
                user_input, 
                history, 
                user_context,
                prompt_engine=self.prompt_engine,
                prompt_context=prompt_context
            )
            
            yield {
                "step_name": "intent_analysis",
                "partial_result": {
                    "task_type": intent_analysis.task_type.value,
                    "confidence": intent_analysis.confidence
                },
                "progress": 20
            }
            
            # 2. 任务分类和路由决策
            available_agents = context.get('available_agents', [])
            routing_decision = await self.task_classifier.classify_and_route(
                intent_analysis, available_agents
            )
            
            # 使用元数据增强路由决策（阶段2）
            try:
                from .metadata_driven_executor import metadata_driven_executor
                routing_decision = await metadata_driven_executor.enhance_with_metadata(
                    user_input=user_input,
                    intent_analysis=intent_analysis,
                    routing_decision=routing_decision,
                    context=context
                )
            except Exception as e:
                logger.debug(f"Failed to enhance routing decision with metadata: {e}")
            
            yield {
                "step_name": "routing_decision",
                "partial_result": {
                    "strategy": routing_decision.strategy.value,
                    "target_service": routing_decision.target_service,
                    "reasoning": routing_decision.reasoning
                },
                "progress": 40
            }
            
            # 3. 执行协调
            execution_methods = {
                ExecutionStrategy.DIRECT_LLM: self._handle_direct_llm,
                ExecutionStrategy.TOOL_CALL: lambda ui, ctx, rd, pc: self._handle_tool_execution(ui, ctx, rd, intent_analysis, pc),
                ExecutionStrategy.WORKFLOW_EXECUTION: self._handle_workflow,
                ExecutionStrategy.ORCHESTRATION: self._handle_complex_orchestration,
                ExecutionStrategy.SERVICE_DELEGATION: self._handle_service_delegation,
            }
            
            handler = execution_methods.get(
                routing_decision.strategy,
                self._handle_direct_llm
            )
            
            # 执行工具（这里会包含LLM分析，如果用户要求分析）
            result = await handler(user_input, context, routing_decision, prompt_context)
            
            # 如果结果包含"正在分析"提示，先发送查询结果部分
            final_response = result.get("output") or result.get("response") or ""
            if "正在使用AI分析数据" in final_response:
                # 分离查询结果和分析提示
                parts = final_response.split("🔄 **正在使用AI分析数据")
                query_result = parts[0] if parts else final_response
                
                # 先发送查询结果
                yield {
                    "step_name": "execution",
                    "partial_result": query_result,
                    "progress": 70
                }
                
                # 发送分析提示
                yield {
                    "step_name": "execution",
                    "partial_result": "\n\n🔄 **正在使用AI分析数据，请稍候...**\n\n",
                    "progress": 75
                }
                
                # 等待LLM分析完成（这里result已经包含完整结果，因为handler已经完成）
                # 但我们需要等待一下，让用户看到"正在分析"提示
                import asyncio
                await asyncio.sleep(0.5)  # 短暂延迟，让前端显示提示
                
                # 发送最终结果（包含分析）
                yield {
                    "step_name": "execution",
                    "partial_result": final_response,
                    "progress": 95
                }
            else:
                # 没有分析步骤，直接返回结果
                yield {
                    "step_name": "execution",
                    "partial_result": final_response,
                    "progress": 80
                }
            
            # 构建最终结果
            overall_execution_time = (datetime.now() - overall_start_time).total_seconds()
            final_result = {
                "success": result.get("success", False),
                "final_response": final_response,
                "execution_path": execution_path,
                "used_services": list(set(used_services)),
                "intent_analysis": {
                    "task_type": intent_analysis.task_type.value,
                    "confidence": intent_analysis.confidence,
                    "reasoning": intent_analysis.reasoning,
                },
                "routing_decision": {
                    "strategy": routing_decision.strategy.value,
                    "target_service": routing_decision.target_service,
                    "reasoning": routing_decision.reasoning,
                },
                "raw_result": result
            }
            
            yield {
                "step_name": "complete",
                "final_result": final_result,
                "progress": 100
            }
            
            # 异步保存对话元数据到metadata-service（不阻塞响应）
            try:
                from ..services.metadata_client import metadata_client
                # 在后台任务中保存，不阻塞主流程
                import asyncio
                asyncio.create_task(
                    metadata_client.save_conversation_metadata(
                        user_input=user_input,
                        ai_response=final_response,
                        intent_analysis=final_result.get("intent_analysis", {}),
                        routing_decision=final_result.get("routing_decision", {}),
                        execution_metadata={
                            "execution_timestamp": datetime.now().isoformat(),
                            "execution_time_seconds": overall_execution_time,
                            "user_input_preview": user_input[:100] + ("..." if len(user_input) > 100 else ""),
                            "session_id": context.get('session_id'),
                            "user_id": context.get('user_id'),
                            "success": final_result.get("success", False)
                        },
                        session_id=context.get('session_id'),
                        user_id=context.get('user_id')
                    )
                )
                logger.info(f"Queued conversation metadata save for stream execution")
            except Exception as e:
                logger.warning(f"Failed to queue conversation metadata save: {e}")
            
        except Exception as e:
            logger.error(f"Stream orchestration failed: {e}", exc_info=True)
            yield {
                "step_name": "error",
                "partial_result": {"error": str(e)},
                "progress": 100
            }


    def _extract_email_parameters(self, user_input: str, intent_analysis: Optional[IntentAnalysis] = None) -> Dict[str, Any]:
        """
        从用户输入中提取邮件参数
        
        Args:
            user_input: 用户输入
            intent_analysis: 意图分析结果（包含extracted_context）
            
        Returns:
            邮件参数字典
        """
        import re
        
        parameters = {}
        
        # 从intent_analysis中获取已提取的参数
        if intent_analysis and intent_analysis.extracted_context:
            extracted_params = intent_analysis.extracted_context.get("parameters", {})
        else:
            extracted_params = {}
        
        # 提取收件人邮箱
        # 匹配邮箱地址
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_input)
        
        # 匹配"给XXX发"、"发送给XXX"等模式
        send_patterns = [
            r'给\s*([^\s]+)\s*发',
            r'发送给\s*([^\s]+)',
            r'发给\s*([^\s]+)',
            r'给\s*([^\s]+)\s*发送',
            r'通知\s*([^\s]+)',
        ]
        
        for pattern in send_patterns:
            match = re.search(pattern, user_input)
            if match:
                recipient = match.group(1)
                # 如果匹配到的是邮箱，直接使用；否则尝试查找对应的邮箱
                if '@' in recipient:
                    emails.append(recipient)
                else:
                    # 尝试从上下文中查找邮箱（如"刘玉斌" -> "yubin.liu@pcitc.com"）
                    # 这里可以扩展为从用户联系人列表查找
                    pass
        
        if emails:
            # 确保 to_emails 始终是列表类型
            parameters["to_emails"] = emails if isinstance(emails, list) else [emails]
        
        # 提取主题（支持多个"主题"关键词，取最后一个或最详细的那个）
        subject_patterns = [
            r'主题[：:]\s*([^，,。\n]+)',
            r'标题[：:]\s*([^，,。\n]+)',
            r'subject[：:]\s*([^，,。\n]+)',
            r'关于[：:]\s*([^，,。\n]+)',
        ]
        
        # 找到所有匹配的主题
        all_subjects = []
        for pattern in subject_patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                subject_text = match.group(1).strip()
                if subject_text and subject_text not in all_subjects:
                    all_subjects.append(subject_text)
        
        # 如果有多个主题，选择最详细的那个（最长的）
        if all_subjects:
            parameters["subject"] = max(all_subjects, key=len)
        # 如果没有明确主题，尝试从上下文推断
        elif "会议" in user_input:
            # 尝试提取会议相关信息
            meeting_patterns = [
                r'会议通知[：:]\s*([^，,。\n]+)',
                r'讨论[：:]\s*([^，,。\n]+)',
                r'关于\s*([^，,。\n]+)\s*的讨论',
            ]
            for pattern in meeting_patterns:
                match = re.search(pattern, user_input)
                if match:
                    meeting_info = match.group(1).strip()
                    parameters["subject"] = f"会议通知：{meeting_info}"
                    break
            
            if "subject" not in parameters:
                # 检查是否有"关于...的讨论"模式
                about_match = re.search(r'关于\s*([^，,。\n]+)\s*的讨论', user_input)
                if about_match:
                    parameters["subject"] = f"会议通知：{about_match.group(1).strip()}"
                else:
                    parameters["subject"] = "会议通知"
        
        # 提取正文
        body_patterns = [
            r'正文[：:]\s*([^\n]+(?:\n[^\n]+)*)',
            r'内容[：:]\s*([^\n]+(?:\n[^\n]+)*)',
            r'body[：:]\s*([^\n]+(?:\n[^\n]+)*)',
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE | re.DOTALL)
            if match:
                parameters["body"] = match.group(1).strip()
                break
        
        # 如果没有明确正文，智能构建正文内容
        if "body" not in parameters:
            body_parts = []
            
            # 提取会议相关信息作为正文
            if "会议" in user_input:
                # 提取收件人姓名
                recipient_name_match = re.search(r'收件人\s*([^，,。\n]+)', user_input)
                if recipient_name_match:
                    recipient_name = recipient_name_match.group(1).strip()
                    body_parts.append(f"尊敬的{recipient_name}，")
                
                # 提取会议主题/讨论内容
                discussion_match = re.search(r'关于\s*([^，,。\n]+)\s*的讨论', user_input)
                if discussion_match:
                    discussion_topic = discussion_match.group(1).strip()
                    body_parts.append(f"\n\n本次会议将讨论：{discussion_topic}")
                
                # 提取会议时间
                time_match = re.search(r'时间[是：:]\s*([^，,。\n]+)', user_input)
                if time_match:
                    meeting_time = time_match.group(1).strip()
                    body_parts.append(f"\n\n会议时间：{meeting_time}")
                elif "明天" in user_input or "下午" in user_input or "点" in user_input:
                    # 尝试提取时间信息
                    time_info = []
                    if "明天" in user_input:
                        time_info.append("明天")
                    if "下午" in user_input:
                        time_info.append("下午")
                    if re.search(r'\d+点', user_input):
                        hour_match = re.search(r'(\d+)点', user_input)
                        if hour_match:
                            time_info.append(f"{hour_match.group(1)}点")
                    if time_info:
                        body_parts.append(f"\n\n会议时间：{' '.join(time_info)}")
                
                # 如果没有提取到具体内容，使用通用模板
                if len(body_parts) == 0:
                    body_parts.append("您好，")
                    body_parts.append("\n\n这是一封会议通知邮件。")
                    if "讨论" in user_input:
                        body_parts.append("\n\n请准时参加。")
            else:
                # 非会议邮件，尝试提取正文内容
                # 移除已提取的收件人和主题部分
                body = user_input
                
                # 移除邮箱地址
                if parameters.get("to_emails"):
                    for email in (parameters["to_emails"] if isinstance(parameters["to_emails"], list) else [parameters["to_emails"]]):
                        body = body.replace(email, "")
                
                # 移除主题相关关键词和内容
                body = re.sub(r'主题[：:]\s*[^，,。\n]+', '', body)
                body = re.sub(r'标题[：:]\s*[^，,。\n]+', '', body)
                body = re.sub(r'关于[：:]\s*[^，,。\n]+', '', body)
                body = re.sub(r'收件人\s*[^，,。\n]+', '', body)
                body = re.sub(r'给\s*[^，,。\n]+\s*发', '', body)
                body = re.sub(r'发送给\s*[^，,。\n]+', '', body)
                
                # 清理多余的空格和标点
                body = re.sub(r'[，,]\s*[，,]', '，', body)
                body = re.sub(r'\s+', ' ', body).strip()
                
                if body and len(body) > 5:  # 确保有实际内容
                    body_parts.append(body)
            
            # 构建最终正文
            if body_parts:
                parameters["body"] = ''.join(body_parts).strip()
            else:
                # 如果仍然没有内容，使用用户输入作为正文（去除明显的命令部分）
                clean_body = user_input
                # 移除明显的命令关键词
                clean_body = re.sub(r'给\s*[^，,。\n]+\s*发邮件', '', clean_body)
                clean_body = re.sub(r'收件人\s*[^，,。\n]+', '', clean_body)
                clean_body = re.sub(r'主题[：:]\s*[^，,。\n]+', '', clean_body)
                clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                parameters["body"] = clean_body if clean_body else "这是一封系统自动发送的邮件。"
        
        # 如果没有收件人，尝试从extracted_params获取
        if "to_emails" not in parameters and extracted_params.get("to_emails"):
            to_emails_value = extracted_params["to_emails"]
            # 确保 to_emails 始终是列表类型
            if isinstance(to_emails_value, str):
                parameters["to_emails"] = [to_emails_value]
            elif isinstance(to_emails_value, list):
                parameters["to_emails"] = to_emails_value
            else:
                parameters["to_emails"] = [str(to_emails_value)]
        
        # 如果没有主题，尝试从extracted_params获取
        if "subject" not in parameters and extracted_params.get("subject"):
            parameters["subject"] = extracted_params["subject"]
        
        # 如果没有正文，尝试从extracted_params获取
        if "body" not in parameters and extracted_params.get("body"):
            parameters["body"] = extracted_params["body"]
        
        # 确保必需参数存在
        if not parameters.get("to_emails"):
            # 如果仍然没有收件人，使用默认值（应该提示用户）
            logger.warning("No recipient email found in user input")
            parameters["to_emails"] = ["yubin.liu@pcitc.com"]  # 临时默认值，实际应该提示用户（确保是列表）
        else:
            # 确保 to_emails 是列表类型
            to_emails_value = parameters.get("to_emails")
            if isinstance(to_emails_value, str):
                parameters["to_emails"] = [to_emails_value]
            elif not isinstance(to_emails_value, list):
                parameters["to_emails"] = [str(to_emails_value)]
        
        if not parameters.get("subject"):
            parameters["subject"] = "系统通知"
        
        if not parameters.get("body"):
            parameters["body"] = user_input  # 使用用户输入作为正文
        
        return parameters
    
    def _format_tool_result(self, result: Any, tool_id: str) -> str:
        """
        格式化工具执行结果为可读文本
        
        Args:
            result: 工具执行结果（可能是字典、列表或其他类型）
            tool_id: 工具ID
        
        Returns:
            格式化后的文本字符串
        """
        import json
        
        # 如果result是字符串，直接返回
        if isinstance(result, str):
            return result
        
        # 如果result是None或空，返回提示信息
        if not result:
            return "工具执行完成，但未返回数据。"
        
        # 对于SAP查询工具，特殊处理
        if tool_id == "sap_query" or "sap" in tool_id.lower():
            return self._format_sap_result(result)
        
        # 对于其他工具，尝试格式化为JSON
        try:
            if isinstance(result, dict):
                # 如果是字典，尝试提取关键信息
                if "data" in result and isinstance(result["data"], list):
                    # 有数据列表的情况
                    data_list = result["data"]
                    count = result.get("count", len(data_list))
                    table = result.get("table", "未知表")
                    
                    formatted = f"查询结果（共 {count} 条记录）:\n\n"
                    formatted += self._format_data_table(data_list)
                    return formatted
                else:
                    # 普通字典，格式化为JSON
                    return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, list):
                # 列表数据，格式化为表格
                return self._format_data_table(result)
            else:
                # 其他类型，转换为字符串
                return str(result)
        except Exception as e:
            logger.warning(f"Failed to format tool result: {e}")
            return json.dumps(result, ensure_ascii=False, indent=2) if result else "工具执行完成。"
    
    def _format_sap_result(self, result: Any) -> str:
        """格式化SAP查询结果"""
        import json
        
        if isinstance(result, dict):
            # 提取关键信息
            table = result.get("table", "未知表")
            query = result.get("query", "")
            data = result.get("data", [])
            count = result.get("count", len(data))
            
            formatted = f"📊 SAP查询结果\n"
            formatted += f"表名: {table}\n"
            if query:
                formatted += f"查询条件: {query}\n"
            formatted += f"记录数: {count}\n\n"
            
            if data and isinstance(data, list) and len(data) > 0:
                formatted += "查询数据:\n"
                formatted += self._format_data_table(data)
            else:
                formatted += "未找到匹配的数据。"
            
            return formatted
        else:
            return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _format_data_table(self, data: List[Dict[str, Any]]) -> str:
        """将数据列表格式化为表格文本"""
        if not data or len(data) == 0:
            return "无数据"
        
        # 获取所有字段名
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            return "数据格式不正确"
        
        # 转换为列表并排序
        keys = sorted(list(all_keys))
        
        # 计算每列的最大宽度
        col_widths = {}
        for key in keys:
            col_widths[key] = max(len(str(key)), max([len(str(item.get(key, ""))) for item in data if isinstance(item, dict)]))
        
        # 生成表格
        formatted = ""
        
        # 表头
        header = " | ".join([str(key).ljust(col_widths[key]) for key in keys])
        formatted += header + "\n"
        formatted += "-" * len(header) + "\n"
        
        # 数据行
        for item in data:
            if isinstance(item, dict):
                row = " | ".join([str(item.get(key, "")).ljust(col_widths[key]) for key in keys])
                formatted += row + "\n"
        
        return formatted


# 全局编排引擎实例
orchestration_engine = OrchestrationEngine()

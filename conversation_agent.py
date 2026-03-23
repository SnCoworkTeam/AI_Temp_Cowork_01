"""
对话理解智能体
分析用户意图、提取上下文、识别任务类型
"""
import logging
import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum

from .llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型枚举"""
    SIMPLE_QUERY = "simple_query"  # 简单查询
    TOOL_EXECUTION = "tool_execution"  # 工具执行
    WORKFLOW_TASK = "workflow_task"  # 工作流任务
    COMPLEX_ANALYSIS = "complex_analysis"  # 复杂分析
    KNOWLEDGE_SEARCH = "knowledge_search"  # 知识库搜索
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    UNKNOWN = "unknown"  # 未知类型


class IntentAnalysis:
    """意图分析结果"""
    def __init__(
        self,
        task_type: TaskType,
        confidence: float,
        extracted_context: Dict[str, Any],
        required_tools: List[str],
        required_services: List[str],
        reasoning: str
    ):
        self.task_type = task_type
        self.confidence = confidence
        self.extracted_context = extracted_context
        self.required_tools = required_tools
        self.required_services = required_services
        self.reasoning = reasoning


class ConversationAgent:
    """对话理解智能体"""
    
    def __init__(self, use_metadata_first: bool = True):
        """
        初始化对话理解智能体
        
        Args:
            use_metadata_first: 是否使用元数据前置模式（默认True）
        """
        self.use_llm = bool(deepseek_llm.llm)
        self.use_metadata_first = use_metadata_first
        
        # 如果启用元数据前置，初始化元数据前置识别器
        if self.use_metadata_first:
            try:
                from .metadata_first_intent_recognizer import MetadataFirstIntentRecognizer
                self.metadata_first_recognizer = MetadataFirstIntentRecognizer(llm_service=deepseek_llm)
                logger.info("Metadata-first intent recognizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize metadata-first recognizer: {e}, falling back to basic mode")
                self.use_metadata_first = False
                self.metadata_first_recognizer = None
        else:
            self.metadata_first_recognizer = None
        
        # 关键词模式（用于规则匹配）
        self.keyword_patterns = {
            TaskType.TOOL_EXECUTION: [
                r"执行|调用|运行|使用.*工具|调用.*API|执行.*命令",
                r"tool|execute|run|call.*api|invoke",
                r"帮我.*做|请.*执行|需要.*工具",
                # SAP相关查询模式
                r"SAP|sap|ERP|erp|销售订单|采购订单|物料|客户|供应商|发票|交货单",
                r"查询.*SAP|查.*SAP|SAP.*查询|SAP.*数据|SAP.*订单|SAP.*客户",
                r"sales.*order|purchase.*order|material|customer|vendor|invoice|delivery",
                r"OData|odata|MCP.*工具|sap.*工具",
                # 邮件发送相关模式
                r"发送.*邮件|发邮件|邮件.*发送|send.*email|email.*send|mail.*send",
                r"发.*给|发送.*给|通知.*邮件|会议.*通知|邮件.*通知",
                r"给.*发邮件|给.*发送|邮件.*给"
            ],
            TaskType.WORKFLOW_TASK: [
                r"工作流|流程|pipeline|workflow|自动化.*流程",
                r"创建.*流程|设计.*工作流|执行.*工作流"
            ],
            TaskType.COMPLEX_ANALYSIS: [
                r"分析|分析.*数据|复杂.*任务|多步骤|需要.*步骤",
                r"analyze|analysis|complex|multi.*step"
            ],
            TaskType.KNOWLEDGE_SEARCH: [
                r"搜索|查找|查询.*知识|知识库|文档|文档库",
                r"search|find|knowledge|document|doc"
            ],
            TaskType.DATA_ANALYSIS: [
                r"数据.*分析|分析.*数据|统计|报表|dashboard|趋势",
                r"data.*analysis|analyze.*data|statistics|report|trend"
            ],
        }
    
    async def understand_conversation(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        prompt_engine=None,  # ✅ 新增参数：提示词引擎
        prompt_context=None  # ✅ 新增参数：提示词上下文
    ) -> IntentAnalysis:
        """
        理解对话意图 - 支持元数据前置和优化提示词
        
        Args:
            message: 用户消息
            conversation_history: 对话历史
            user_context: 用户上下文
            prompt_engine: 提示词引擎（可选）
            prompt_context: 提示词上下文（可选）
            
        Returns:
            意图分析结果
        """
        # 如果启用元数据前置，优先使用元数据前置识别器
        if self.use_metadata_first and self.metadata_first_recognizer:
            try:
                logger.debug("Using metadata-first intent recognition")
                return await self.metadata_first_recognizer.recognize_intent(
                    user_input=message,
                    context=user_context,
                    conversation_history=conversation_history
                )
            except Exception as e:
                logger.warning(f"Metadata-first recognition failed: {e}, falling back to basic mode")
                # 继续执行后续的基础识别逻辑
        
        # 尝试使用元数据增强的提示词
        enhanced_system_prompt = None
        try:
            from ..core.metadata_enhanced_prompt import metadata_enhanced_prompt_builder
            
            if prompt_context:
                enhanced_system_prompt = await metadata_enhanced_prompt_builder.build_enhanced_prompt(
                    user_input=message,
                    context=prompt_context
                )
                logger.debug("Built metadata-enhanced system prompt")
        except Exception as e:
            logger.debug(f"Failed to build metadata-enhanced prompt: {e}, using default")
        
        # 使用优化提示词（如果提供）
        if prompt_engine and prompt_context and self.use_llm and deepseek_llm.llm:
            try:
                from ..prompt_engine.prompt_engine import PromptEngine
                from ..prompt_templates.base_templates import TaskCategory
                
                optimized_prompt = await prompt_engine.get_optimized_prompt(
                    TaskCategory.CONVERSATION_UNDERSTANDING,
                    message,
                    prompt_context
                )
                
                # 如果构建了元数据增强提示词，替换系统提示
                if enhanced_system_prompt and optimized_prompt.messages:
                    # 查找系统消息并替换
                    for msg in optimized_prompt.messages:
                        if msg.get("role") == "system":
                            msg["content"] = enhanced_system_prompt
                            break
                    else:
                        # 如果没有系统消息，在开头添加
                        optimized_prompt.messages.insert(0, {
                            "role": "system",
                            "content": enhanced_system_prompt
                        })
                
                # 使用优化提示词调用LLM
                response = await deepseek_llm.chat(
                    messages=optimized_prompt.messages,
                    temperature=optimized_prompt.temperature,
                    max_tokens=optimized_prompt.max_tokens
                )
                
                return self._parse_intent_response(response)
                
            except Exception as e:
                logger.warning(f"Optimized intent analysis failed: {e}, falling back to basic method", exc_info=True)
        
        # 降级到基础方法
        if self.use_llm and deepseek_llm.llm:
            return await self._analyze_with_llm(message, conversation_history, user_context, enhanced_system_prompt)
        else:
            return await self._analyze_with_rules(message, conversation_history, user_context)
    
    async def _analyze_with_llm(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        user_context: Optional[Dict[str, Any]],
        enhanced_system_prompt: Optional[str] = None
    ) -> IntentAnalysis:
        """使用LLM分析意图"""
        try:
            # 构建系统提示（使用增强提示词或默认提示词）
            if enhanced_system_prompt:
                system_prompt = enhanced_system_prompt
            else:
                system_prompt = """你是一个对话理解智能体，负责分析用户意图并提取关键信息。

# 角色定义
- "你"指AI助手（系统）
- "我"指用户
- 当用户说"你分析一下"时，意思是"AI分析"
- 当用户说"我来操作"时，意思是"用户操作"
- 当用户说"给出执行过程"时，意思是"显示执行过程"

# 人称代词处理规则
1. "你" + 动作 → AI执行该动作
2. "我" + 动作 → 用户执行该动作
3. "给出" + 名词 → 显示/返回该名词

任务类型：
1. simple_query - 简单查询，只需要LLM回答（一般性问题、概念解释）
2. tool_execution - 需要执行工具或调用API（查询SAP数据、调用外部系统、执行操作）
3. workflow_task - 工作流相关任务
4. complex_analysis - 复杂分析任务，需要多步骤处理
5. knowledge_search - 知识库搜索
6. data_analysis - 数据分析任务

重要规则：
- 如果用户查询SAP ERP数据（如销售订单、采购订单、物料、客户、供应商等），必须使用 tool_execution 类型
- 如果用户提到"SAP"、"ERP"、"查询"、"查一下"等关键词，且涉及具体业务数据，应识别为 tool_execution
- 如果只是询问SAP概念、使用方法等知识性问题，可以使用 simple_query
- 对于SAP查询，required_tools 应包含 "sap_query" 或相关的SAP工具
- 注意区分用户说的"你"（指AI）和"我"（指用户），正确识别动作的执行者

请分析用户消息，返回JSON格式：
{
    "task_type": "任务类型",
    "confidence": 0.0-1.0之间的置信度,
    "extracted_context": {
        "entities": ["实体1", "实体2"],
        "parameters": {"参数名": "参数值"},
        "intent": "用户意图描述"
    },
    "required_tools": ["需要的工具列表"],
    "required_services": ["需要的服务列表"],
    "reasoning": "分析理由"
}"""

            # 构建消息
            messages = []
            
            # 添加对话历史（增加到20条，保持更长的上下文记忆）
            if conversation_history:
                messages.extend(conversation_history[-20:])  # 增加到20条，保持更长的对话上下文
            
            # 添加用户上下文
            if user_context:
                context_str = json.dumps(user_context, ensure_ascii=False)
                messages.append({
                    "role": "system",
                    "content": f"用户上下文：{context_str}"
                })
            
            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message
            })
            
            # 调用LLM（使用增强提示词或默认提示词）
            final_system_prompt = enhanced_system_prompt if enhanced_system_prompt else system_prompt
            response = await deepseek_llm.chat(
                messages=messages,
                system_prompt=final_system_prompt,
                temperature=0.3
            )
            
            return self._parse_intent_response(response)
        except Exception as e:
            logger.error(f"LLM intent analysis failed: {e}", exc_info=True)
            # 返回默认分析结果
            return IntentAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                extracted_context={},
                required_tools=[],
                required_services=[],
                reasoning=f"LLM analysis failed: {str(e)}"
            )
    
    def _parse_intent_response(self, response: str) -> IntentAnalysis:
        """解析意图分析响应"""
        try:
            response_text = response.strip()
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
                response_text = re.sub(r"\n?```$", "", response_text)
            
            analysis_data = json.loads(response_text)
            
            return IntentAnalysis(
                task_type=TaskType(analysis_data.get("task_type", "unknown")),
                confidence=float(analysis_data.get("confidence", 0.5)),
                extracted_context=analysis_data.get("extracted_context", {}),
                required_tools=analysis_data.get("required_tools", []),
                required_services=analysis_data.get("required_services", []),
                reasoning=analysis_data.get("reasoning", "LLM analysis")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent response: {e}, response: {response[:200]}")
            # 返回默认分析结果
            return IntentAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                extracted_context={},
                required_tools=[],
                required_services=[],
                reasoning=f"Failed to parse LLM response: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Parse intent response failed: {e}", exc_info=True)
            # 返回默认分析结果
            return IntentAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                extracted_context={},
                required_tools=[],
                required_services=[],
                reasoning=f"Parse failed: {str(e)}"
            )
    
    async def _analyze_with_rules(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        user_context: Optional[Dict[str, Any]]
    ) -> IntentAnalysis:
        """使用规则分析意图"""
        message_lower = message.lower()
        
        # 计算每个任务类型的匹配分数
        task_scores = {}
        
        for task_type, patterns in self.keyword_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower, re.IGNORECASE))
                score += matches * 0.3
            
            if score > 0:
                task_scores[task_type] = score
        
        # 选择得分最高的任务类型
        if task_scores:
            best_task = max(task_scores.items(), key=lambda x: x[1])
            task_type = best_task[0]
            confidence = min(best_task[1] / 2.0, 1.0)
        else:
            task_type = TaskType.SIMPLE_QUERY
            confidence = 0.5
        
        # 提取上下文（简单版本）
        extracted_context = {
            "entities": self._extract_entities(message),
            "parameters": self._extract_parameters(message),
            "intent": message
        }
        
        # 推断需要的工具和服务
        required_tools = []
        required_services = []
        
        if task_type == TaskType.TOOL_EXECUTION:
            required_services.append("mcp-gateway")
        elif task_type == TaskType.WORKFLOW_TASK:
            required_services.append("workflow-engine")
        elif task_type == TaskType.COMPLEX_ANALYSIS:
            required_services.append("agent-orchestrator")
            required_services.append("dag-orchestrator")
        elif task_type == TaskType.KNOWLEDGE_SEARCH:
            required_services.append("knowledge-base")
        elif task_type == TaskType.DATA_ANALYSIS:
            required_services.append("dag-orchestrator")
            required_services.append("mcp-gateway")
        
        return IntentAnalysis(
            task_type=task_type,
            confidence=confidence,
            extracted_context=extracted_context,
            required_tools=required_tools,
            required_services=required_services,
            reasoning=f"Rule-based matching: {task_type.value} (score: {confidence:.2f})"
        )
    
    def _extract_entities(self, message: str) -> List[str]:
        """提取实体（简单版本）"""
        # 这里可以使用更复杂的NLP技术
        entities = []
        
        # 提取可能的实体（数字、日期、名称等）
        # 简化实现，实际应该使用NER模型
        return entities
    
    def _extract_parameters(self, message: str) -> Dict[str, Any]:
        """提取参数（简单版本）"""
        parameters = {}
        
        # 提取常见参数模式
        # 例如：日期、时间、数量等
        # 简化实现，实际应该使用更复杂的解析
        
        return parameters


# 全局对话理解智能体实例
# 默认启用元数据前置模式
conversation_agent = ConversationAgent(use_metadata_first=True)





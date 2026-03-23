"""
任务分类器
根据意图分析结果，决定执行策略和路由目标
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from .conversation_agent import TaskType, IntentAnalysis

logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """执行策略枚举"""
    DIRECT_LLM = "direct_llm"  # 直接使用LLM
    TOOL_CALL = "tool_call"  # 调用工具
    WORKFLOW_EXECUTION = "workflow_execution"  # 执行工作流
    ORCHESTRATION = "orchestration"  # 智能体编排
    SERVICE_DELEGATION = "service_delegation"  # 委托给其他服务


class RoutingDecision:
    """路由决策结果"""
    def __init__(
        self,
        strategy: ExecutionStrategy,
        target_service: Optional[str],
        target_agent_id: Optional[str],
        required_tools: List[str],
        execution_params: Dict[str, Any],
        reasoning: str
    ):
        self.strategy = strategy
        self.target_service = target_service
        self.target_agent_id = target_agent_id
        self.required_tools = required_tools
        self.execution_params = execution_params
        self.reasoning = reasoning


class TaskClassifier:
    """任务分类器"""
    
    def __init__(self):
        # 任务类型到执行策略的映射
        self.strategy_mapping = {
            TaskType.SIMPLE_QUERY: ExecutionStrategy.DIRECT_LLM,
            TaskType.TOOL_EXECUTION: ExecutionStrategy.TOOL_CALL,
            TaskType.WORKFLOW_TASK: ExecutionStrategy.WORKFLOW_EXECUTION,
            TaskType.COMPLEX_ANALYSIS: ExecutionStrategy.ORCHESTRATION,
            TaskType.KNOWLEDGE_SEARCH: ExecutionStrategy.SERVICE_DELEGATION,
            TaskType.DATA_ANALYSIS: ExecutionStrategy.ORCHESTRATION,
        }
        
        # 任务类型到目标服务的映射
        self.service_mapping = {
            TaskType.SIMPLE_QUERY: "chat-service",
            TaskType.TOOL_EXECUTION: "mcp-gateway",
            TaskType.WORKFLOW_TASK: "workflow-engine",
            TaskType.COMPLEX_ANALYSIS: "agent-orchestrator",
            TaskType.KNOWLEDGE_SEARCH: "knowledge-base",
            TaskType.DATA_ANALYSIS: "dag-orchestrator",
        }
    
    async def classify_and_route(
        self,
        intent_analysis: IntentAnalysis,
        available_agents: Optional[List[Dict[str, Any]]] = None
    ) -> RoutingDecision:
        """
        分类任务并决定路由策略
        
        Args:
            intent_analysis: 意图分析结果
            available_agents: 可用的智能体列表
            
        Returns:
            路由决策结果
        """
        task_type = intent_analysis.task_type
        
        # 获取执行策略
        strategy = self.strategy_mapping.get(task_type, ExecutionStrategy.DIRECT_LLM)
        
        # 获取目标服务
        target_service = self.service_mapping.get(task_type)
        
        # 选择智能体（如果需要）
        target_agent_id = None
        if strategy in [ExecutionStrategy.DIRECT_LLM, ExecutionStrategy.TOOL_CALL]:
            target_agent_id = await self._select_agent(
                task_type,
                intent_analysis.required_tools,
                available_agents
            )
        
        # 构建执行参数
        execution_params = {
            "task_type": task_type.value,
            "confidence": intent_analysis.confidence,
            "context": intent_analysis.extracted_context,
            "required_tools": intent_analysis.required_tools,
        }
        
        reasoning = f"Task classified as {task_type.value}, using {strategy.value} strategy"
        if target_service:
            reasoning += f", routing to {target_service}"
        if target_agent_id:
            reasoning += f", using agent {target_agent_id}"
        
        return RoutingDecision(
            strategy=strategy,
            target_service=target_service,
            target_agent_id=target_agent_id,
            required_tools=intent_analysis.required_tools,
            execution_params=execution_params,
            reasoning=reasoning
        )
    
    async def _select_agent(
        self,
        task_type: TaskType,
        required_tools: List[str],
        available_agents: Optional[List[Dict[str, Any]]]
    ) -> Optional[str]:
        """
        选择最合适的智能体
        
        Args:
            task_type: 任务类型
            required_tools: 需要的工具列表
            available_agents: 可用的智能体列表
            
        Returns:
            智能体ID
        """
        if not available_agents:
            return None
        
        # 根据任务类型和能力匹配智能体
        best_agent = None
        best_score = 0.0
        
        for agent in available_agents:
            if not isinstance(agent, dict):
                continue
            
            score = 0.0
            capabilities = agent.get("capabilities", [])
            
            # 根据任务类型匹配能力
            if task_type == TaskType.TOOL_EXECUTION:
                if "tool_execution" in capabilities or "code_generation" in capabilities:
                    score += 0.5
            elif task_type == TaskType.DATA_ANALYSIS:
                if "data_analysis" in capabilities:
                    score += 0.5
            elif task_type == TaskType.KNOWLEDGE_SEARCH:
                if "knowledge_retrieval" in capabilities:
                    score += 0.5
            
            # 根据需要的工具匹配
            if required_tools:
                # 这里可以检查智能体是否支持这些工具
                score += 0.3
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.get("id") if best_agent else None


# 全局任务分类器实例
task_classifier = TaskClassifier()





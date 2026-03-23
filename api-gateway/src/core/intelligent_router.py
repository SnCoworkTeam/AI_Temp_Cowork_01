"""
智能路由决策器
基于请求内容智能路由到最佳服务
"""
import logging
import os
import json
import re
from typing import Dict, Any, Optional, List
from enum import Enum
from fastapi import Request

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class RouteIntent(str, Enum):
    """路由意图枚举"""
    SIMPLE_CHAT = "simple_chat"  # 简单对话
    TOOL_EXECUTION = "tool_execution"  # 需要工具执行
    WORKFLOW_TASK = "workflow_task"  # 工作流任务
    AGENT_TASK = "agent_task"  # 智能体任务
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    KNOWLEDGE_SEARCH = "knowledge_search"  # 知识库搜索
    UNKNOWN = "unknown"  # 未知意图


class IntentAnalysis:
    """意图分析结果"""
    def __init__(
        self,
        intent: RouteIntent,
        confidence: float,
        requires_tools: bool = False,
        is_workflow_task: bool = False,
        is_simple_chat: bool = False,
        needs_data_analysis: bool = False,
        needs_knowledge_search: bool = False,
        reasoning: str = ""
    ):
        self.intent = intent
        self.confidence = confidence
        self.requires_tools = requires_tools
        self.is_workflow_task = is_workflow_task
        self.is_simple_chat = is_simple_chat
        self.needs_data_analysis = needs_data_analysis
        self.needs_knowledge_search = needs_knowledge_search
        self.reasoning = reasoning


class IntelligentRouter:
    """智能路由决策器"""
    
    def __init__(self):
        self.llm_client = None
        self.use_llm = os.getenv("INTELLIGENT_ROUTER_USE_LLM", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        
        # 初始化LLM客户端（如果启用）
        if self.use_llm and LANGCHAIN_AVAILABLE and self.api_key:
            self._init_llm()
        
        # 路由映射
        self.route_mapping = {
            RouteIntent.SIMPLE_CHAT: "chat-service",  # 简单对话使用chat-service
            RouteIntent.TOOL_EXECUTION: "agent-service",
            RouteIntent.WORKFLOW_TASK: "workflow-engine",
            RouteIntent.AGENT_TASK: "agent-service",
            RouteIntent.DATA_ANALYSIS: "dag-orchestrator",
            RouteIntent.KNOWLEDGE_SEARCH: "knowledge-base",
        }
        
        # 关键词映射（用于规则匹配）
        self.keyword_patterns = {
            RouteIntent.TOOL_EXECUTION: [
                r"执行|调用|运行|使用.*工具|调用.*API|执行.*命令",
                r"tool|execute|run|call.*api|invoke",
                r"帮我.*做|请.*执行|需要.*工具"
            ],
            RouteIntent.WORKFLOW_TASK: [
                r"工作流|流程|pipeline|workflow|自动化.*流程",
                r"创建.*流程|设计.*工作流|执行.*工作流"
            ],
            RouteIntent.AGENT_TASK: [
                r"智能体|agent|帮我完成|自动.*处理|复杂.*任务",
                r"需要.*智能体|使用.*agent|编排.*任务"
            ],
            RouteIntent.DATA_ANALYSIS: [
                r"分析.*数据|数据.*分析|统计|报表|dashboard",
                r"data.*analysis|analyze|statistics|report"
            ],
            RouteIntent.KNOWLEDGE_SEARCH: [
                r"搜索|查找|查询.*知识|知识库|文档|文档库",
                r"search|find|knowledge|document|doc"
            ],
        }
    
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            llm_kwargs = {
                "model": self.model,
                "temperature": 0.3,  # 较低温度以获得更稳定的路由决策
                "api_key": self.api_key,
            }
            
            if self.base_url:
                base_url_clean = self.base_url.rstrip("/v1").rstrip("/")
                llm_kwargs["base_url"] = base_url_clean
            
            self.llm_client = ChatOpenAI(**llm_kwargs)
            logger.info(f"Intelligent Router LLM initialized: model={self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM for Intelligent Router: {e}")
            self.llm_client = None
            self.use_llm = False
    
    async def determine_best_service(self, request: Request) -> str:
        """
        简化路由策略：只做静态路由，所有对话请求统一到agent-service
        让agent-service内部的orchestrator做唯一的智能决策
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            目标服务名称
        """
        path = request.url.path
        
        # 1. 静态API路径路由（保持现有逻辑）
        static_mappings = {
            "/api/workflows": "workflow-engine",
            "/api/mcp": "mcp-gateway",
            "/api/auth": "auth-service",
            "/api/knowledge": "knowledge-base",
            "/api/metadata": "metadata-service",
            "/api/dag": "dag-orchestrator",
            "/api/registry": "registry-service",
            "/api/config": "config-center",
            "/api/agent-registry": "agent-registry",
            "/api/joyagent": "joyagent-adapter",
        }
        
        for prefix, service in static_mappings.items():
            if path.startswith(prefix):
                return service
        
        # 2. 所有其他请求（包括对话）都路由到agent-service
        # 包括：/api/chat, /api/chat/intelligent, /api/agents, /api/orchestrate 等
        return "agent-service"
    
    async def _route_by_path(self, request: Request) -> str:
        """
        基于路径的静态路由（已废弃，逻辑已合并到determine_best_service）
        保留此方法以保持向后兼容，但不再使用
        """
        # 此方法已被determine_best_service替代
        return await self.determine_best_service(request)
    
    # ⚠️ 以下方法已废弃，不再使用
    # 智能路由决策已移至Agent Service的OrchestrationEngine
    # 保留这些方法仅用于向后兼容，但不会被调用
    
    async def _is_conversational_request(self, request: Request) -> bool:
        """
        对话请求识别（已废弃）
        现在所有对话请求都统一路由到agent-service，不再需要此方法
        """
        # 此方法已不再使用，所有对话请求都通过determine_best_service路由到agent-service
        return True
    
    async def _route_by_content(self, request: Request) -> str:
        """
        基于内容的路由决策（已废弃）
        智能路由决策已移至Agent Service的OrchestrationEngine
        """
        logger.warning("_route_by_content is deprecated, all requests should route to agent-service")
        return "agent-service"
    
    async def _extract_content(self, request: Request) -> Optional[str]:
        """
        从请求中提取内容（已废弃）
        不再在API Gateway层进行内容分析
        """
        return None
    
    async def _analyze_intent_with_rules(self, content: str) -> IntentAnalysis:
        """
        使用规则分析意图（已废弃）
        意图分析已移至Agent Service的ConversationAgent
        """
        # 返回默认值，但此方法不应被调用
        return IntentAnalysis(
            intent=RouteIntent.UNKNOWN,
            confidence=0.0,
            reasoning="This method is deprecated"
        )
    
    async def _analyze_intent_with_llm(self, content: str) -> IntentAnalysis:
        """
        使用LLM分析意图（已废弃）
        意图分析已移至Agent Service的ConversationAgent
        """
        # 返回默认值，但此方法不应被调用
        return IntentAnalysis(
            intent=RouteIntent.UNKNOWN,
            confidence=0.0,
            reasoning="This method is deprecated"
        )


# 全局智能路由实例
intelligent_router = IntelligentRouter()


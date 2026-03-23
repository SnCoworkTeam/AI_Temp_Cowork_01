"""
Platform Integration Service

Handles integration between JoyAgent and other platform services
(MCP Gateway, Workflow Engine, Knowledge Base, Metadata Service).
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
import httpx
import structlog

from ..config import settings
from ..models import (
    JoyAgentTaskRequest,
    TaskType,
    AgentMode,
    WorkflowIntegrationRequest,
    KnowledgeEnhancementRequest,
    MCPToolIntegrationRequest,
    IntegrationContext
)

logger = structlog.get_logger(__name__)


class PlatformIntegrationService:
    """Service for integrating JoyAgent with platform services"""

    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.workflow_callbacks: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the integration service"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10)
        )
        logger.info("Platform integration service initialized")

    async def shutdown(self):
        """Shutdown the integration service"""
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Platform integration service shut down")

    async def enhance_task_with_workflow_context(
        self,
        task_request: JoyAgentTaskRequest,
        context: IntegrationContext
    ) -> JoyAgentTaskRequest:
        """Enhance JoyAgent task with workflow context"""
        try:
            enhanced_context = task_request.context or {}

            # Add workflow context
            if context.workflow_id:
                workflow_info = await self._get_workflow_info(context.workflow_id)
                enhanced_context["workflow"] = workflow_info

            # Add user context
            if context.user_id:
                enhanced_context["user_id"] = context.user_id

            # Add session context
            if context.session_id:
                enhanced_context["session_id"] = context.session_id

            # Add knowledge base context
            if context.knowledge_context:
                enhanced_context["knowledge"] = context.knowledge_context

            # Add available MCP tools
            if context.mcp_tools:
                enhanced_context["available_tools"] = context.mcp_tools

            # Create enhanced task
            enhanced_task = JoyAgentTaskRequest(
                query=task_request.query,
                task_type=task_request.task_type,
                mode=task_request.mode,
                context=enhanced_context,
                parameters=task_request.parameters,
                timeout=task_request.timeout,
                priority=task_request.priority,
                metadata={
                    **(task_request.metadata or {}),
                    "workflow_integration": True,
                    "enhanced_context": True
                }
            )

            return enhanced_task

        except Exception as e:
            logger.error(f"Failed to enhance task with workflow context: {e}")
            # Return original task if enhancement fails
            return task_request

    async def _get_workflow_info(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow information from Workflow Engine"""
        try:
            response = await self.http_client.get(
                f"{settings.workflow_engine_url}/api/workflows/{workflow_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get workflow info: {response.status_code}")
                return {"workflow_id": workflow_id, "status": "unknown"}

        except Exception as e:
            logger.error(f"Error getting workflow info: {e}")
            return {"workflow_id": workflow_id, "error": str(e)}

    async def register_workflow_callback(
        self,
        task_id: str,
        callback_url: str,
        workflow_id: str,
        step_name: str
    ):
        """Register callback for workflow task completion"""
        self.workflow_callbacks[task_id] = {
            "callback_url": callback_url,
            "workflow_id": workflow_id,
            "step_name": step_name,
            "registered_at": asyncio.get_event_loop().time()
        }
        logger.info(f"Registered workflow callback for task {task_id}")

    async def create_knowledge_enhancement_task(
        self,
        request: KnowledgeEnhancementRequest
    ) -> JoyAgentTaskRequest:
        """Create JoyAgent task for knowledge enhancement"""
        try:
            # Get knowledge base context if specified
            knowledge_context = {}
            if request.knowledge_base_id:
                knowledge_context = await self._get_knowledge_context(
                    request.knowledge_base_id,
                    request.query
                )

            # Prepare task based on enhancement type
            if request.enhancement_type == "analysis":
                task_type = TaskType.DATA_ANALYSIS
                enhanced_query = f"分析以下知识内容并提供洞察：{request.query}"
            elif request.enhancement_type == "summary":
                task_type = TaskType.DOCUMENT_PROCESSING
                enhanced_query = f"总结以下内容的关键信息：{request.query}"
            elif request.enhancement_type == "report":
                task_type = TaskType.REPORT_GENERATION
                enhanced_query = f"基于以下信息生成详细报告：{request.query}"
            else:
                task_type = TaskType.QUERY
                enhanced_query = request.query

            return JoyAgentTaskRequest(
                query=enhanced_query,
                task_type=task_type,
                mode=AgentMode.AUTO,
                context={
                    "knowledge_base_context": knowledge_context,
                    "enhancement_type": request.enhancement_type,
                    "parameters": request.parameters
                },
                parameters={
                    "knowledge_enhancement": True,
                    **request.parameters
                },
                metadata={
                    "integration_type": "knowledge_enhancement",
                    "knowledge_base_id": request.knowledge_base_id
                }
            )

        except Exception as e:
            logger.error(f"Failed to create knowledge enhancement task: {e}")
            raise

    async def _get_knowledge_context(
        self,
        knowledge_base_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Get relevant knowledge context from Knowledge Base service"""
        try:
            search_payload = {
                "query": query,
                "knowledge_base_id": knowledge_base_id,
                "top_k": 5
            }

            response = await self.http_client.post(
                f"{settings.knowledge_base_url}/api/search",
                json=search_payload
            )

            if response.status_code == 200:
                search_results = response.json()
                return {
                    "relevant_documents": search_results.get("documents", []),
                    "search_query": query,
                    "knowledge_base_id": knowledge_base_id
                }
            else:
                logger.warning(f"Knowledge base search failed: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error getting knowledge context: {e}")
            return {}

    async def create_mcp_integration_task(
        self,
        request: MCPToolIntegrationRequest
    ) -> JoyAgentTaskRequest:
        """Create JoyAgent task with MCP tool integration"""
        try:
            # Get MCP tool information
            tool_info = await self._get_mcp_tool_info(request.tool_name)

            # Prepare context with MCP tool information
            mcp_context = {
                "tool_name": request.tool_name,
                "tool_action": request.action,
                "tool_parameters": request.parameters,
                "tool_info": tool_info
            }

            # Add JoyAgent context if provided
            if request.joyagent_context:
                mcp_context.update(request.joyagent_context)

            # Create enhanced query that includes MCP tool usage
            enhanced_query = (
                f"使用 {request.tool_name} 工具执行 {request.action} 操作，"
                f"参数：{json.dumps(request.parameters, ensure_ascii=False)}，"
                f"并分析处理结果"
            )

            return JoyAgentTaskRequest(
                query=enhanced_query,
                task_type=TaskType.CUSTOM,
                mode=AgentMode.PLAN_AND_EXECUTE,
                context=mcp_context,
                parameters={
                    "mcp_integration": True,
                    "tool_name": request.tool_name,
                    "tool_action": request.action,
                    **request.parameters
                },
                metadata={
                    "integration_type": "mcp_tool",
                    "tool_name": request.tool_name,
                    "action": request.action
                }
            )

        except Exception as e:
            logger.error(f"Failed to create MCP integration task: {e}")
            raise

    async def _get_mcp_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get MCP tool information from MCP Gateway"""
        try:
            response = await self.http_client.get(
                f"{settings.mcp_gateway_url}/api/tools/{tool_name}"
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get MCP tool info: {response.status_code}")
                return {"tool_name": tool_name, "status": "unknown"}

        except Exception as e:
            logger.error(f"Error getting MCP tool info: {e}")
            return {"tool_name": tool_name, "error": str(e)}

    async def notify_workflow_completion(self, task_id: str, result: Dict[str, Any]):
        """Notify workflow service of task completion"""
        try:
            callback_info = self.workflow_callbacks.get(task_id)
            if not callback_info:
                return

            # Prepare notification payload
            notification = {
                "task_id": task_id,
                "workflow_id": callback_info["workflow_id"],
                "step_name": callback_info["step_name"],
                "result": result,
                "completed_at": asyncio.get_event_loop().time()
            }

            # Send to callback URL
            response = await self.http_client.post(
                callback_info["callback_url"],
                json=notification
            )

            if response.status_code == 200:
                logger.info(f"Successfully notified workflow completion: {task_id}")
                # Remove callback after successful notification
                del self.workflow_callbacks[task_id]
            else:
                logger.warning(f"Failed to notify workflow completion: {response.status_code}")

        except Exception as e:
            logger.error(f"Error notifying workflow completion: {e}")

    async def check_platform_health(self) -> bool:
        """Check health of platform services"""
        try:
            services = [
                (settings.workflow_engine_url, "/api/health"),
                (settings.mcp_gateway_url, "/api/health"),
                (settings.knowledge_base_url, "/api/health"),
                (settings.metadata_service_url, "/api/health"),
                (settings.auth_service_url, "/api/health")
            ]

            health_checks = []
            for base_url, health_path in services:
                health_checks.append(self._check_service_health(base_url, health_path))

            results = await asyncio.gather(*health_checks, return_exceptions=True)

            # Count healthy services
            healthy_count = sum(1 for result in results if result is True)
            total_count = len(services)

            logger.info(f"Platform health check: {healthy_count}/{total_count} services healthy")

            # Consider platform healthy if at least 50% of services are up
            return healthy_count >= total_count * 0.5

        except Exception as e:
            logger.error(f"Platform health check failed: {e}")
            return False

    async def _check_service_health(self, base_url: str, health_path: str) -> bool:
        """Check health of a single service"""
        try:
            response = await self.http_client.get(
                f"{base_url}{health_path}",
                timeout=5.0
            )
            return response.status_code == 200

        except Exception as e:
            logger.debug(f"Service health check failed for {base_url}: {e}")
            return False


# Create global integration service instance
platform_integrator = PlatformIntegrationService()
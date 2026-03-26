"""
服务客户端集合
统一管理各服务客户端
"""
import logging
import os
from typing import Dict, Any

from ..services.mcp_client import MCPClient
from ..services.workflow_client import WorkflowClient
from ..services.knowledge_client import KnowledgeClient
from ..services.dag_client import DAGClient

logger = logging.getLogger(__name__)


class ChatClient:
    """Chat Service客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        import httpx
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def process_message(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理消息"""
        try:
            # chat-service的API端点是 /api/v1/chat
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "metadata": context
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Chat service call failed: {e}")
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()


class ServiceClients:
    """各服务客户端集合"""
    
    def __init__(self):
        self.mcp_gateway_url = os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8001")
        self.workflow_engine_url = os.getenv("WORKFLOW_ENGINE_URL", "http://workflow-engine:8002")
        self.knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://knowledge-base:8004")
        self.dag_orchestrator_url = os.getenv("DAG_ORCHESTRATOR_URL", "http://dag-orchestrator:8009")
        self.chat_service_url = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8006")
        
        # 初始化客户端（延迟初始化，按需创建）
        self._mcp_client = None
        self._workflow_client = None
        self._knowledge_client = None
        self._dag_client = None
        self._chat_client = None
    
    @property
    def mcp_gateway(self) -> MCPClient:
        """MCP Gateway客户端"""
        if self._mcp_client is None:
            self._mcp_client = MCPClient()
        return self._mcp_client
    
    @property
    def workflow_engine(self) -> WorkflowClient:
        """Workflow Engine客户端"""
        if self._workflow_client is None:
            self._workflow_client = WorkflowClient()
        return self._workflow_client
    
    @property
    def knowledge_base(self) -> KnowledgeClient:
        """Knowledge Base客户端"""
        if self._knowledge_client is None:
            self._knowledge_client = KnowledgeClient()
        return self._knowledge_client
    
    @property
    def dag_orchestrator(self) -> DAGClient:
        """DAG Orchestrator客户端"""
        if self._dag_client is None:
            self._dag_client = DAGClient()
        return self._dag_client
    
    @property
    def chat_service(self) -> ChatClient:
        """Chat Service客户端"""
        if self._chat_client is None:
            self._chat_client = ChatClient(self.chat_service_url)
        return self._chat_client
    
    async def close_all(self):
        """关闭所有客户端连接"""
        if self._mcp_client:
            await self._mcp_client.close()
        if self._workflow_client:
            await self._workflow_client.close()
        if self._knowledge_client:
            await self._knowledge_client.close()
        if self._dag_client:
            await self._dag_client.close()
        if self._chat_client:
            await self._chat_client.close()


# 全局服务客户端实例
service_clients = ServiceClients()


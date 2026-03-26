"""
后端服务客户端
负责调用各个微服务
"""
import httpx
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class BackendClients:
    """后端服务客户端集合"""
    
    def __init__(self):
        # 从环境变量获取服务地址，支持Docker网络和本地开发
        self.mcp_gateway_url = os.getenv(
            "MCP_GATEWAY_URL", 
            "http://mcp-gateway:8001"
        )
        self.workflow_engine_url = os.getenv(
            "WORKFLOW_ENGINE_URL",
            "http://workflow-engine:8002"
        )
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.chat_service_url = os.getenv(
            "CHAT_SERVICE_URL",
            "http://chat-service:8005"
        )
        
        # HTTP客户端配置
        self.timeout = httpx.Timeout(300.0, connect=10.0)
        
    async def call_mcp_gateway(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用MCP网关执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            timeout: 超时时间（秒）
            
        Returns:
            工具执行结果
        """
        try:
            url = f"{self.mcp_gateway_url}/api/v1/tools/{tool_name}/execute"
            
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(
                    url,
                    json={"parameters": parameters}
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"MCP tool '{tool_name}' executed successfully")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP gateway HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"MCP tool execution failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"MCP gateway request error: {str(e)}")
            raise Exception(f"MCP gateway connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"MCP gateway unexpected error: {str(e)}")
            raise
    
    async def call_workflow_engine(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用工作流引擎执行工作流
        
        Args:
            workflow_id: 工作流ID或名称
            input_data: 输入数据
            timeout: 超时时间（秒）
            
        Returns:
            工作流执行结果
        """
        try:
            # 先尝试通过ID执行
            url = f"{self.workflow_engine_url}/api/v1/workflows/{workflow_id}/execute"
            
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(
                    url,
                    json={"input_data": input_data}
                )
                
                # 如果404，尝试通过名称查找
                if response.status_code == 404:
                    # 尝试通过名称执行
                    url = f"{self.workflow_engine_url}/api/v1/workflows/execute"
                    response = await client.post(
                        url,
                        json={
                            "workflow_name": workflow_id,
                            "input_data": input_data
                        }
                    )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Workflow '{workflow_id}' executed successfully")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Workflow engine HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Workflow execution failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Workflow engine request error: {str(e)}")
            raise Exception(f"Workflow engine connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Workflow engine unexpected error: {str(e)}")
            raise
    
    async def call_knowledge_base(
        self,
        action: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用知识库服务
        
        Args:
            action: 操作类型（search, retrieve等）
            parameters: 操作参数
            timeout: 超时时间（秒）
            
        Returns:
            知识库查询结果
        """
        try:
            if action == "search" or action == "semantic_search":
                url = f"{self.knowledge_base_url}/api/v1/knowledge/search"
            elif action == "retrieve":
                url = f"{self.knowledge_base_url}/api/v1/knowledge/retrieve"
            else:
                url = f"{self.knowledge_base_url}/api/v1/knowledge/{action}"
            
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(
                    url,
                    json=parameters
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Knowledge base action '{action}' executed successfully")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Knowledge base HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Knowledge base operation failed: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Knowledge base request error: {str(e)}")
            raise Exception(f"Knowledge base connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Knowledge base unexpected error: {str(e)}")
            raise
    
    async def call_agent_service(
        self,
        agent_action: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用智能体服务（如果存在）
        
        Args:
            agent_action: 智能体操作
            parameters: 操作参数
            timeout: 超时时间（秒）
            
        Returns:
            智能体执行结果
        """
        # TODO: 实现智能体服务调用
        # 目前工作流引擎可能包含智能体功能
        logger.warning(f"Agent service call not implemented: {agent_action}")
        raise NotImplementedError("Agent service integration not yet implemented")












































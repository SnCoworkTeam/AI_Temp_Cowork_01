"""
系统端点适配器
从MCP Gateway/服务注册中心适配系统端点为统一资源
"""
from typing import List, Dict, Any, Optional
import logging

try:
    from ..resource_model import SystemEndpointResource, ResourceType
    from ..resource_registry import ResourceRegistry
except ImportError:
    from resource_model import SystemEndpointResource, ResourceType
    from resource_registry import ResourceRegistry

logger = logging.getLogger(__name__)


class SystemEndpointAdapter:
    """系统端点适配器"""
    
    def __init__(self, registry: ResourceRegistry):
        """
        初始化系统端点适配器
        
        Args:
            registry: 资源注册表
        """
        self.registry = registry
        logger.info("系统端点适配器初始化完成")
    
    def adapt_from_mcp_server(
        self,
        server_info: Dict[str, Any]
    ) -> SystemEndpointResource:
        """
        从MCP服务器信息适配为系统端点资源
        
        Args:
            server_info: MCP服务器信息字典
            
        Returns:
            SystemEndpointResource: 系统端点资源对象
        """
        server_name = server_info.get("name", "unknown")
        server_url = server_info.get("url", server_info.get("endpoint", ""))
        
        resource = SystemEndpointResource(
            id=f"mcp:{server_name}",
            name=server_info.get("display_name", server_name),
            description=server_info.get("description", f"MCP服务器: {server_name}"),
            uri=f"mcp://{server_name}",
            endpoint_url=server_url,
            endpoint_type="mcp",
            protocol="mcp",
            authentication_required=server_info.get("auth_required", True),
            capabilities=self._extract_mcp_capabilities(server_info),
            service_metadata={
                "source": "mcp_gateway",
                "server_name": server_name,
                "tools": server_info.get("tools", []),
                "original_info": server_info
            }
        )
        
        return resource
    
    def adapt_from_api_endpoint(
        self,
        endpoint_info: Dict[str, Any]
    ) -> SystemEndpointResource:
        """
        从API端点信息适配为系统端点资源
        
        Args:
            endpoint_info: API端点信息字典
            
        Returns:
            SystemEndpointResource: 系统端点资源对象
        """
        endpoint_path = endpoint_info.get("path", endpoint_info.get("url", ""))
        method = endpoint_info.get("method", "GET").upper()
        
        resource = SystemEndpointResource(
            id=f"api:{endpoint_info.get('id', endpoint_path)}",
            name=endpoint_info.get("name", f"{method} {endpoint_path}"),
            description=endpoint_info.get("description", f"API端点: {method} {endpoint_path}"),
            uri=f"api://{endpoint_path}",
            endpoint_url=endpoint_path,
            endpoint_type="api",
            protocol=endpoint_info.get("protocol", "http"),
            authentication_required=endpoint_info.get("auth_required", True),
            capabilities=["invoke", "query"],
            service_metadata={
                "source": "api_gateway",
                "method": method,
                "parameters": endpoint_info.get("parameters", {}),
                "response_schema": endpoint_info.get("response_schema", {}),
                "original_info": endpoint_info
            }
        )
        
        return resource
    
    def adapt_from_service_registry(
        self,
        service_info: Dict[str, Any]
    ) -> SystemEndpointResource:
        """
        从服务注册中心适配为系统端点资源
        
        Args:
            service_info: 服务信息字典
            
        Returns:
            SystemEndpointResource: 系统端点资源对象
        """
        service_name = service_info.get("name", "unknown")
        service_url = service_info.get("url", service_info.get("endpoint", ""))
        
        resource = SystemEndpointResource(
            id=f"service:{service_name}",
            name=service_info.get("display_name", service_name),
            description=service_info.get("description", f"服务: {service_name}"),
            uri=f"service://{service_name}",
            endpoint_url=service_url,
            endpoint_type="service",
            protocol=service_info.get("protocol", "http"),
            authentication_required=service_info.get("auth_required", True),
            capabilities=["invoke", "query"],
            service_metadata={
                "source": "service_registry",
                "service_name": service_name,
                "version": service_info.get("version", "1.0.0"),
                "health_check_url": service_info.get("health_check", ""),
                "original_info": service_info
            }
        )
        
        return resource
    
    def register_system_endpoints(
        self,
        endpoints: List[Dict[str, Any]],
        source: str = "mcp"
    ) -> int:
        """
        批量注册系统端点
        
        Args:
            endpoints: 端点信息列表
            source: 数据源类型（"mcp" | "api" | "service"）
            
        Returns:
            int: 成功注册的数量
        """
        registered_count = 0
        
        for endpoint in endpoints:
            try:
                if source == "mcp":
                    resource = self.adapt_from_mcp_server(endpoint)
                elif source == "api":
                    resource = self.adapt_from_api_endpoint(endpoint)
                else:
                    resource = self.adapt_from_service_registry(endpoint)
                
                if self.registry.register(resource):
                    registered_count += 1
                    
            except Exception as e:
                logger.error(f"注册系统端点失败: {e}")
        
        logger.info(f"批量注册系统端点完成: {registered_count}/{len(endpoints)}")
        return registered_count
    
    def _extract_mcp_capabilities(self, server_info: Dict[str, Any]) -> List[str]:
        """从MCP服务器信息中提取能力列表"""
        capabilities = ["invoke", "query"]
        
        # 从工具列表中提取能力
        tools = server_info.get("tools", [])
        for tool in tools:
            tool_name = tool.get("name", "").lower()
            if "read" in tool_name or "get" in tool_name:
                capabilities.append("read")
            elif "write" in tool_name or "create" in tool_name:
                capabilities.append("write")
            elif "search" in tool_name:
                capabilities.append("search")
        
        # 去重
        return list(set(capabilities))


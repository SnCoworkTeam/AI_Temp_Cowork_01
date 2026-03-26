"""
SAP MCP客户端
用于通过MCP Gateway调用SAP OData服务
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
import os
import json

logger = logging.getLogger(__name__)


class SAPMCPClient:
    """SAP MCP客户端"""
    
    def __init__(
        self,
        mcp_gateway_url: Optional[str] = None,
        sap_mcp_server_url: Optional[str] = None
    ):
        """
        初始化SAP MCP客户端
        
        Args:
            mcp_gateway_url: MCP Gateway服务URL
            sap_mcp_server_url: SAP MCP服务器直接URL（可选，用于绕过Gateway）
        """
        self.mcp_gateway_url = mcp_gateway_url or os.getenv("MCP_GATEWAY_URL", "http://mcp-gateway:8001")
        self.sap_mcp_server_url = sap_mcp_server_url or os.getenv("SAP_MCP_SERVER_URL", "http://sap-mcp-server:3000")
        self.http_client = httpx.AsyncClient(timeout=60.0)
        self.sap_server_name = "sap-mcp-server"  # SAP MCP服务器名称
        self.use_direct = True  # 优先使用直接连接
    
    async def _discover_services_rest_api(self) -> List[Dict[str, Any]]:
        """使用REST API发现SAP OData服务"""
        try:
            # 使用REST API获取服务列表
            response = await self.http_client.get(
                f"{self.sap_mcp_server_url}/api/services",
                headers={"Accept": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success") and "services" in result:
                services = result["services"]
                logger.info(f"Discovered {len(services)} SAP OData services via REST API")
                return services
            else:
                logger.warning("REST API response format unexpected")
                return []
        except Exception as e:
            logger.error(f"Error discovering services via REST API: {e}", exc_info=True)
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    async def discover_services(self) -> List[Dict[str, Any]]:
        """
        发现所有SAP OData服务
        
        Returns:
            OData服务列表
        """
        # 优先使用REST API（更简单可靠）
        try:
            return await self._discover_services_rest_api()
        except Exception as e:
            logger.warning(f"REST API call failed: {e}, trying direct MCP")
            # 回退到直接MCP调用
            if self.use_direct:
                try:
                    return await self._discover_services_direct()
                except Exception as e2:
                    logger.warning(f"Direct SAP MCP call failed: {e2}, trying MCP Gateway")
        
        # 最后回退到MCP Gateway
        try:
            # 首先查找SAP相关的工具
            tools_response = await self.http_client.get(f"{self.mcp_gateway_url}/api/tools")
            tools_response.raise_for_status()
            tools_data = tools_response.json()
            
            # 查找get-service-report工具
            tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
            sap_tool = None
            for tool in tools:
                # 查找SAP相关的工具，优先查找get-service-report
                tool_name = tool.get("name", "")
                metadata = tool.get("metadata", {})
                if (tool_name == "get-service-report" or 
                    "get-service-report" in tool_name.lower() or
                    metadata.get("server") == self.sap_server_name):
                    sap_tool = tool
                    break
            
            if not sap_tool:
                logger.warning("SAP tool 'get-service-report' not found in MCP Gateway")
                # 再次尝试直接调用
                return await self._discover_services_direct()
            
            tool_name = sap_tool.get("name")
            
            # 通过MCP Gateway执行工具
            response = await self.http_client.post(
                f"{self.mcp_gateway_url}/api/tools/{tool_name}/execute",
                json={
                    "parameters": {
                        "detailLevel": "detailed"
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                output = result.get("output", {})
                # 处理不同的输出格式
                if isinstance(output, dict):
                    services = output.get("services", [])
                elif isinstance(output, list):
                    services = output
                else:
                    services = []
                logger.info(f"Discovered {len(services)} SAP OData services via MCP Gateway")
                return services
            else:
                logger.warning(f"Failed to discover services: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error discovering SAP services via MCP Gateway: {e}", exc_info=True)
            # 最后尝试直接调用
            return await self._discover_services_direct()
    
    async def _discover_services_direct(self) -> List[Dict[str, Any]]:
        """直接调用SAP MCP服务器发现服务"""
        session_id = None
        try:
            # 步骤1: 创建session
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "sap-metadata-agent",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_response = await self.http_client.post(
                f"{self.sap_mcp_server_url}/mcp",
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            # 从响应头获取session ID
            session_id = init_response.headers.get("Mcp-Session-Id") or init_response.headers.get("mcp-session-id")
            
            if not session_id:
                # 尝试从响应体获取
                try:
                    init_result = init_response.json()
                    session_id = init_result.get("sessionId") or init_result.get("result", {}).get("sessionId")
                except Exception as e:
                    logger.warning(f"Failed to parse init response: {e}, response text: {init_response.text[:200]}")
            
            if not session_id:
                logger.warning("Failed to get session ID from SAP MCP server")
                return []
            
            logger.debug(f"Created session: {session_id}")
            
            # 步骤2: 获取工具列表
            list_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            list_response = await self.http_client.post(
                f"{self.sap_mcp_server_url}/mcp",
                json=list_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id
                }
            )
            list_response.raise_for_status()
            
            # 解析响应（可能是SSE格式或JSON格式）
            list_result = None
            response_text = list_response.text
            
            # 检查是否是SSE格式
            if "data:" in response_text or response_text.startswith("event:"):
                # SSE格式：标准格式是 event: message\ndata: {json}\n\n
                # JSON可能跨多行，需要合并所有data:行之后的内容
                lines = response_text.strip().split("\n")
                json_str = ""
                in_data_block = False
                
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith("data:"):
                        # 开始data块
                        in_data_block = True
                        json_str = line[5:].strip()  # 移除"data:"前缀，保留原始空格
                    elif in_data_block:
                        if line_stripped == "":
                            # 空行可能表示data块结束，尝试解析
                            if json_str:
                                try:
                                    list_result = json.loads(json_str)
                                    break
                                except:
                                    # 可能还没结束，继续
                                    pass
                        else:
                            # 继续累积JSON内容
                            json_str += "\n" + line
                
                # 如果还没解析成功，尝试解析累积的JSON
                if not list_result and json_str:
                    try:
                        list_result = json.loads(json_str)
                    except Exception as e:
                        logger.debug(f"Failed to parse accumulated JSON: {e}, preview: {json_str[:200]}")
                        # 尝试只解析第一行（如果JSON在一行内）
                        first_data_line = None
                        for line in lines:
                            if line.strip().startswith("data:"):
                                first_data_line = line[5:].strip()
                                break
                        if first_data_line:
                            try:
                                list_result = json.loads(first_data_line)
                            except:
                                pass
            else:
                # JSON格式
                try:
                    list_result = list_response.json()
                except Exception as e:
                    logger.error(f"Failed to parse tools list response: {e}, response text: {response_text[:200]}")
                    return []
            
            if not list_result:
                logger.error(f"Failed to parse tools list response, response preview: {response_text[:500]}")
                return []
            
            logger.debug(f"Tools list response keys: {list(list_result.keys()) if isinstance(list_result, dict) else 'not dict'}")
            
            # 查找get-service-report工具
            tools = []
            if "result" in list_result:
                result_data = list_result["result"]
                if isinstance(result_data, dict):
                    tools = result_data.get("tools", [])
                elif isinstance(result_data, list):
                    tools = result_data
            elif "tools" in list_result:
                tools = list_result["tools"]
            
            logger.debug(f"Found {len(tools)} tools")
            tool_found = any(t.get("name") == "get-service-report" for t in tools)
            
            # 如果没有找到get-service-report，尝试使用search-sap-services
            if not tool_found:
                tool_found = any(t.get("name") == "search-sap-services" for t in tools)
                if tool_found:
                    logger.info("Using search-sap-services instead of get-service-report")
            
            if not tool_found:
                logger.warning("get-service-report or search-sap-services tool not found in SAP MCP server")
                return []
            
            # 确定使用的工具名称
            tool_name = "get-service-report"
            if not any(t.get("name") == "get-service-report" for t in tools):
                tool_name = "search-sap-services"
            
            # 步骤3: 调用工具
            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {
                        "detailLevel": "detailed" if tool_name == "get-service-report" else {}
                    }
                }
            }
            
            call_response = await self.http_client.post(
                f"{self.sap_mcp_server_url}/mcp",
                json=call_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id
                }
            )
            call_response.raise_for_status()
            
            # 解析响应（可能是SSE格式或JSON格式）
            call_result = None
            response_text = call_response.text
            
            # 检查是否是SSE格式
            if "data:" in response_text or response_text.startswith("event:"):
                # SSE格式：标准格式是 event: message\ndata: {json}\n\n
                lines = response_text.strip().split("\n")
                json_parts = []
                current_data = None
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.startswith("data:"):
                        json_str = line[5:].strip()  # 移除"data:"前缀
                        if json_str:
                            # 检查JSON是否完整（以}结尾）
                            if json_str.endswith("}"):
                                try:
                                    parsed = json.loads(json_str)
                                    json_parts.append(parsed)
                                    current_data = parsed
                                except:
                                    # JSON可能跨多行，继续累积
                                    if current_data is None:
                                        current_data = json_str
                                    else:
                                        current_data += json_str
                            else:
                                # JSON跨多行，累积
                                if current_data is None:
                                    current_data = json_str
                                else:
                                    current_data += json_str
                    elif line == "" and current_data:
                        # 空行表示一个SSE消息结束，尝试解析累积的数据
                        if isinstance(current_data, str):
                            try:
                                parsed = json.loads(current_data)
                                json_parts.append(parsed)
                                current_data = None
                            except:
                                pass
                
                # 处理最后累积的数据
                if isinstance(current_data, str):
                    try:
                        parsed = json.loads(current_data)
                        json_parts.append(parsed)
                    except:
                        pass
                
                # 从解析的JSON中找到包含result的
                for parsed in reversed(json_parts):
                    if isinstance(parsed, dict) and "result" in parsed:
                        call_result = parsed
                        break
                
                # 如果还没找到，使用最后一个解析的结果
                if not call_result and json_parts:
                    call_result = json_parts[-1]
            else:
                # JSON格式
                try:
                    call_result = call_response.json()
                except Exception as e:
                    logger.error(f"Failed to parse tool call response: {e}, response text: {response_text[:500]}")
                    return []
            
            if not call_result:
                logger.error("Failed to parse tool call response")
                return []
            
            logger.debug(f"Tool call response keys: {list(call_result.keys()) if isinstance(call_result, dict) else 'not dict'}")
            
            if call_result.get("result"):
                # MCP协议返回格式
                result_data = call_result.get("result", {})
                content = result_data.get("content", [])
                
                if content and len(content) > 0:
                    # 解析内容
                    import json
                    content_item = content[0]
                    if isinstance(content_item, dict):
                        if "text" in content_item:
                            try:
                                text_content = content_item["text"]
                                if isinstance(text_content, str):
                                    services_data = json.loads(text_content)
                                else:
                                    services_data = text_content
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse text content as JSON: {e}, content: {str(content_item.get('text', ''))[:200]}")
                                services_data = {"services": []}
                        elif "data" in content_item:
                            services_data = content_item["data"]
                        else:
                            services_data = content_item
                        
                        if isinstance(services_data, dict):
                            services = services_data.get("services", [])
                        elif isinstance(services_data, list):
                            services = services_data
                        else:
                            services = []
                        
                        logger.info(f"Discovered {len(services)} SAP OData services via direct MCP")
                        return services
                else:
                    # 尝试直接从result获取
                    if isinstance(result_data, dict) and "services" in result_data:
                        services = result_data["services"]
                        logger.info(f"Discovered {len(services)} SAP OData services via direct MCP (from result)")
                        return services
            
            logger.warning("No services found in MCP response")
            return []
        except Exception as e:
            logger.error(f"Error in direct SAP MCP call: {e}", exc_info=True)
            # 返回空列表而不是抛出异常，允许继续执行
            return []
        finally:
            # 清理session（如果创建了）
            if session_id:
                try:
                    await self.http_client.delete(
                        f"{self.sap_mcp_server_url}/mcp",
                        headers={"mcp-session-id": session_id}
                    )
                except:
                    pass
    
    async def get_entity_structure(
        self,
        service_id: str,
        entity_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取实体结构信息
        
        Args:
            service_id: 服务ID
            entity_name: 实体名称
            
        Returns:
            实体结构信息
        """
        try:
            # 查找get-entity-structure工具
            tools_response = await self.http_client.get(f"{self.mcp_gateway_url}/api/tools")
            tools_response.raise_for_status()
            tools_data = tools_response.json()
            
            tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
            sap_tool = None
            for tool in tools:
                tool_name = tool.get("name", "")
                metadata = tool.get("metadata", {})
                if (tool_name == "get-entity-structure" or 
                    "get-entity-structure" in tool_name.lower() or
                    metadata.get("server") == self.sap_server_name):
                    sap_tool = tool
                    break
            
            if not sap_tool:
                logger.warning("SAP tool 'get-entity-structure' not found")
                return None
            
            tool_name = sap_tool.get("name")
            
            # 执行工具
            response = await self.http_client.post(
                f"{self.mcp_gateway_url}/api/tools/{tool_name}/execute",
                json={
                    "parameters": {
                        "serviceId": service_id,
                        "entityName": entity_name
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                return result.get("output")
            else:
                logger.warning(f"Failed to get entity structure: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error getting entity structure: {e}", exc_info=True)
            return None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取SAP MCP服务器提供的所有工具
        
        Returns:
            工具列表
        """
        try:
            response = await self.http_client.get(f"{self.base_url}/api/tools")
            response.raise_for_status()
            tools_data = response.json()
            
            # 过滤SAP相关的工具
            tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
            sap_tools = [
                tool for tool in tools
                if tool.get("metadata", {}).get("server") == self.sap_server_name
            ]
            
            return sap_tools
        except Exception as e:
            logger.error(f"Error listing SAP tools: {e}", exc_info=True)
            return []
    
    async def get_service_metadata(self, service_id: str) -> Optional[str]:
        """
        获取OData服务的$metadata XML
        
        Args:
            service_id: OData服务ID
            
        Returns:
            $metadata XML字符串，失败返回None
        """
        try:
            # 方法1: 尝试从服务URL直接获取$metadata
            # 首先获取服务信息
            services = await self.discover_services()
            service_info = None
            for service in services:
                if service.get("serviceId") == service_id or service.get("name") == service_id:
                    service_info = service
                    break
            
            if service_info:
                service_url = service_info.get("url") or service_info.get("serviceUrl")
                if service_url:
                    # 确保URL以/结尾
                    if not service_url.endswith("/"):
                        service_url += "/"
                    metadata_url = f"{service_url}$metadata"
                    
                    try:
                        response = await self.http_client.get(metadata_url, timeout=30.0)
                        response.raise_for_status()
                        return response.text
                    except Exception as e:
                        logger.debug(f"Failed to get metadata from URL {metadata_url}: {e}")
            
            # 方法2: 尝试通过MCP工具获取
            try:
                tools_response = await self.http_client.get(f"{self.mcp_gateway_url}/api/tools")
                tools_response.raise_for_status()
                tools_data = tools_response.json()
                
                tools = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
                metadata_tool = None
                for tool in tools:
                    tool_name = tool.get("name", "")
                    if "metadata" in tool_name.lower() or "get-metadata" in tool_name.lower():
                        metadata_tool = tool
                        break
                
                if metadata_tool:
                    tool_name = metadata_tool.get("name")
                    response = await self.http_client.post(
                        f"{self.mcp_gateway_url}/api/tools/{tool_name}/execute",
                        json={
                            "parameters": {
                                "serviceId": service_id
                            }
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    if result.get("success"):
                        output = result.get("output", {})
                        if isinstance(output, str):
                            return output
                        elif isinstance(output, dict):
                            return output.get("metadata") or output.get("xml")
            except Exception as e:
                logger.debug(f"Failed to get metadata via MCP tool: {e}")
            
            logger.warning(f"Could not retrieve metadata for service: {service_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting service metadata for {service_id}: {e}", exc_info=True)
            return None


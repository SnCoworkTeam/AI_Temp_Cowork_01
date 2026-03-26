"""
MCP工具注册表
提供工具注册、发现和执行功能
"""
from typing import Dict, List, Any, Optional, Callable, Tuple
import logging
import asyncio
from datetime import datetime
import json
import re

from ..models.tool_models import (
    ToolDefinition,
    ToolStatus,
    ToolExecutionRequest,
    ToolExecutionResponse
)
from ..core.mcp_client import MCPClient, MCPConnectionPool, MCPConnectionError, MCPProtocolError
from typing import Union

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """工具执行错误"""
    def __init__(self, message: str, tool_name: str, error_code: str = "EXECUTION_ERROR"):
        self.message = message
        self.tool_name = tool_name
        self.error_code = error_code
        super().__init__(self.message)


class ToolRegistry:
    """MCP工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._mcp_clients: Dict[str, Union[MCPClient, Any]] = {}  # MCP客户端映射（支持WebSocket和HTTP）
        self._mcp_connection_pool = MCPConnectionPool()  # MCP连接池
        self._tool_sources: Dict[str, str] = {}  # 工具来源映射（tool_name -> source）
        self._auto_refresh_task: Optional[asyncio.Task] = None
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具（不包含SAP工具，SAP工具由专门的sap_odata_agent处理）"""
        # 注意：SAP工具不再在这里注册，应该由sap_odata_agent直接连接SAP MCP服务器
        
        # 注册知识库工具
        try:
            from .knowledge_search_tool import KNOWLEDGE_SEARCH_TOOL, execute_knowledge_search
            self.register_tool(KNOWLEDGE_SEARCH_TOOL, executor=execute_knowledge_search)
        except Exception as e:
            logger.warning(f"Failed to register knowledge_search tool: {str(e)}")
        
        try:
            from .document_management_tool import DOCUMENT_MANAGEMENT_TOOL, execute_document_management
            self.register_tool(DOCUMENT_MANAGEMENT_TOOL, executor=execute_document_management)
        except Exception as e:
            logger.warning(f"Failed to register document_management tool: {str(e)}")
        
        try:
            from .knowledge_graph_tool import KNOWLEDGE_GRAPH_TOOL, execute_knowledge_graph
            self.register_tool(KNOWLEDGE_GRAPH_TOOL, executor=execute_knowledge_graph)
        except Exception as e:
            logger.warning(f"Failed to register knowledge_graph tool: {str(e)}")
        
        # 注册邮件发送工具
        try:
            from .email_tool import SEND_EMAIL_TOOL, execute_send_email
            self.register_tool(SEND_EMAIL_TOOL, executor=execute_send_email)
        except Exception as e:
            logger.warning(f"Failed to register send_email tool: {str(e)}")
        
        # 注册SAP ERP表查询工具
        try:
            from .sap_erp_table_tool import SAP_ERP_TABLE_TOOL, execute_query_sap_table
            self.register_tool(SAP_ERP_TABLE_TOOL, executor=execute_query_sap_table)
        except Exception as e:
            logger.warning(f"Failed to register sap_erp_table_query tool: {str(e)}")

        # 注册文件生成工具
        try:
            from .ppt_generator_tool import PPTGeneratorTool
            ppt_def = ToolDefinition(
                name=PPTGeneratorTool.name,
                description=PPTGeneratorTool.description,
                version=PPTGeneratorTool.version,
                tool_type="function",
                parameters={},
                required_parameters=[],
                returns={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "download_url": {"type": ["string", "null"]},
                    },
                },
                metadata={"category": "document", "service": "mcp-gateway"},
            )
            self.register_tool(ppt_def, executor=PPTGeneratorTool().execute)
        except Exception as e:
            logger.warning(f"Failed to register generate_ppt tool: {str(e)}")

        try:
            from .docx_generator_tool import DOCXGeneratorTool
            docx_def = ToolDefinition(
                name=DOCXGeneratorTool.name,
                description=DOCXGeneratorTool.description,
                version=DOCXGeneratorTool.version,
                tool_type="function",
                parameters={},
                required_parameters=[],
                returns={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "download_url": {"type": ["string", "null"]},
                    },
                },
                metadata={"category": "document", "service": "mcp-gateway"},
            )
            self.register_tool(docx_def, executor=DOCXGeneratorTool().execute)
        except Exception as e:
            logger.warning(f"Failed to register generate_docx tool: {str(e)}")

        try:
            from .excel_generator_tool import ExcelGeneratorTool
            xls_def = ToolDefinition(
                name=ExcelGeneratorTool.name,
                description=ExcelGeneratorTool.description,
                version=ExcelGeneratorTool.version,
                tool_type="function",
                parameters={},
                required_parameters=[],
                returns={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "download_url": {"type": ["string", "null"]},
                    },
                },
                metadata={"category": "document", "service": "mcp-gateway"},
            )
            self.register_tool(xls_def, executor=ExcelGeneratorTool().execute)
        except Exception as e:
            logger.warning(f"Failed to register generate_excel tool: {str(e)}")
    
    async def _execute_sap_query(self, parameters: Dict[str, Any]) -> Any:
        """执行SAP查询 - 调用SAP MCP服务器的execute-entity-operation工具"""
        table = parameters.get("table")
        query = parameters.get("query", "")
        
        logger.info(f"Executing SAP query: table={table}, query={query}")
        
        # 尝试从MCP客户端池获取SAP MCP服务器客户端
        sap_client_name = "sap-mcp-server"
        logger.info(f"Looking for MCP client '{sap_client_name}'")
        logger.info(f"_mcp_clients keys: {list(self._mcp_clients.keys())}")
        
        client = self._mcp_clients.get(sap_client_name)
        if not client:
            logger.info(f"Client not in _mcp_clients, trying connection pool...")
            # 尝试从连接池获取
            client = self._mcp_connection_pool.get_client(sap_client_name)
            if client:
                logger.info(f"Found client in connection pool, adding to _mcp_clients")
                self._mcp_clients[sap_client_name] = client
        
        if not client:
            logger.error(f"SAP MCP client '{sap_client_name}' not found")
            # 尝试列出所有可用的客户端
            available_clients = list(self._mcp_clients.keys())
            # 尝试从连接池获取所有客户端名称（通过尝试已知的服务器名称）
            for known_name in ["sap-mcp-server"]:
                pool_client = self._mcp_connection_pool.get_client(known_name)
                if pool_client:
                    logger.info(f"Found client '{known_name}' in connection pool")
                    if known_name not in available_clients:
                        available_clients.append(known_name)
                        # 同时添加到 _mcp_clients 以便后续使用
                        self._mcp_clients[known_name] = pool_client
            logger.info(f"Available MCP clients: {available_clients}")
            
            # 如果仍然没有客户端，尝试重新初始化
            if not client and available_clients:
                logger.warning(f"Client was in pool but not accessible, trying to re-add to _mcp_clients")
                client = self._mcp_clients.get(sap_client_name)
            
            if not client:
                # 提供更详细的错误信息
                error_msg = (
                    f"SAP MCP server not available. "
                    f"Please ensure SAP MCP server is running and connected. "
                    f"Available clients: {available_clients if available_clients else 'none'}"
                )
                raise ToolExecutionError(
                    error_msg,
                    "sap_query",
                    "MCP_CLIENT_NOT_FOUND"
                )
        
        # 构建execute-entity-operation工具的参数
        # 需要找到包含该实体的服务
        service_id = None
        entity_name = table
        
        # 首先尝试搜索服务，找到包含该实体的服务
        try:
            logger.info(f"Searching for services containing entity '{table}'")
            search_result = await client.execute_tool(
                "search-sap-services",
                {"query": "sales order", "limit": 20}  # 搜索销售订单相关服务
            )
            logger.info(f"Service search result type: {type(search_result)}")
            logger.info(f"Service search result (first 500 chars): {str(search_result)[:500]}")
            
            # 解析搜索结果，找到包含该实体的服务
            if isinstance(search_result, str):
                # 如果是字符串，尝试解析服务名称
                import re
                # 查找所有可能的服务ID
                service_matches = re.findall(r'(\w+[Ss]ales[Oo]rder\w*[Ss]rv|\w+_SALES_ORDER\w*)', search_result, re.IGNORECASE)
                if service_matches:
                    # 尝试每个服务，看是否包含目标实体
                    for svc_id in service_matches[:5]:  # 只尝试前5个
                        try:
                            logger.info(f"Trying service: {svc_id}")
                            entities_result = await client.execute_tool(
                                "discover-service-entities",
                                {"serviceId": svc_id}
                            )
                            if isinstance(entities_result, str) and table in entities_result:
                                service_id = svc_id
                                logger.info(f"✅ Found service {svc_id} containing entity {table}")
                                break
                        except Exception as e:
                            logger.debug(f"Service {svc_id} check failed: {e}")
                            continue
            elif isinstance(search_result, dict):
                # 如果是字典，查找服务列表
                services = search_result.get("services", []) or search_result.get("results", [])
                for svc in services[:10]:  # 只检查前10个服务
                    if isinstance(svc, dict):
                        svc_id = svc.get("id") or svc.get("serviceId") or svc.get("name")
                        if svc_id:
                            try:
                                logger.info(f"Checking service: {svc_id}")
                                entities_result = await client.execute_tool(
                                    "discover-service-entities",
                                    {"serviceId": svc_id}
                                )
                                if isinstance(entities_result, str) and table in entities_result:
                                    service_id = svc_id
                                    logger.info(f"✅ Found service {svc_id} containing entity {table}")
                                    break
                            except Exception as e:
                                logger.debug(f"Service {svc_id} check failed: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Failed to search services: {e}")
        
        # 如果搜索失败，尝试常见的服务名称
        if not service_id:
            logger.info(f"Trying common service names for entity '{table}'")
            # 根据实体名称推断可能的服务
            common_services = []
            if "SalesOrder" in table or "salesorder" in table.lower():
                common_services = [
                    "API_SALES_ORDER_SRV",
                    "ZAPI_SALES_ORDER_SRV", 
                    "C_SALESORDER_SRV",
                    "SALES_ORDER_SRV",
                    "API_SALESORDER_SRV"
                ]
            else:
                # 通用服务搜索
                common_services = [
                    f"API_{table}_SRV",
                    f"ZAPI_{table}_SRV",
                    f"C_{table}_SRV"
                ]
            
            for svc_id in common_services:
                try:
                    logger.info(f"Trying service: {svc_id}")
                    entities_result = await client.execute_tool(
                        "discover-service-entities",
                        {"serviceId": svc_id}
                    )
                    if isinstance(entities_result, str) and table in entities_result:
                        service_id = svc_id
                        logger.info(f"✅ Found service {svc_id} containing entity {table}")
                        break
                except Exception as e:
                    logger.debug(f"Service {svc_id} not found: {e}")
                    continue
        
        # 如果仍然没有找到，尝试不指定serviceId，让SAP MCP服务器在所有服务中搜索
        if not service_id:
            logger.warning(f"Could not find specific service for entity {table}, will let SAP MCP server search all services")
        
        execute_params = {
            "entityName": entity_name,
            "operation": "read",
            "filters": {}
        }
        
        # 只有在找到服务ID时才添加
        if service_id:
            execute_params["serviceId"] = service_id
            logger.info(f"Using service: {service_id}")
        else:
            logger.info(f"No specific service found, SAP MCP server will search all services for entity {entity_name}")
        
        # 如果有查询条件，尝试解析为OData查询表达式
        if query:
            # 检查是否是有效的OData查询表达式
            import re
            # 简单的启发式检查：如果包含OData操作符或字段名模式，才认为是有效的查询表达式
            odata_patterns = [
                r'\w+\s+(eq|ne|gt|ge|lt|le|contains|startswith|endswith)\s+',  # 字段名 操作符
                r'\$filter=',  # 明确的$filter标记
                r'and\s+|\s+or\s+',  # 逻辑操作符
                r'\(.*\)',  # 括号表达式
            ]
            
            is_valid_odata = any(re.search(pattern, query, re.IGNORECASE) for pattern in odata_patterns)
            
            if is_valid_odata:
                logger.info(f"Query appears to be valid OData expression, using as $filter: {query}")
                execute_params["filters"] = {"$filter": query}
            else:
                # 尝试解析自然语言中的日期条件
                filter_conditions = []
                
                # 解析月份条件（如"9月份"、"9月"、"September"等）
                month_patterns = [
                    (r'(\d{1,2})月份?', lambda m: int(m.group(1))),  # "9月份"、"9月"
                    (r'(\d{1,2})月', lambda m: int(m.group(1))),  # "9月"
                    (r'(\d{4})年(\d{1,2})月份?', lambda m: (int(m.group(1)), int(m.group(2)))),  # "2024年9月份"
                ]
                
                current_year = datetime.now().year
                month_found = None
                year_found = None
                
                for pattern, extractor in month_patterns:
                    match = re.search(pattern, query)
                    if match:
                        result = extractor(match)
                        if isinstance(result, tuple):
                            year_found, month_found = result
                        else:
                            month_found = result
                        break
                
                if month_found:
                    # 构建日期范围过滤条件
                    # 假设日期字段可能是：SalesOrderDate, OrderDate, CreationDate, DocumentDate
                    if year_found is None:
                        year_found = current_year
                    
                    # 计算月份的开始和结束日期
                    from datetime import date
                    start_date = date(year_found, month_found, 1).strftime('%Y-%m-%d')
                    # 计算月份的最后一天（下个月的第一天）
                    if month_found == 12:
                        end_date = date(year_found + 1, 1, 1).strftime('%Y-%m-%d')
                    else:
                        end_date = date(year_found, month_found + 1, 1).strftime('%Y-%m-%d')
                    
                    # 构建OData过滤条件：日期 >= 开始日期 and 日期 < 结束日期
                    # 尝试多个可能的日期字段名
                    date_fields = ['SalesOrderDate', 'OrderDate', 'CreationDate', 'DocumentDate', 'SalesOrderDate']
                    date_filter_parts = []
                    for date_field in date_fields:
                        # 使用 ge (greater than or equal) 和 lt (less than)
                        date_filter_parts.append(
                            f"({date_field} ge datetime'{start_date}T00:00:00' and {date_field} lt datetime'{end_date}T00:00:00')"
                        )
                    
                    # 使用 or 连接多个可能的日期字段
                    if date_filter_parts:
                        date_filter = ' or '.join(date_filter_parts)
                        filter_conditions.append(f"({date_filter})")
                        logger.info(f"Parsed date condition: {year_found}年{month_found}月 -> {start_date} to {end_date}")
                
                # 如果有解析出的过滤条件，添加到filters
                if filter_conditions:
                    filter_expression = ' and '.join(filter_conditions)
                    execute_params["filters"] = {"$filter": filter_expression}
                    logger.info(f"Generated OData filter: {filter_expression}")
                else:
                    # 自然语言查询，忽略它，只查询所有数据
                    logger.info(f"Query appears to be natural language without parseable conditions, ignoring: {query}")
                    logger.info("Will query all records without filter")
        
        logger.info(f"Calling execute-entity-operation with params: {execute_params}")
        
        # 检查客户端连接状态，如果未连接则尝试重连
        if hasattr(client, 'connected') and not client.connected:
            logger.warning(f"SAP MCP client '{sap_client_name}' is not connected, attempting to reconnect...")
            try:
                if hasattr(client, 'connect'):
                    connected = await client.connect()
                    if not connected:
                        logger.error(f"Failed to reconnect to SAP MCP server '{sap_client_name}'")
                        raise ToolExecutionError(
                            f"SAP MCP server '{sap_client_name}' is not connected and reconnection failed",
                            "sap_query",
                            "MCP_CLIENT_NOT_CONNECTED"
                        )
                    logger.info(f"Successfully reconnected to SAP MCP server '{sap_client_name}'")
            except Exception as reconnect_error:
                logger.error(f"Error during reconnection: {reconnect_error}")
                raise ToolExecutionError(
                    f"Failed to reconnect to SAP MCP server: {str(reconnect_error)}",
                    "sap_query",
                    "RECONNECTION_ERROR"
                )
        
        try:
            # 调用SAP MCP服务器的execute-entity-operation工具
            result = await client.execute_tool(
                "execute-entity-operation",
                execute_params,
                timeout=60  # SAP查询可能需要更长时间
            )
            
            logger.info(f"SAP query executed successfully, result type: {type(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute SAP query: {e}", exc_info=True)
            raise ToolExecutionError(
                f"SAP query execution failed: {str(e)}",
                "sap_query",
                "EXECUTION_ERROR"
            )
    
    def _is_sap_odata_tool(self, tool: Union[ToolDefinition, Dict[str, Any]]) -> bool:
        """
        判断工具是否为SAP OData工具（应该由sap_odata_agent处理）
        
        Args:
            tool: 工具定义（ToolDefinition对象或字典）
            
        Returns:
            是否为SAP OData工具
        """
        # 处理ToolDefinition对象
        if isinstance(tool, ToolDefinition):
            tool_name = tool.name
            description = tool.description.lower() if tool.description else ""
            metadata = tool.metadata or {}
        else:
            # 处理字典格式
            tool_name = tool.get("name", "")
            description = tool.get("description", "").lower()
            metadata = tool.get("metadata", {})
        
        # 检查是否是SAP OData MCP服务的工具
        is_sap = (
            # 核心SAP OData工具
            tool_name in [
                "search-sap-services",
                "discover-service-entities",
                "get-entity-schema",
                "execute-entity-operation"
            ] or
            # 基于元数据判断
            metadata.get("source") == "sap-odata-mcp-server" or
            metadata.get("service_type") == "sap_odata" or
            metadata.get("category") == "sap" or
            metadata.get("server") == "sap-mcp-server" or
            # CRUD工具（基于元数据）
            (metadata.get("operation") in ["read", "create", "update", "delete"] and
             metadata.get("sap_service")) or
            # 工具名称模式（r-/c-/u-/d-开头的SAP工具）
            (tool_name.startswith(("r-", "c-", "u-", "d-")) and
             ("sap" in description or "odata" in description)) or
            # 描述中包含SAP OData关键词
            ("sap" in description and "odata" in description) or
            # 工具来源是SAP MCP服务器
            (isinstance(tool, dict) and tool.get("source", "").startswith("mcp:sap-"))
        )
        
        return is_sap
    
    def register_tool(
        self,
        tool_def: ToolDefinition,
        executor: Optional[Callable] = None,
        overwrite: bool = False,
        source: Optional[str] = None
    ) -> bool:
        """
        注册工具
        
        Args:
            tool_def: 工具定义
            executor: 工具执行器函数（可选）
            overwrite: 是否覆盖已存在的工具
        
        Returns:
            是否注册成功
        
        Raises:
            ValueError: 如果工具定义无效或已存在且不允许覆盖
        """
        tool_name = tool_def.name
        
        # 检查工具是否已存在
        if tool_name in self._tools and not overwrite:
            raise ValueError(f"Tool '{tool_name}' already exists. Use overwrite=True to replace it.")
        
        # 验证工具定义
        try:
            # Pydantic会自动验证
            tool_def.model_validate(tool_def.model_dump())
        except Exception as e:
            raise ValueError(f"Invalid tool definition: {str(e)}")
        
        # 注册工具
        self._tools[tool_name] = tool_def
        
        # 注册执行器
        if executor:
            self._executors[tool_name] = executor
        elif tool_name not in self._executors:
            # 如果没有提供执行器，使用默认实现
            logger.warning(f"No executor provided for tool '{tool_name}', using default")
            self._executors[tool_name] = self._default_executor
        
        # 保存元数据
        self._tool_metadata[tool_name] = {
            "registered_at": datetime.now().isoformat(),
            "status": tool_def.status.value
        }
        
        # 保存工具来源
        if source:
            self._tool_sources[tool_name] = source
            if source.startswith("mcp:"):
                # 如果是MCP工具，更新metadata
                if not tool_def.metadata:
                    tool_def.metadata = {}
                tool_def.metadata["source"] = source
        
        logger.info(f"Registered tool: {tool_name} (version: {tool_def.version}, source: {source or 'local'})")
        return True
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
        
        Returns:
            是否注销成功
        """
        if tool_name not in self._tools:
            return False
        
        del self._tools[tool_name]
        if tool_name in self._executors:
            del self._executors[tool_name]
        if tool_name in self._tool_metadata:
            del self._tool_metadata[tool_name]
        
        logger.info(f"Unregistered tool: {tool_name}")
        return True
    
    def list_tools(
        self,
        status: Optional[ToolStatus] = None,
        tool_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出所有工具
        
        Args:
            status: 按状态过滤
            tool_type: 按工具类型过滤
            page: 页码
            page_size: 每页大小
        
        Returns:
            工具列表
        """
        tools = list(self._tools.values())
        
        # 过滤
        if status:
            tools = [t for t in tools if t.status == status]
        if tool_type:
            tools = [t for t in tools if t.tool_type.value == tool_type]
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        tools = tools[start:end]
        
        # 转换为字典并添加元数据
        result = []
        for tool in tools:
            tool_dict = tool.model_dump()
            if tool.name in self._tool_metadata:
                tool_dict["registered_at"] = self._tool_metadata[tool.name].get("registered_at")
            result.append(tool_dict)
        
        return result
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
        
        Returns:
            工具信息字典，如果不存在则返回None
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return None
        
        tool_dict = tool.model_dump()
        if tool_name in self._tool_metadata:
            tool_dict.update(self._tool_metadata[tool_name])
        
        return tool_dict
    
    def validate_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        验证工具参数
        
        Args:
            tool_name: 工具名称
            parameters: 参数字典
        
        Returns:
            (是否有效, 错误消息)
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"
        
        # 检查必需参数
        for req_param in tool.required_parameters:
            if req_param not in parameters:
                return False, f"Missing required parameter: {req_param}"
        
        # 获取参数schema（JSON Schema格式）
        param_schema = tool.parameters
        if isinstance(param_schema, dict) and "properties" in param_schema:
            # JSON Schema格式：参数在properties中
            properties = param_schema.get("properties", {})
            required_params = param_schema.get("required", tool.required_parameters)
        else:
            # 直接参数字典格式
            properties = param_schema if isinstance(param_schema, dict) else {}
            required_params = tool.required_parameters
        
        # 检查未知参数
        for param_name in parameters:
            if param_name not in properties:
                # 允许额外参数，但记录警告
                logger.debug(f"Unknown parameter '{param_name}' for tool '{tool_name}'")
        
        # 详细的类型和范围验证
        for param_name, param_value in parameters.items():
            if param_name in properties:
                param_def = properties[param_name]
                validation_result = self._validate_parameter_value(param_name, param_value, param_def)
                if not validation_result[0]:
                    return validation_result
        
        return True, None
    
    def _validate_parameter_value(
        self,
        param_name: str,
        value: Any,
        schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        验证单个参数值
        
        Args:
            param_name: 参数名称
            value: 参数值
            schema: 参数schema定义
        
        Returns:
            (是否有效, 错误消息)
        """
        # 类型检查（支持联合类型，如 ["string", "array"]）
        expected_type = schema.get("type")
        if expected_type:
            type_valid = False
            
            # 处理联合类型（数组形式）
            allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
            
            for allowed_type in allowed_types:
                if allowed_type == "string" and isinstance(value, str):
                    type_valid = True
                    break
                elif allowed_type == "integer" and isinstance(value, int):
                    type_valid = True
                    break
                elif allowed_type == "number" and isinstance(value, (int, float)):
                    type_valid = True
                    break
                elif allowed_type == "boolean" and isinstance(value, bool):
                    type_valid = True
                    break
                elif allowed_type == "array" and isinstance(value, list):
                    type_valid = True
                    break
                elif allowed_type == "object" and isinstance(value, dict):
                    type_valid = True
                    break
            
            if not type_valid:
                type_str = str(allowed_types) if isinstance(expected_type, list) else expected_type
                return False, f"Parameter '{param_name}' must be of type '{type_str}', got '{type(value).__name__}'"
        
        # 字符串验证
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                return False, f"Parameter '{param_name}' must be at least {schema['minLength']} characters"
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                return False, f"Parameter '{param_name}' must be at most {schema['maxLength']} characters"
            if "pattern" in schema:
                pattern = schema["pattern"]
                if not re.match(pattern, value):
                    return False, f"Parameter '{param_name}' does not match pattern '{pattern}'"
        
        # 数值验证
        if isinstance(value, (int, float)):
            if "minimum" in schema and value < schema["minimum"]:
                return False, f"Parameter '{param_name}' must be at least {schema['minimum']}"
            if "maximum" in schema and value > schema["maximum"]:
                return False, f"Parameter '{param_name}' must be at most {schema['maximum']}"
            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
                return False, f"Parameter '{param_name}' must be greater than {schema['exclusiveMinimum']}"
            if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
                return False, f"Parameter '{param_name}' must be less than {schema['exclusiveMaximum']}"
        
        # 枚举验证
        if "enum" in schema:
            if value not in schema["enum"]:
                return False, f"Parameter '{param_name}' must be one of {schema['enum']}"
        
        # 数组验证
        if isinstance(value, list):
            if "minItems" in schema and len(value) < schema["minItems"]:
                return False, f"Parameter '{param_name}' must have at least {schema['minItems']} items"
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                return False, f"Parameter '{param_name}' must have at most {schema['maxItems']} items"
            # 验证数组元素类型
            if "items" in schema:
                items_schema = schema["items"]
                for i, item in enumerate(value):
                    item_validation = self._validate_parameter_value(
                        f"{param_name}[{i}]",
                        item,
                        items_schema
                    )
                    if not item_validation[0]:
                        return item_validation
        
        # 对象验证
        if isinstance(value, dict) and "properties" in schema:
            obj_properties = schema.get("properties", {})
            obj_required = schema.get("required", [])
            
            # 检查必需字段
            for req_field in obj_required:
                if req_field not in value:
                    return False, f"Parameter '{param_name}.{req_field}' is required"
            
            # 验证对象属性
            for field_name, field_value in value.items():
                if field_name in obj_properties:
                    field_validation = self._validate_parameter_value(
                        f"{param_name}.{field_name}",
                        field_value,
                        obj_properties[field_name]
                    )
                    if not field_validation[0]:
                        return field_validation
        
        return True, None
    
    async def execute_tool(
        self,
        tool_name: str,
        execution_request: ToolExecutionRequest
    ) -> ToolExecutionResponse:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            execution_request: 执行请求
        
        Returns:
            执行响应
        
        Raises:
            ToolExecutionError: 如果执行失败
        """
        import time
        start_time = time.time()
        
        # 检查工具是否存在
        tool = self._tools.get(tool_name)
        if not tool:
            raise ToolExecutionError(
                f"Tool '{tool_name}' not found",
                tool_name,
                "TOOL_NOT_FOUND"
            )
        
        # 检查工具状态
        if tool.status != ToolStatus.ACTIVE:
            raise ToolExecutionError(
                f"Tool '{tool_name}' is not active (status: {tool.status.value})",
                tool_name,
                "TOOL_INACTIVE"
            )
        
        # 验证参数
        is_valid, error_msg = self.validate_parameters(
            tool_name,
            execution_request.parameters
        )
        if not is_valid:
            raise ToolExecutionError(
                error_msg or "Invalid parameters",
                tool_name,
                "INVALID_PARAMETERS"
            )
        
        # 检查是否是MCP工具
        tool_source = self._tool_sources.get(tool_name)
        if tool_source and tool_source.startswith("mcp:"):
            # MCP工具：通过MCP客户端执行
            client_name = tool_source.split(":")[1]
            client = self._mcp_clients.get(client_name)
            if not client:
                # 尝试从连接池获取
                client = self._mcp_connection_pool.get_client(client_name)
            
            if client:
                try:
                    result = await client.execute_tool(
                        tool_name,
                        execution_request.parameters,
                        timeout=execution_request.timeout
                    )
                except (MCPConnectionError, MCPProtocolError) as e:
                    raise ToolExecutionError(
                        f"MCP tool execution failed: {str(e)}",
                        tool_name,
                        "MCP_EXECUTION_ERROR"
                    )
            else:
                raise ToolExecutionError(
                    f"MCP client '{client_name}' not found for tool '{tool_name}'",
                    tool_name,
                    "MCP_CLIENT_NOT_FOUND"
                )
        else:
            # 本地工具：使用本地执行器
            executor = self._executors.get(tool_name)
            logger.info(f"Executing local tool '{tool_name}', executor: {executor is not None}")
            if not executor:
                logger.error(f"No executor registered for tool '{tool_name}'. Available executors: {list(self._executors.keys())}")
                raise ToolExecutionError(
                    f"No executor registered for tool '{tool_name}'",
                    tool_name,
                    "NO_EXECUTOR"
                )
            
            try:
                logger.info(f"Calling executor for tool '{tool_name}'")
                # 执行工具（带超时控制）
                if execution_request.timeout:
                    result = await asyncio.wait_for(
                        executor(execution_request.parameters),
                        timeout=execution_request.timeout
                    )
                else:
                    result = await executor(execution_request.parameters)
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_msg = f"Tool execution timed out after {execution_request.timeout}s"
                logger.error(f"Tool '{tool_name}' execution timeout: {error_msg}")
                
                raise ToolExecutionError(
                    error_msg,
                    tool_name,
                    "EXECUTION_TIMEOUT"
                )
        
        # 处理执行结果
        execution_time = time.time() - start_time
        
        logger.info(
            f"Tool '{tool_name}' executed successfully in {execution_time:.3f}s"
        )
        
        return ToolExecutionResponse(
            success=True,
            tool_name=tool_name,
            result=result,
            execution_time=execution_time
        )
    
    async def _default_executor(self, parameters: Dict[str, Any]) -> Any:
        """默认执行器（占位符）"""
        logger.warning("Using default executor - tool implementation not provided")
        return {
            "message": "Tool executed with default executor",
            "parameters": parameters,
            "note": "This is a placeholder implementation"
        }
    
    def get_tool_count(self) -> int:
        """获取工具总数"""
        return len(self._tools)
    
    def get_active_tool_count(self) -> int:
        """获取活跃工具数量"""
        return sum(1 for tool in self._tools.values() if tool.status == ToolStatus.ACTIVE)
    
    # ==================== MCP客户端管理 ====================
    
    async def initialize_mcp_clients(self, server_configs: List[Dict[str, Any]]) -> int:
        """
        初始化所有配置的MCP客户端（支持WebSocket和HTTP传输）
        
        Args:
            server_configs: MCP服务器配置列表，每个配置包含：
                - name: 服务器名称
                - url: 服务器URL（WebSocket或HTTP）
                - transport: 传输类型（"websocket"、"http"或"auto"，默认"auto"）
                - timeout: 超时时间（可选，默认30秒）
                - auto_connect: 是否自动连接（可选，默认True）
        
        Returns:
            成功初始化的客户端数量
        """
        initialized_count = 0
        
        for server_config in server_configs:
            try:
                server_name = server_config.get("name", f"mcp_{len(self._mcp_clients)}")
                transport = server_config.get("transport", "auto")
                logger.info(f"Initializing MCP client: {server_name} (transport: {transport})")
                
                success = await self._mcp_connection_pool.add_server(server_config)
                
                if success:
                    client = self._mcp_connection_pool.get_client(server_name)
                    if client:
                        self._mcp_clients[server_name] = client
                        
                        # 发现并注册工具（排除SAP工具，由sap_odata_agent直接处理）
                        try:
                            tools = await client.discover_tools()
                            # 过滤SAP OData工具
                            filtered_tools = [
                                tool for tool in tools
                                if not self._is_sap_odata_tool(tool)
                            ]
                            for tool in filtered_tools:
                                # 根据传输类型设置source前缀
                                source_prefix = "mcp-http" if transport == "http" else "mcp"
                                self.register_tool(tool, source=f"{source_prefix}:{server_name}", overwrite=True)
                            logger.info(f"Discovered and registered {len(filtered_tools)}/{len(tools)} tools from {server_name} (excluded {len(tools) - len(filtered_tools)} SAP tools)")
                        except Exception as e:
                            logger.warning(f"Failed to discover tools from {server_name}: {e}")
                        
                        initialized_count += 1
                else:
                    logger.warning(f"Failed to initialize MCP client: {server_name}")
                    
            except Exception as e:
                logger.error(f"Error initializing MCP client from config {server_config}: {e}", exc_info=True)
        
        logger.info(f"Initialized {initialized_count}/{len(server_configs)} MCP clients")
        return initialized_count
    
    async def refresh_tools(self) -> int:
        """
        刷新所有MCP服务器的工具列表
        
        Returns:
            刷新的工具数量
        """
        refreshed_count = 0
        
        for server_name, client in self._mcp_clients.items():
            if client.connected:
                try:
                    tools = await client.discover_tools()
                    old_count = len([t for t in self._tools.values() if self._tool_sources.get(t.name) == f"mcp:{server_name}"])
                    
                    # 移除旧的MCP工具
                    tools_to_remove = [
                        name for name, source in self._tool_sources.items()
                        if source == f"mcp:{server_name}"
                    ]
                    for tool_name in tools_to_remove:
                        self.unregister_tool(tool_name)
                    
                    # 注册新工具（排除SAP工具）
                    filtered_tools = [
                        tool for tool in tools
                        if not self._is_sap_odata_tool(tool)
                    ]
                    for tool in filtered_tools:
                        self.register_tool(tool, source=f"mcp:{server_name}", overwrite=True)
                    
                    refreshed_count += len(filtered_tools)
                    logger.info(f"Refreshed {len(filtered_tools)}/{len(tools)} tools from {server_name} (excluded {len(tools) - len(filtered_tools)} SAP tools)")
                    
                except Exception as e:
                    logger.error(f"Failed to refresh tools from {server_name}: {e}")
        
        return refreshed_count
    
    async def start_auto_refresh(self, interval: int = 300):
        """
        启动工具自动刷新任务
        
        Args:
            interval: 刷新间隔（秒）
        """
        if self._auto_refresh_task:
            self._auto_refresh_task.cancel()
        
        async def refresh_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.refresh_tools()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in auto-refresh loop: {e}")
        
        self._auto_refresh_task = asyncio.create_task(refresh_loop())
        logger.info(f"Started auto-refresh task with interval {interval}s")
    
    async def close_all_clients(self):
        """关闭所有MCP客户端连接"""
        await self._mcp_connection_pool.close_all()
        self._mcp_clients.clear()
        
        if self._auto_refresh_task:
            self._auto_refresh_task.cancel()
            try:
                await self._auto_refresh_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Closed all MCP clients")
    
    async def execute_tool_with_retry(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[int] = None
    ) -> ToolExecutionResponse:
        """
        带重试的工具执行
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            timeout: 超时时间（秒）
        
        Returns:
            执行响应
        """
        execution_request = ToolExecutionRequest(
            parameters=parameters,
            timeout=timeout
        )
        
        for attempt in range(max_retries):
            try:
                return await self.execute_tool(tool_name, execution_request)
            except (ToolExecutionError, MCPConnectionError, MCPProtocolError) as e:
                if attempt == max_retries - 1:
                    raise
                
                error_code = getattr(e, 'error_code', 'UNKNOWN')
                if error_code in ['MCP_EXECUTION_ERROR', 'MCP_CLIENT_NOT_FOUND', 'EXECUTION_TIMEOUT']:
                    logger.warning(
                        f"Tool execution failed (attempt {attempt + 1}/{max_retries}): {e.message}"
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
                else:
                    # 非可重试错误，直接抛出
                    raise
        
        raise ToolExecutionError("Max retries exceeded", tool_name, "MAX_RETRIES_EXCEEDED")

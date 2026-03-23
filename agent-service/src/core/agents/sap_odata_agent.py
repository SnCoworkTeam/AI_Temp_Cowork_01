"""
SAP OData智能体
专门处理SAP数据查询和操作，基于MCP服务动态发现和执行SAP OData操作
移除所有硬编码，完全基于MCP服务动态发现
"""
import logging
import json
import os
import httpx
from typing import Dict, Any, Optional, List, AsyncIterator
from datetime import datetime

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm
from ...services.sap_odata_mcp_client import SAPODataMCPClient

logger = logging.getLogger(__name__)


class LazyMetadataBuilder:
    """按需懒加载元数据构建器 - 从metadata-service获取元数据"""
    
    def __init__(self, metadata_service_url: Optional[str] = None):
        """
        初始化懒加载元数据构建器
        
        Args:
            metadata_service_url: 元数据服务URL（可选，默认从环境变量获取）
        """
        self.metadata_service_url = metadata_service_url or os.getenv(
            "METADATA_SERVICE_URL", "http://metadata-service:8005"
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timeout = 30.0
    
    async def get_metadata(self, service_id: str) -> Dict[str, Any]:
        """按需懒加载元数据，从metadata-service查询而非重新构建"""
        if service_id in self._cache:
            return self._cache[service_id]
        
        # 从metadata-service查询服务元数据
        metadata = await self._query_metadata_from_service(service_id)
        if metadata:
            self._cache[service_id] = metadata
        return metadata
    
    async def _query_metadata_from_service(self, service_id: str) -> Dict[str, Any]:
        """从metadata-service查询SAP OData服务元数据"""
        try:
            logger.info(f"Querying metadata from metadata-service for service: {service_id}")
            
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                # 方法1: 通过搜索查找数据资产（按服务ID或名称）
                search_url = f"{self.metadata_service_url}/api/data-assets"
                params = {
                    "search": service_id,
                    "limit": 100
                }
                
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    assets = response.json()
                    if isinstance(assets, list):
                        # 查找匹配的服务
                        for asset in assets:
                            asset_metadata = asset.get("metadata", {})
                            asset_name = asset.get("name", "")
                            asset_display_name = asset.get("display_name", "")
                            
                            # 检查是否匹配服务ID或名称
                            if (service_id.lower() in asset_name.lower() or
                                service_id.lower() in asset_display_name.lower() or
                                asset_metadata.get("service_id") == service_id or
                                asset_metadata.get("service_name") == service_id):
                                
                                # 转换为服务元数据格式
                                metadata = self._convert_asset_to_service_metadata(asset)
                                logger.info(f"Found metadata for {service_id} in metadata-service")
                                return metadata
                
                # 方法2: 如果搜索未找到，尝试通过分类和标签查找
                params = {
                    "classification": "sap_odata_service",
                    "limit": 200
                }
                response = await client.get(search_url, params=params)
                
                if response.status_code == 200:
                    assets = response.json()
                    if isinstance(assets, list):
                        for asset in assets:
                            asset_metadata = asset.get("metadata", {})
                            if (asset_metadata.get("service_id") == service_id or
                                asset_metadata.get("service_name") == service_id):
                                metadata = self._convert_asset_to_service_metadata(asset)
                                logger.info(f"Found metadata for {service_id} in metadata-service (by classification)")
                                return metadata
                
                logger.warning(f"Service {service_id} not found in metadata-service")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to query metadata from metadata-service for {service_id}: {e}")
            return {}
    
    def _convert_asset_to_service_metadata(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """将数据资产转换为服务元数据格式"""
        metadata = asset.get("metadata", {})
        
        # 提取服务信息
        service_metadata = {
            "service_id": metadata.get("service_id") or asset.get("name", ""),
            "service_name": metadata.get("service_name") or asset.get("display_name", ""),
            "description": asset.get("description", ""),
            "url": metadata.get("url") or metadata.get("service_url", ""),
            "category": asset.get("classification", ""),
            "entities": metadata.get("entities", []),
            "entities_count": len(metadata.get("entities", [])),
            "metadata_source": "metadata-service",
            "metadata_retrieved_at": datetime.now().isoformat()
        }
        
        # 如果元数据中有schema信息，也包含进去
        if metadata.get("schema"):
            service_metadata["schema"] = metadata.get("schema")
        
        return service_metadata
    
    def get_cached_metadata(self, service_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的元数据（不触发查询）"""
        return self._cache.get(service_id)
    
    def clear_cache(self, service_id: Optional[str] = None):
        """清除缓存"""
        if service_id:
            self._cache.pop(service_id, None)
        else:
            self._cache.clear()


class SAPODataAgent(IntelligentAgent):
    """SAP OData智能体 - 专门处理SAP数据查询和操作"""
    
    def __init__(self, mcp_client: Optional[SAPODataMCPClient] = None):
        """
        初始化SAP OData智能体
        
        Args:
            mcp_client: SAP OData MCP客户端（可选，默认创建新的）
        """
        super().__init__(
            agent_id="sap_odata_agent",
            name="SAP OData智能体",
            description="专门处理SAP数据查询、业务操作和数据分析，基于MCP服务动态执行SAP OData操作",
            capabilities={
                "sap_data_query": "SAP数据查询",
                "sap_business_operations": "SAP业务操作",
                "sap_analytics": "SAP数据分析",
                "dynamic_service_discovery": "动态服务发现",
                "intelligent_parameter_mapping": "智能参数映射"
            }
        )
        
        self.mcp_client = mcp_client or SAPODataMCPClient()
        self.llm = deepseek_llm
        self._available_tools_cache: Optional[List[Dict[str, Any]]] = None
        # 使用懒加载元数据构建器（从metadata-service获取，而非重新构建）
        self._metadata_builder = LazyMetadataBuilder()
        # 保留向后兼容的缓存结构
        self._service_metadata_cache: Dict[str, Any] = {"services": []}
        self._entity_keywords_cache: Optional[List[str]] = None
    
    async def initialize(self):
        """初始化智能体，连接MCP服务"""
        try:
            success = await self.mcp_client.initialize()
            if success:
                logger.info("SAP OData Agent initialized successfully")
                # 可选：在初始化时构建元数据（异步，不阻塞）
                # await self.build_metadata()
            else:
                logger.warning("SAP OData Agent initialization failed, will retry on first use")
        except Exception as e:
            logger.error(f"Failed to initialize SAP OData Agent: {e}")
            # 不抛出异常，允许延迟初始化
    
    def get_metadata_for_registration(self) -> Dict[str, Any]:
        """
        获取用于注册到元数据服务的元数据信息
        
        Returns:
            包含智能体详细信息的元数据字典
        """
        # 构建完整的元数据信息，便于在metadata-service中查询和发现
        metadata = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "agent_type": "sap_odata",
            "display_name": "SAP OData智能体",
            "capabilities": list(self.capabilities.keys()) if isinstance(self.capabilities, dict) else self.capabilities,
            "capability_details": {
                "sap_data_query": "支持SAP数据查询，包括实体查询、过滤、排序等",
                "sap_business_operations": "支持SAP业务操作，如创建、更新、删除等",
                "sap_analytics": "支持SAP数据分析和报表生成",
                "dynamic_service_discovery": "动态发现SAP OData服务，无需硬编码",
                "intelligent_parameter_mapping": "智能参数映射，自动优化OData查询参数"
            },
            "description": self.description,
            "detailed_description": (
                "SAP OData智能体专门处理SAP数据查询和业务操作。"
                "基于MCP服务动态发现和执行SAP OData操作，支持："
                "1. 智能服务发现：自动发现可用的SAP OData服务"
                "2. 动态工具选择：根据用户需求智能选择最合适的工具"
                "3. 参数优化：自动优化OData查询参数（$filter、$select、$top等）"
                "4. 元数据集成：从metadata-service按需加载服务元数据"
                "5. 结果分析：使用LLM分析和总结查询结果"
            ),
            "version": "1.0.0",
            "source": "agent-service",
            "builtin": True,
            "category": "sap_integration",
            "tags": [
                "sap",
                "odata",
                "sap-odata",
                "sap-integration",
                "data-query",
                "business-operations",
                "mcp-integration",
                "intelligent-agent"
            ],
            "mcp_integration": {
                "mcp_client_type": "SAPODataMCPClient",
                "server_url": getattr(self.mcp_client, 'server_url', None),
                "enabled": True,
                "description": "通过MCP服务动态发现和执行SAP OData操作"
            },
            "metadata_integration": {
                "enabled": True,
                "metadata_source": "metadata-service",
                "lazy_loading": True,
                "description": "从metadata-service按需加载SAP OData服务元数据，无需全量构建"
            },
            "metadata_features": {
                "service_metadata_cache": True,
                "entity_keywords_cache": True,
                "lazy_metadata_loading": True,
                "metadata_source": "metadata-service",
                "auto_service_discovery": True,
                "intelligent_tool_selection": True
            },
            "supported_operations": [
                "query",
                "create",
                "update",
                "delete",
                "service_discovery",
                "entity_discovery",
                "schema_retrieval"
            ],
            "supported_sap_entities": [
                "所有通过MCP服务发现的SAP OData实体"
            ],
            "query_optimization": {
                "auto_top_limit": True,
                "auto_select_fields": True,
                "intelligent_filtering": True,
                "parameter_mapping": True
            },
            "metadata_stats": {
                "cached_services": len(self._metadata_builder._cache),
                "cache_size": len(self._metadata_builder._cache),
                "metadata_service_url": self._metadata_builder.metadata_service_url
            },
            "usage_examples": [
                "查询SAP客户数据",
                "获取SAP物料信息",
                "创建SAP业务单据",
                "更新SAP主数据",
                "分析SAP业务数据"
            ],
            "integration_points": {
                "mcp_gateway": "通过MCP Gateway访问SAP OData服务",
                "metadata_service": "从metadata-service获取服务元数据",
                "llm_service": "使用LLM进行智能分析和参数优化"
            }
        }
        
        return metadata
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析SAP请求，确定最佳执行策略
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            SAP操作计划
        """
        try:
            # 确保MCP客户端已初始化
            if not self.mcp_client.initialized:
                await self.initialize()
            
            # 获取可用的SAP工具（动态发现，无硬编码）
            available_tools = await self._get_available_sap_tools()
            
            if not available_tools:
                return {
                    "needs_sap_operation": False,
                    "reason": "No SAP tools available from MCP service",
                    "suggestion": "Check SAP OData MCP server connection"
                }
            
            # 使用LLM分析请求并选择最佳工具（基于实际工具信息和元数据）
            analysis_result = await self._intelligent_sap_analysis(
                task_description, context, available_tools
            )
            
            # 如果分析结果中包含服务或实体信息，使用元数据增强（按需懒加载）
            if analysis_result.get("needs_sap_operation"):
                analysis_result = await self._enhance_analysis_with_metadata(
                    analysis_result, task_description, context
                )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"SAP request analysis failed: {e}", exc_info=True)
            return {
                "needs_sap_operation": False,
                "error": str(e),
                "fallback_strategy": "direct_query"
            }
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行SAP OData操作
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果
        """
        try:
            # 确保MCP客户端已初始化
            if not self.mcp_client.initialized:
                await self.initialize()
            
            user_input = input_data.get("task", "")
            execution_plan = input_data.get("execution_plan")
            
            if not execution_plan:
                execution_plan = await self.analyze_task(user_input, context)
            
            # 检查是否需要SAP操作
            if not execution_plan.get("needs_sap_operation", True):
                return {
                    "agent_type": "sap_odata",
                    "decision": "no_sap_operation_needed",
                    "reason": execution_plan.get("reason", "Request doesn't require SAP operation")
                }
            
            # 执行SAP操作
            operation_type = execution_plan.get("operation_type", "query")
            tool_name = execution_plan.get("selected_tool")
            parameters = execution_plan.get("parameters", {})
            
            if not tool_name:
                return {
                    "agent_type": "sap_odata",
                    "error": "No tool selected in execution plan",
                    "execution_plan": execution_plan
                }
            
            # 执行MCP工具
            result = await self._execute_sap_tool(
                tool_name, parameters, operation_type, context
            )
            
            # 结果后处理和分析
            processed_result = await self._process_sap_result(
                result, execution_plan, context
            )
            
            return {
                "agent_type": "sap_odata",
                "operation_type": operation_type,
                "tool_executed": tool_name,
                "execution_success": True,
                "raw_result": result,
                "processed_result": processed_result,
                "execution_plan": execution_plan
            }
            
        except Exception as e:
            logger.error(f"SAP OData agent execution failed: {e}", exc_info=True)
            return await self._handle_sap_execution_failure(e, input_data, context)
    
    async def _get_available_sap_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用的SAP工具（动态分类，无硬编码）
        """
        if self._available_tools_cache is None:
            try:
                tools = await self.mcp_client.list_tools()
                
                # 使用动态分类而非硬编码规则
                tool_categories = await self._categorize_tools_dynamically(tools)
                sap_tools = tool_categories.get("sap_odata", [])
                
                self._available_tools_cache = sap_tools
                logger.info(f"Found {len(sap_tools)} SAP tools from MCP service (dynamic classification)")
            except Exception as e:
                logger.warning(f"Failed to get SAP tools: {e}")
                self._available_tools_cache = []
        
        return self._available_tools_cache
    
    async def _categorize_tools_dynamically(self, tools: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        动态分类工具，而非硬编码排除
        
        Args:
            tools: 所有可用工具列表
            
        Returns:
            分类后的工具字典
        """
        # 如果工具数量较少，可以逐个分类；如果较多，批量分类
        if len(tools) <= 20:
            # 逐个分类
            categories = {
                "sap_odata": [],
                "general_tools": [],
                "data_tools": [],
                "communication_tools": []
            }
            
            for tool in tools:
                category = await self._determine_tool_category(tool)
                categories[category].append(tool)
            
            return categories
        else:
            # 批量分类以提高效率
            return await self._batch_categorize_tools(tools)
    
    async def _determine_tool_category(self, tool: Dict[str, Any]) -> str:
        """
        动态确定工具分类（使用LLM）
        
        Args:
            tool: 工具信息
            
        Returns:
            工具分类名称
        """
        try:
            tool_info = {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "metadata": tool.get("metadata", {}),
                "tool_type": tool.get("tool_type", ""),
                "parameters": tool.get("inputSchema", {}).get("properties", {}) if tool.get("inputSchema") else {}
            }
            
            prompt = f"""
分析以下工具信息，确定其分类：

工具信息：
{json.dumps(tool_info, ensure_ascii=False, indent=2)}

可选分类：
- sap_odata: SAP OData相关工具（用于SAP数据查询、业务操作等）
- general_tools: 通用工具（不特定于某个系统）
- data_tools: 数据处理工具（但不包括SAP OData）
- communication_tools: 通信工具（邮件、消息等）

请基于工具的实际功能（名称、描述、元数据、参数）进行判断，而不是仅凭名称模式。

返回分类名称（只返回分类名称，不要其他内容）：
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            classify_prompt = get_system_prompt(
                "sap_odata_agent_classify",
                fallback="你是工具分类专家，擅长基于工具的实际功能进行分类。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": classify_prompt},
                {"role": "user", "content": prompt}
            ])
            
            category = response.strip().lower() if isinstance(response, str) else "general_tools"
            
            # 验证分类是否有效
            valid_categories = ["sap_odata", "general_tools", "data_tools", "communication_tools"]
            if category not in valid_categories:
                # 如果返回的不是有效分类，尝试从响应中提取
                for valid_cat in valid_categories:
                    if valid_cat in category:
                        return valid_cat
                return "general_tools"
            
            return category
            
        except Exception as e:
            logger.warning(f"Failed to determine tool category for {tool.get('name', 'unknown')}: {e}")
            # 降级：基于简单规则
            return self._fallback_tool_category(tool)
    
    def _fallback_tool_category(self, tool: Dict[str, Any]) -> str:
        """
        降级工具分类（当LLM分类失败时使用）
        
        Args:
            tool: 工具信息
            
        Returns:
            工具分类名称
        """
        description = tool.get("description", "").lower()
        metadata = tool.get("metadata", {})
        
        # 基于元数据判断
        if (metadata.get("source") == "sap-odata-mcp-server" or
            metadata.get("service_type") == "sap_odata" or
            tool.get("tool_type") == "sap_odata"):
            return "sap_odata"
        
        # 基于描述判断
        if "sap" in description and "odata" in description:
            return "sap_odata"
        
        return "general_tools"
    
    async def _batch_categorize_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量分类工具（用于工具数量较多时）
        
        Args:
            tools: 工具列表
            
        Returns:
            分类后的工具字典
        """
        categories = {
            "sap_odata": [],
            "general_tools": [],
            "data_tools": [],
            "communication_tools": []
        }
        
        # 将工具分批处理
        batch_size = 10
        for i in range(0, len(tools), batch_size):
            batch = tools[i:i + batch_size]
            
            # 构建批量分类提示词
            tools_summary = []
            for tool in batch:
                tools_summary.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", "")[:200],  # 限制长度
                    "metadata_source": tool.get("metadata", {}).get("source", ""),
                    "tool_type": tool.get("tool_type", "")
                })
            
            prompt = f"""
分析以下工具列表，为每个工具确定分类：

工具列表：
{json.dumps(tools_summary, ensure_ascii=False, indent=2)}

可选分类：
- sap_odata: SAP OData相关工具
- general_tools: 通用工具
- data_tools: 数据处理工具（非SAP）
- communication_tools: 通信工具

返回JSON格式，键为工具名称，值为分类名称：
{{
    "工具名称1": "分类名称",
    "工具名称2": "分类名称",
    ...
}}
"""
            
            try:
                # 从提示词模板获取系统提示词
                from ..prompt_utils import get_system_prompt
                classify_prompt = get_system_prompt(
                    "sap_odata_agent_classify",
                    fallback="你是工具分类专家。"
                )
                
                response = await self.llm.chat([
                    {"role": "system", "content": classify_prompt},
                    {"role": "user", "content": prompt}
                ])
                
                # 解析响应
                if isinstance(response, str):
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        category_map = json.loads(response[json_start:json_end])
                        
                        # 根据分类结果分配工具
                        for tool in batch:
                            tool_name = tool.get("name", "")
                            category = category_map.get(tool_name, "general_tools")
                            if category in categories:
                                categories[category].append(tool)
                            else:
                                categories["general_tools"].append(tool)
                    else:
                        # 解析失败，使用降级方案
                        for tool in batch:
                            category = self._fallback_tool_category(tool)
                            categories[category].append(tool)
                else:
                    # 响应不是字符串，使用降级方案
                    for tool in batch:
                        category = self._fallback_tool_category(tool)
                        categories[category].append(tool)
                        
            except Exception as e:
                logger.warning(f"Batch categorization failed: {e}, using fallback")
                # 使用降级方案
                for tool in batch:
                    category = self._fallback_tool_category(tool)
                    categories[category].append(tool)
        
        return categories
    
    async def _intelligent_sap_analysis(
        self,
        user_input: str,
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        智能SAP请求分析（基于实际工具信息，无硬编码规则）
        """
        
        # 动态确定工具数量限制
        tool_limit = self._get_tool_limit(context)
        tools_to_analyze = available_tools[:tool_limit]
        
        # 构建完整的工具信息用于LLM分析
        tools_info = []
        for tool in tools_to_analyze:
            tool_info = {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "tool_type": tool.get("tool_type"),
                "status": tool.get("status")
            }
            
            # 提取参数信息
            input_schema = tool.get("inputSchema", {})
            if input_schema:
                tool_info["parameters"] = input_schema.get("properties", {})
                tool_info["required_parameters"] = input_schema.get("required", [])
            
            # 提取元数据信息（包含业务实体、服务等信息）
            metadata = tool.get("metadata", {})
            if metadata:
                tool_info["metadata"] = metadata
                tool_info["business_entity"] = metadata.get("entity_name")
                tool_info["sap_service"] = metadata.get("service_id")
                tool_info["operation_type"] = metadata.get("operation")  # read/create/update/delete
            
            # 提取返回值信息
            if tool.get("returns"):
                tool_info["returns"] = tool.get("returns")
            
            tools_info.append(tool_info)
        
        # 动态提取相关上下文
        context_summary = await self._extract_relevant_context(context)
        
        # 构建增强的提示词，不包含硬编码规则
        prompt = f"""
作为SAP OData专家，分析以下用户请求，从可用工具中选择最合适的工具。

**用户请求**：
{user_input}

**可用SAP工具**（包含完整信息）：
{json.dumps(tools_info, ensure_ascii=False, indent=2)}

**上下文信息**：
{json.dumps(context_summary, ensure_ascii=False, indent=2)}

**分析要求**：

1. **任务深度分析**：
   - 任务的核心业务需求是什么？
   - 涉及哪些SAP业务实体？
   - 需要执行什么类型的操作？（查询、创建、更新、删除、服务发现）

2. **工具能力匹配**：
   - 仔细检查每个工具的参数定义（parameters），理解工具的具体能力
   - 检查必需参数（required_parameters），确保任务能提供这些参数
   - 分析工具元数据（metadata），理解工具的业务实体和服务信息
   - 找到最能满足任务需求的工具

3. **参数提取**：
   - 从任务描述中提取参数值
   - 从上下文信息中提取参数值
   - 确保所有必需参数都有值
   - 对于OData查询，考虑是否需要$filter、$select、$top等参数

**返回JSON格式**：
{{
    "needs_sap_operation": true/false,
    "operation_type": "query|create|update|delete|discovery",
    "selected_tool": "工具名称（如果needs_sap_operation为true，必须提供）",
    "parameters": {{"参数名": "参数值"}},
    "business_entities": ["实体1", "实体2"],
    "sap_service": "服务名称",
    "reasoning": "详细的分析过程和匹配理由",
    "confidence": 0.0-1.0
}}
"""
        
        response = await self.llm.chat([
            {
                "role": "system",
                "content": """你是SAP OData专家，擅长：
1. 理解用户自然语言请求并映射到SAP操作
2. 智能选择最合适的SAP OData服务和实体
3. 提取和优化OData查询参数
4. 处理复杂的业务逻辑和数据分析需求
你需要基于实际工具信息进行判断，而不是依赖硬编码的规则。"""
            },
            {"role": "user", "content": prompt}
        ])
        
        return self._parse_llm_response(response)
    
    async def _execute_sap_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        operation_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行SAP工具"""
        try:
            logger.info(f"Executing SAP tool: {tool_name} with parameters: {parameters}")
            
            # 优化参数
            optimized_params = await self._optimize_parameters(
                tool_name, parameters, operation_type, context
            )
            
            # 执行工具
            result = await self.mcp_client.call_tool(tool_name, optimized_params)
            
            return result
            
        except Exception as e:
            logger.error(f"SAP tool execution failed: {e}", exc_info=True)
            raise
    
    def _get_tool_limit(self, context: Dict[str, Any]) -> int:
        """
        基于上下文动态确定工具数量限制
        
        Args:
            context: 上下文信息
            
        Returns:
            工具数量限制
        """
        # 从配置或上下文获取
        default_limit = context.get("tool_limit", 20)
        complexity = context.get("task_complexity", "medium")
        
        limits = {
            "simple": 10,
            "medium": 20,
            "complex": 50
        }
        
        return limits.get(complexity, default_limit)
    
    async def _extract_relevant_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        动态提取相关上下文（使用LLM）
        
        Args:
            context: 完整上下文
            
        Returns:
            提取的相关上下文
        """
        try:
            # 如果上下文较小，直接使用LLM提取
            context_str = json.dumps(context, ensure_ascii=False)
            if len(context_str) < 2000:
                prompt = f"""
从以下上下文数据中提取与SAP工具执行相关的信息：

完整上下文：
{context_str}

请提取：
1. 可能作为工具参数的数据（如服务ID、实体名称、查询条件等）
2. 影响工具选择的配置信息
3. 用户偏好或约束条件（如数据量限制、字段需求等）
4. 业务相关的上下文信息

返回提取的相关信息（JSON格式，只包含相关字段）：
"""
                
                # 从提示词模板获取系统提示词
                from ..prompt_utils import get_system_prompt
                context_prompt = get_system_prompt(
                    "sap_odata_agent_context",
                    fallback="你是上下文提取专家，擅长从复杂上下文中提取与工具执行相关的关键信息。"
                )
                
                response = await self.llm.chat([
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": prompt}
                ])
                
                # 解析响应
                if isinstance(response, str):
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        extracted = json.loads(response[json_start:json_end])
                        return extracted
            
            # 降级：简单提取
            return self._simple_context_extraction(context)
            
        except Exception as e:
            logger.warning(f"Failed to extract relevant context dynamically: {e}")
            return self._simple_context_extraction(context)
    
    def _simple_context_extraction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        简单的上下文提取（降级方案）
        
        Args:
            context: 完整上下文
            
        Returns:
            提取的上下文
        """
        context_summary = {}
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                context_summary[key] = value
            elif isinstance(value, dict):
                # 提取字典中的关键信息（但不硬编码字段名）
                if isinstance(value, dict) and len(str(value)) < 500:
                    context_summary[key] = value
                else:
                    # 如果太大，只保留键
                    context_summary[key] = list(value.keys()) if isinstance(value, dict) else str(value)[:200]
        
        return context_summary
    
    async def _optimize_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        operation_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化工具参数（动态判断，无硬编码前缀检查）
        """
        optimized = parameters.copy()
        
        # 动态确定是否需要OData查询优化
        needs_odata_optimization = await self._needs_odata_optimization(
            tool_name, operation_type, parameters, context
        )
        
        if needs_odata_optimization:
            # 自动添加$top限制（防止返回过多数据）
            if "$top" not in optimized:
                optimized["$top"] = 100
            
            # 如果上下文中有字段需求，添加$select
            if "$select" not in optimized:
                required_fields = context.get("required_fields")
                if required_fields and isinstance(required_fields, list):
                    optimized["$select"] = ",".join(required_fields)
        
        return optimized
    
    async def _needs_odata_optimization(
        self,
        tool_name: str,
        operation_type: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        动态判断是否需要OData查询优化（无硬编码）
        
        Args:
            tool_name: 工具名称
            operation_type: 操作类型
            parameters: 参数
            context: 上下文
            
        Returns:
            是否需要OData优化
        """
        # 如果操作类型明确是查询
        if operation_type == "query":
            return True
        
        # 使用LLM判断工具是否需要OData优化
        try:
            tool_info = {
                "name": tool_name,
                "operation_type": operation_type,
                "parameters": list(parameters.keys()),
                "has_odata_params": any(key.startswith("$") for key in parameters.keys())
            }
            
            prompt = f"""
判断以下工具是否需要OData查询优化（如$top、$select等）：

工具信息：
{json.dumps(tool_info, ensure_ascii=False, indent=2)}

OData查询优化适用于：
- 执行数据查询操作的工具
- 可能返回大量数据的工具
- 支持OData查询参数（$filter、$select、$top等）的工具

返回 true 或 false（只返回布尔值，不要其他内容）：
"""
            
            response = await self.llm.chat([
                {"role": "system", "content": "你是OData查询优化专家。"},
                {"role": "user", "content": prompt}
            ])
            
            if isinstance(response, str):
                response_lower = response.strip().lower()
                if "true" in response_lower or "是" in response_lower or "需要" in response_lower:
                    return True
                if "false" in response_lower or "否" in response_lower or "不需要" in response_lower:
                    return False
            
            # 降级：基于参数判断
            return any(key.startswith("$") for key in parameters.keys())
            
        except Exception as e:
            logger.warning(f"Failed to determine OData optimization need: {e}")
            # 降级：基于操作类型判断
            return operation_type == "query"
    
    async def _process_sap_result(
        self,
        raw_result: Dict[str, Any],
        execution_plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理SAP结果"""
        try:
            # 使用LLM分析和总结结果
            prompt = f"""
分析以下SAP操作结果：

操作类型: {execution_plan.get('operation_type')}
业务实体: {execution_plan.get('business_entities', [])}
原始结果: {json.dumps(raw_result, ensure_ascii=False, indent=2)}

请提供：
1. **结果摘要**: 简洁的结果总结
2. **关键信息**: 提取重要数据点
3. **业务洞察**: 业务含义和分析
4. **后续建议**: 下一步操作建议

返回JSON格式:
{{
    "summary": "结果摘要",
    "key_findings": ["发现1", "发现2"],
    "business_insights": ["洞察1", "洞察2"],
    "next_actions": ["建议1", "建议2"],
    "data_quality": "good|partial|limited"
}}
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            analyze_prompt = get_system_prompt(
                "sap_odata_agent_analyze",
                fallback="你是SAP数据分析专家，擅长从SAP操作结果中提取业务价值。"
            )
            
            analysis = await self.llm.chat([
                {"role": "system", "content": analyze_prompt},
                {"role": "user", "content": prompt}
            ])
            
            processed = self._parse_llm_response(analysis)
            
            # 添加原始结果引用
            processed["raw_data_reference"] = {
                "record_count": self._extract_record_count(raw_result),
                "success": raw_result.get("success", True)
            }
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to process SAP result: {e}")
            return {
                "summary": "结果处理失败",
                "key_findings": [],
                "business_insights": ["无法分析结果"],
                "next_actions": ["检查原始数据"],
                "data_quality": "unknown",
                "processing_error": str(e)
            }
    
    async def _handle_sap_execution_failure(
        self,
        error: Exception,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理SAP执行失败"""
        
        user_input = input_data.get("task", "")
        error_msg = str(error).lower()
        
        # 尝试使用服务发现进行降级
        try:
            # 从MCP服务动态获取实体关键词（而非硬编码）
            keywords = await self._extract_sap_keywords_dynamic(user_input)
            if keywords:
                # 使用服务发现工具
                discovery_result = await self.mcp_client.search_services(
                    keyword=keywords[0] if keywords else "",
                    category="all"
                )
                
                return {
                    "agent_type": "sap_odata",
                    "execution_success": False,
                    "error": str(error),
                    "fallback_suggestion": "尝试服务发现",
                    "available_services": discovery_result.get("services", []),
                    "suggestion": f"发现相关服务，请尝试使用具体服务工具"
                }
        except Exception as fallback_error:
            logger.warning(f"Fallback also failed: {fallback_error}")
        
        return {
            "agent_type": "sap_odata",
            "execution_success": False,
            "error": str(error),
            "suggestion": "请检查SAP连接或重新表述请求"
        }
    
    async def _enhance_analysis_with_metadata(
        self,
        analysis_result: Dict[str, Any],
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用懒加载元数据增强分析结果
        
        Args:
            analysis_result: 初始分析结果
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            增强后的分析结果
        """
        try:
            # 如果已经选择了工具和服务，按需加载元数据
            selected_service = analysis_result.get("sap_service")
            business_entities = analysis_result.get("business_entities", [])
            
            if selected_service:
                # 使用懒加载获取服务元数据
                service_metadata = await self._metadata_builder.get_metadata(selected_service)
                if service_metadata:
                    analysis_result["service_metadata"] = {
                        "description": service_metadata.get("description"),
                        "category": service_metadata.get("category"),
                        "entities_count": service_metadata.get("entities_count", 0)
                    }
                    
                    # 如果指定了业务实体，从该服务的元数据中查找匹配的实体
                    if business_entities:
                        matched_entities = []
                        for entity_name in business_entities:
                            for entity in service_metadata.get("entities", []):
                                if entity.get("name", "").lower() == entity_name.lower():
                                    matched_entities.append({
                                        "entity_name": entity.get("name"),
                                        "service_id": service_metadata.get("service_id"),
                                        "service_name": service_metadata.get("service_name"),
                                        "schema_available": "schema" in entity
                                    })
                                    break
                        
                        if matched_entities:
                            analysis_result["matched_entities"] = matched_entities
            
            return analysis_result
            
        except Exception as e:
            logger.warning(f"Failed to enhance analysis with metadata: {e}")
            return analysis_result
    
    async def _extract_sap_keywords_dynamic(self, text: str) -> List[str]:
        """
        从MCP服务动态提取SAP关键词（移除硬编码）
        """
        try:
            # 1. 先使用服务发现获取可用的SAP服务
            services_result = await self.mcp_client.search_services(
                keyword="",
                category="all"
            )
            
            # 2. 从服务名称和描述中提取关键词（动态限制）
            services = services_result.get("services", [])
            service_limit = self._get_service_limit_for_keywords(len(services))
            all_keywords = []
            for service in services[:service_limit]:
                service_name = service.get("name", "").lower()
                service_desc = service.get("description", "").lower()
                
                # 提取服务名称中的关键词
                if service_name:
                    all_keywords.append(service_name)
                if service_desc:
                    # 从描述中提取关键词（简单分词）
                    words = service_desc.split()
                    all_keywords.extend([w for w in words if len(w) > 3])
            
            # 3. 使用LLM进行语义匹配
            if all_keywords:
                # 动态限制关键词数量
                keyword_limit = self._get_keyword_limit_for_llm(len(all_keywords))
                unique_keywords = list(set(all_keywords))[:keyword_limit]
                
                prompt = f"""
从以下文本中提取与SAP相关的关键词：

文本: {text}

可用的SAP服务关键词: {', '.join(unique_keywords)}

请返回与文本相关的SAP关键词列表（JSON数组格式）。
"""
                response = await self.llm.chat([
                    {"role": "system", "content": "你是SAP关键词提取专家。"},
                    {"role": "user", "content": prompt}
                ])
                
                # 解析响应
                if isinstance(response, str):
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    if json_start >= 0 and json_end > json_start:
                        return json.loads(response[json_start:json_end])
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to extract SAP keywords dynamically: {e}")
            return []
    
    def _get_service_limit_for_keywords(self, total_services: int) -> int:
        """
        动态确定用于关键词提取的服务数量限制
        
        Args:
            total_services: 总服务数量
            
        Returns:
            服务数量限制
        """
        # 根据总数量动态调整
        if total_services <= 10:
            return total_services
        elif total_services <= 50:
            return 20
        else:
            return 30
    
    def _get_keyword_limit_for_llm(self, total_keywords: int) -> int:
        """
        动态确定用于LLM的关键词数量限制
        
        Args:
            total_keywords: 总关键词数量
            
        Returns:
            关键词数量限制
        """
        # 根据总数量动态调整，避免token过长
        if total_keywords <= 30:
            return total_keywords
        elif total_keywords <= 100:
            return 50
        else:
            return 80
    
    async def _determine_execution_strategy(
        self,
        tool: Dict[str, Any],
        task: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        动态确定执行策略（无硬编码枚举）
        
        Args:
            tool: 工具信息
            task: 任务描述
            parameters: 工具参数
            
        Returns:
            执行策略名称
        """
        try:
            tool_info = {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": parameters,
                "parameter_count": len(parameters),
                "has_complex_params": any(
                    isinstance(v, (dict, list)) for v in parameters.values()
                )
            }
            
            prompt = f"""
分析工具执行策略：

工具信息：
{json.dumps(tool_info, ensure_ascii=False, indent=2)}

任务描述：
{task}

可选策略：
- direct: 直接执行，参数简单明确，无需预处理
- preprocess: 需要预处理，参数复杂或需要转换
- validate_first: 需要先验证参数有效性
- batch: 适合批量处理多个请求

请基于工具的实际参数复杂度和任务需求选择策略。

返回策略名称（只返回策略名称，不要其他内容）：
"""
            
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            strategy_prompt = get_system_prompt(
                "sap_odata_agent_strategy",
                fallback="你是执行策略专家，擅长根据工具和任务特征选择最佳执行策略。"
            )
            
            response = await self.llm.chat([
                {"role": "system", "content": strategy_prompt},
                {"role": "user", "content": prompt}
            ])
            
            strategy = response.strip().lower() if isinstance(response, str) else "direct"
            
            # 验证策略是否有效
            valid_strategies = ["direct", "preprocess", "validate_first", "batch"]
            if strategy not in valid_strategies:
                # 如果返回的不是有效策略，尝试从响应中提取
                for valid_strat in valid_strategies:
                    if valid_strat in strategy:
                        return valid_strat
                return "direct"
            
            return strategy
            
        except Exception as e:
            logger.warning(f"Failed to determine execution strategy: {e}")
            # 降级：基于参数复杂度判断
            if len(parameters) > 5 or any(isinstance(v, (dict, list)) for v in parameters.values()):
                return "preprocess"
            return "direct"
    
    def _extract_record_count(self, result: Dict[str, Any]) -> int:
        """提取记录数量"""
        if isinstance(result, dict):
            # 检查不同可能的结果格式
            if "value" in result and isinstance(result["value"], list):
                return len(result["value"])
            if "items" in result and isinstance(result["items"], list):
                return len(result["items"])
            if "data" in result and isinstance(result["data"], list):
                return len(result["data"])
            if "results" in result and isinstance(result["results"], list):
                return len(result["results"])
        return 0
    
    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """解析LLM响应"""
        if isinstance(response, str):
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(response[json_start:json_end])
            except Exception as e:
                logger.warning(f"Failed to parse LLM response: {e}")
        
        # 默认返回
        return {
            "needs_sap_operation": False,
            "error": "Failed to parse LLM response"
        }
    
    async def build_metadata(
        self,
        force_rebuild: bool = False,
        limit_services: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        构建SAP OData服务元数据（已废弃，现在使用懒加载从metadata-service获取）
        
        注意：此方法已废弃。元数据现在从metadata-service按需懒加载，无需全量构建。
        如需获取特定服务的元数据，请使用 get_service_metadata(service_id)。
        
        Args:
            force_rebuild: 已废弃
            limit_services: 已废弃
            
        Returns:
            提示信息
        """
        logger.warning(
            "build_metadata() is deprecated. "
            "Metadata is now lazily loaded from metadata-service. "
            "Use get_service_metadata(service_id) to get specific service metadata."
        )
        
        return {
            "status": "deprecated",
            "message": "Metadata is now lazily loaded from metadata-service. No need to build in advance.",
            "cached_services": len(self._metadata_builder._cache),
            "metadata_service_url": self._metadata_builder.metadata_service_url,
            "suggestion": "Use get_service_metadata(service_id) to get specific service metadata on demand."
        }
    
    def _build_entity_keywords_cache(self):
        """构建实体关键词缓存，用于快速搜索"""
        try:
            keywords = set()
            
            for service in self._service_metadata_cache.get("services", []):
                service_name = service.get("service_name", "").lower()
                if service_name:
                    keywords.add(service_name)
                
                for entity in service.get("entities", []):
                    entity_name = entity.get("name", "").lower()
                    if entity_name:
                        keywords.add(entity_name)
                        # 提取关键词（简单分词）
                        words = entity_name.split("_")
                        keywords.update([w for w in words if len(w) > 2])
            
            self._entity_keywords_cache = list(keywords)
            logger.info(f"Built entity keywords cache: {len(keywords)} keywords")
            
        except Exception as e:
            logger.warning(f"Failed to build entity keywords cache: {e}")
            self._entity_keywords_cache = []
    
    async def get_service_metadata(
        self,
        service_id: Optional[str] = None,
        auto_build: bool = True
    ) -> Dict[str, Any]:
        """
        获取服务元数据（从metadata-service懒加载）
        
        Args:
            service_id: 服务ID（如果为None，返回缓存的所有服务）
            auto_build: 已废弃，保留用于向后兼容
            
        Returns:
            服务元数据
        """
        # 如果指定了服务ID，使用懒加载从metadata-service获取
        if service_id:
            return await self._metadata_builder.get_metadata(service_id)
        
        # 返回所有缓存的元数据
        return {
            "services": list(self._metadata_builder._cache.values()),
            "total_services": len(self._metadata_builder._cache),
            "cached_services": list(self._metadata_builder._cache.keys())
        }
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        获取元数据摘要
        
        Returns:
            元数据摘要信息
        """
        return {
            "metadata_source": "metadata-service",
            "lazy_loading": True,
            "cached_services": len(self._metadata_builder._cache),
            "cache_size": len(self._metadata_builder._cache),
            "metadata_service_url": self._metadata_builder.metadata_service_url
        }


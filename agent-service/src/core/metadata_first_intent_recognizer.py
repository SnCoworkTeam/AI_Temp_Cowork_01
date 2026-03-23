"""
元数据前置意图识别器
在LLM理解之前先检索相关元数据，提供业务上下文
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import os
from cachetools import TTLCache
import hashlib
import json
import time

from .llm_integration import deepseek_llm
# 延迟导入以避免循环导入
# from .conversation_agent import IntentAnalysis, TaskType

logger = logging.getLogger(__name__)


class MetadataCache:
    """元数据缓存"""
    
    def __init__(self, maxsize=1000, ttl=300):
        """
        初始化缓存
        
        Args:
            maxsize: 最大缓存条目数
            ttl: 缓存过期时间（秒）
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.similarity_cache = {}  # 相似查询缓存
    
    def _generate_cache_key(self, user_input: str, context: Optional[Dict] = None) -> str:
        """生成缓存键"""
        key_data = {
            "input": user_input.lower().strip(),
            "context": context or {}
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, user_input: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """获取缓存"""
        cache_key = self._generate_cache_key(user_input, context)
        return self.cache.get(cache_key)
    
    def set(self, user_input: str, metadata: Dict, context: Optional[Dict] = None):
        """设置缓存"""
        cache_key = self._generate_cache_key(user_input, context)
        self.cache[cache_key] = metadata
    
    def _find_similar_query(self, user_input: str) -> Optional[str]:
        """查找相似查询（简单实现）"""
        # TODO: 实现更智能的相似度匹配
        user_lower = user_input.lower().strip()
        for cached_query in self.similarity_cache.keys():
            if user_lower in cached_query or cached_query in user_lower:
                return cached_query
        return None


class MetadataRetriever:
    """元数据检索器"""
    
    def __init__(self):
        self.metadata_service_url = os.getenv(
            "METADATA_SERVICE_URL",
            "http://metadata-service:8005"
        )
        self.mcp_gateway_url = os.getenv(
            "MCP_GATEWAY_URL",
            "http://mcp-gateway:8001"
        )
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.timeout = httpx.Timeout(5.0)  # 5秒超时
    
    async def _search_tools(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索工具元数据（支持语义搜索）"""
        try:
            # 首先尝试语义搜索（如果知识库中有向量化的工具元数据）
            semantic_tools = await self._semantic_search_tools(query, limit)
            if semantic_tools:
                logger.debug(f"Found {len(semantic_tools)} tools via semantic search")
                return semantic_tools
            
            # 降级到关键词搜索
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 搜索工具（通过MCP Gateway）
                response = await client.get(
                    f"{self.mcp_gateway_url}/api/tools",
                    params={"page": 1, "page_size": 100}
                )
                if response.status_code == 200:
                    tools_data = response.json()
                    tools_list = []
                    
                    # 处理不同的响应格式
                    if isinstance(tools_data, dict):
                        if "tools" in tools_data:
                            tools_list = tools_data["tools"]
                        elif "items" in tools_data:
                            tools_list = tools_data["items"]
                        elif "data" in tools_data:
                            tools_list = tools_data["data"]
                    elif isinstance(tools_data, list):
                        tools_list = tools_data
                    
                    # 本地过滤（基于查询关键词）
                    query_lower = query.lower()
                    filtered_tools = []
                    for tool in tools_list:
                        tool_name = tool.get("name", "").lower()
                        tool_desc = tool.get("description", "").lower()
                        if query_lower in tool_name or query_lower in tool_desc:
                            filtered_tools.append(tool)
                            if len(filtered_tools) >= limit:
                                break
                    
                    return filtered_tools
                return []
        except Exception as e:
            logger.warning(f"Failed to search tools: {str(e)}")
            return []
    
    async def _semantic_search_tools(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """语义搜索工具（通过知识库）"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 在工具元数据知识库中搜索
                response = await client.post(
                    f"{self.knowledge_base_url}/api/search/semantic",
                    json={
                        "query": query,
                        "top_k": limit,
                        "filters": {"category": "tool_metadata"}
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", []) if isinstance(data, dict) else data
                    
                    # 从搜索结果中提取工具信息
                    tools = []
                    for result in results:
                        metadata = result.get("metadata", {})
                        filename = metadata.get("filename", "")
                        
                        # 从文件名提取工具名称
                        if filename.startswith("tool_"):
                            tool_name = filename.replace("tool_", "").replace(".md", "")
                            tools.append({
                                "name": tool_name,
                                "description": result.get("content", "")[:200],  # 前200字符
                                "score": result.get("score", 0.0),
                                "source": "semantic_search"
                            })
                    
                    return tools
                
                return []
        except Exception as e:
            logger.debug(f"Semantic tool search failed: {str(e)}")
            return []
    
    async def _search_sap_services(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索SAP服务元数据"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 搜索SAP数据资产
                response = await client.get(
                    f"{self.metadata_service_url}/api/data-assets",
                    params={
                        "asset_type": "sap_service",
                        "search": query,
                        "limit": limit
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "items" in data:
                        return data["items"]
                return []
        except Exception as e:
            logger.warning(f"Failed to search SAP services: {str(e)}")
            return []
    
    async def _search_business_entities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索业务实体元数据"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 搜索业务实体
                response = await client.get(
                    f"{self.metadata_service_url}/api/business-entities",
                    params={"search": query, "limit": limit}
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "items" in data:
                        return data["items"]
                return []
        except Exception as e:
            logger.warning(f"Failed to search business entities: {str(e)}")
            return []
    
    async def _search_workflows(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """搜索工作流元数据"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 搜索工作流
                response = await client.get(
                    f"{self.metadata_service_url}/api/workflows",
                    params={
                        "workflow_type": "workflow",
                        "search": query,
                        "limit": limit
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "items" in data:
                        return data["items"]
                return []
        except Exception as e:
            logger.warning(f"Failed to search workflows: {str(e)}")
            return []
    
    async def _semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """语义搜索（使用知识库服务）"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 使用知识库的语义搜索
                response = await client.post(
                    f"{self.knowledge_base_url}/api/search/semantic",
                    json={"query": query, "top_k": limit}
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "results" in data:
                        return data["results"]
                    elif isinstance(data, list):
                        return data
                return []
        except Exception as e:
            logger.warning(f"Failed to semantic search: {str(e)}")
            return []
    
    async def retrieve_metadata(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        检索与用户输入相关的元数据
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            元数据字典
        """
        # 并行检索不同类型的元数据
        tasks = [
            self._search_tools(user_input, limit=5),
            self._search_sap_services(user_input, limit=5),
            self._search_business_entities(user_input, limit=5),
            self._search_workflows(user_input, limit=3),
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            tools, sap_services, business_entities, workflows = results
            
            # 处理异常
            tools = tools if not isinstance(tools, Exception) else []
            sap_services = sap_services if not isinstance(sap_services, Exception) else []
            business_entities = business_entities if not isinstance(business_entities, Exception) else []
            workflows = workflows if not isinstance(workflows, Exception) else []
            
            return {
                "tools": tools or [],
                "sap_services": sap_services or [],
                "business_entities": business_entities or [],
                "workflows": workflows or [],
                "retrieved_at": datetime.now().isoformat(),
                "query": user_input
            }
        except Exception as e:
            logger.error(f"Error retrieving metadata: {str(e)}", exc_info=True)
            return {
                "tools": [],
                "sap_services": [],
                "business_entities": [],
                "workflows": [],
                "retrieved_at": datetime.now().isoformat(),
                "query": user_input,
                "error": str(e)
            }
    
    async def retrieve_metadata_fast(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        快速检索元数据（分层策略）
        
        1. 先尝试关键词匹配（最快）
        2. 如果不够，再进行语义搜索
        """
        # 第一层：快速关键词匹配
        quick_metadata = await self._quick_keyword_match(user_input)
        if quick_metadata and self._is_high_confidence(quick_metadata):
            return quick_metadata
        
        # 第二层：完整检索
        return await self.retrieve_metadata(user_input, context)
    
    async def _quick_keyword_match(self, user_input: str) -> Optional[Dict[str, Any]]:
        """快速关键词匹配（改进版：包含业务实体检索）"""
        # 简单的关键词匹配逻辑
        user_lower = user_input.lower()
        
        # 检查是否是SAP相关
        sap_keywords = ["sap", "销售订单", "采购订单", "物料", "客户", "供应商", "erp"]
        is_sap = any(kw in user_lower for kw in sap_keywords)
        
        # 检查是否是工具相关
        tool_keywords = ["发送邮件", "发邮件", "邮件", "email", "send"]
        is_tool = any(kw in user_lower for kw in tool_keywords)
        
        if not (is_sap or is_tool):
            return None
        
        metadata = {
            "tools": [],
            "sap_services": [],
            "business_entities": [],
            "workflows": [],
            "retrieved_at": datetime.now().isoformat(),
            "query": user_input
        }
        
        # 如果是SAP相关，尝试快速检索业务实体（获取表名信息）
        if is_sap:
            try:
                # 快速检索业务实体（带超时，避免阻塞）
                entities = await asyncio.wait_for(
                    self.metadata_retriever._search_business_entities(user_input, limit=5),
                    timeout=2.0  # 2秒超时
                )
                if entities:
                    metadata["business_entities"] = entities
                    logger.debug(f"Found {len(entities)} business entities for quick match: {[e.get('name', '') for e in entities]}")
            except (asyncio.TimeoutError, Exception) as e:
                logger.debug(f"Quick business entity search failed: {e}")
            
            metadata["sap_services"] = [{"name": "SAP查询", "type": "sap_query"}]
        
        if is_tool:
            metadata["tools"] = [{"name": "send_email", "type": "email"}]
        
        return metadata
    
    def _is_high_confidence(self, metadata: Dict[str, Any]) -> bool:
        """判断元数据置信度是否足够高"""
        # 简单判断：如果有明确的匹配结果，认为置信度高
        total_matches = (
            len(metadata.get("tools", [])) +
            len(metadata.get("sap_services", [])) +
            len(metadata.get("business_entities", []))
        )
        return total_matches > 0


class MetadataFirstIntentRecognizer:
    """元数据前置意图识别器"""
    
    def __init__(self, llm_service=None):
        """
        初始化意图识别器
        
        Args:
            llm_service: LLM服务（可选，默认使用deepseek_llm）
        """
        self.llm = llm_service or deepseek_llm
        self.metadata_retriever = MetadataRetriever()
        self.metadata_cache = MetadataCache(maxsize=1000, ttl=300)  # 5分钟缓存
        self.intent_cache = MetadataCache(maxsize=500, ttl=600)  # 10分钟缓存
        
        # 性能监控
        try:
            from .intent_performance_monitor import get_performance_monitor
            self.performance_monitor = get_performance_monitor()
        except Exception as e:
            logger.warning(f"Failed to initialize performance monitor: {e}")
            self.performance_monitor = None
    
    async def recognize_intent(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """
        识别用户意图（元数据前置）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            conversation_history: 对话历史
            
        Returns:
            意图分析结果
        """
        # 延迟导入以避免循环导入
        from .conversation_agent import IntentAnalysis, TaskType
        
        # 性能监控：记录开始时间
        start_time = time.time()
        metadata_time = None
        llm_time = None
        classification_time = None
        cache_hit = False
        
        # 检查缓存
        cache_key = self._generate_cache_key(user_input, context)
        cached_result = self.intent_cache.get(user_input, context)
        if cached_result:
            user_lower = user_input.lower()
            has_sap_keyword = (
                "sap" in user_lower
                or "erp" in user_lower
                or any(kw in user_input for kw in ["销售订单", "采购订单", "物料", "客户", "供应商"])
            )
            if ("sap_query" in cached_result.required_tools) and not has_sap_keyword:
                cached_result = None
        if cached_result:
            logger.debug(f"Using cached intent result for: {user_input[:50]}")
            cache_hit = True
            elapsed_time = (time.time() - start_time) * 1000
            
            # 记录性能指标
            if self.performance_monitor:
                self.performance_monitor.record_request(
                    user_input=user_input,
                    task_type=cached_result.task_type.value,
                    elapsed_time_ms=elapsed_time,
                    cache_hit=True,
                    success=True
                )
            
            return cached_result
        
        try:
            # 1. 检索元数据（带缓存）
            metadata_start = time.time()
            metadata = await self._get_metadata_with_cache(user_input, context)
            metadata_time = (time.time() - metadata_start) * 1000
            
            # 2. 基于元数据的LLM理解
            llm_start = time.time()
            understanding = await self._llm_understanding_with_metadata(
                user_input,
                metadata,
                conversation_history,
                context
            )
            llm_time = (time.time() - llm_start) * 1000
            
            # 3. 动态分类
            classification_start = time.time()
            intent_analysis = await self._dynamic_classification(
                understanding,
                metadata,
                context
            )
            classification_time = (time.time() - classification_start) * 1000
            
            # 缓存结果
            self.intent_cache.set(user_input, intent_analysis, context)
            
            elapsed_time = (time.time() - start_time) * 1000
            
            # 记录性能指标
            if self.performance_monitor:
                self.performance_monitor.record_request(
                    user_input=user_input,
                    task_type=intent_analysis.task_type.value,
                    elapsed_time_ms=elapsed_time,
                    cache_hit=False,
                    metadata_time_ms=metadata_time,
                    llm_time_ms=llm_time,
                    classification_time_ms=classification_time,
                    success=True
                )
            
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Error in metadata-first intent recognition: {str(e)}", exc_info=True)
            
            elapsed_time = (time.time() - start_time) * 1000
            
            # 记录错误
            if self.performance_monitor:
                self.performance_monitor.record_request(
                    user_input=user_input,
                    task_type="unknown",
                    elapsed_time_ms=elapsed_time,
                    cache_hit=False,
                    success=False,
                    error=str(e)
                )
            
            # 降级到基础LLM理解
            return await self._fallback_to_basic_llm(user_input, conversation_history, context)
    
    async def _get_metadata_with_cache(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取元数据（带缓存）"""
        # 检查缓存
        cached_metadata = self.metadata_cache.get(user_input, context)
        if cached_metadata:
            logger.debug(f"Using cached metadata for: {user_input[:50]}")
            return cached_metadata
        
        # 检索元数据
        metadata = await self.metadata_retriever.retrieve_metadata_fast(user_input, context)
        
        # 缓存结果
        self.metadata_cache.set(user_input, metadata, context)
        
        return metadata
    
    async def _llm_understanding_with_metadata(
        self,
        user_input: str,
        metadata: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """基于元数据的LLM理解"""
        
        # 构建元数据上下文
        metadata_context = self._format_metadata_context(metadata)
        
        # 构建提示词
        system_prompt = f"""你是一个企业业务助手，基于以下业务元数据理解用户需求：

# 业务上下文
{metadata_context}

用户输入: "{user_input}"

请基于以上业务元数据，分析用户的真实业务意图，包括：
1. 涉及哪些具体的业务实体？
2. 想要执行什么业务操作？
3. 需要哪些数据或服务？
4. 业务场景和目标是什么？

# 重要规则（SAP查询）：
如果用户查询SAP数据，必须从业务实体元数据中提取表名：
- 如果业务实体元数据中包含 "sap_table_name" 字段，使用该值作为表名
- 如果没有元数据，根据实体名称推断：
  * "采购订单" / "purchase order" → 表名: "I_PurchaseOrder"
  * "销售订单" / "sales order" → 表名: "I_SalesOrder"
  * "物料" / "material" → 表名: "I_Material"
  * "客户" / "customer" → 表名: "I_Customer"
  * "供应商" / "vendor" → 表名: "I_Vendor"

返回JSON格式：
{{
    "entities": ["实体1", "实体2"],
    "operation": "操作类型",
    "required_services": ["服务1", "服务2"],
    "required_tools": ["工具1", "工具2"],
    "business_scenario": "业务场景描述",
    "parameters": {{
        "table": "SAP表名（如果是SAP查询）",
        "query": "查询条件（可选）",
        "其他参数": "参数值"
    }},
    "confidence": 0.0-1.0
}}"""
        
        messages = []
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history[-20:])  # 增加到20条，保持更长的对话上下文
        
        # 添加系统提示
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 添加用户输入
        messages.append({
            "role": "user",
            "content": user_input
        })
        
            # 调用LLM
        try:
            # 检查LLM是否可用
            if not self.llm or not hasattr(self.llm, 'chat'):
                logger.warning("LLM not available, returning default understanding")
                return {
                    "entities": [],
                    "operation": "unknown",
                    "confidence": 0.5
                }
            
            response = await self.llm.chat(
                messages=messages,
                temperature=0.7
            )
            
            # 解析响应
            understanding = {"entities": [], "operation": "unknown", "confidence": 0.5}
            
            if isinstance(response, str):
                try:
                    # 尝试解析JSON
                    understanding = json.loads(response)
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试提取关键信息
                    logger.warning(f"LLM response is not JSON: {response}")
                    # 简单提取操作类型
                    if "邮件" in response or "email" in response.lower():
                        understanding["operation"] = "send_email"
                        understanding["required_tools"] = ["send_email"]
                    else:
                        user_lower = user_input.lower()
                        sap_hit = (
                            "sap" in user_lower
                            or "erp" in user_lower
                            or any(kw in user_input for kw in ["销售订单", "采购订单", "物料", "客户", "供应商"])
                        )
                        if sap_hit:
                            understanding["operation"] = "sap_query"
                            understanding["required_tools"] = ["sap_query"]
            elif isinstance(response, dict):
                understanding = response
            elif hasattr(response, 'content'):
                # LangChain消息对象
                content = response.content
                if isinstance(content, str):
                    try:
                        understanding = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning(f"LLM response content is not JSON: {content}")
            
            return understanding
            
        except Exception as e:
            logger.error(f"Error in LLM understanding: {str(e)}", exc_info=True)
            return {
                "entities": [],
                "operation": "unknown",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _format_metadata_context(self, metadata: Dict[str, Any]) -> str:
        """格式化元数据上下文（包含详细信息）"""
        context_parts = []
        
        # 工具元数据
        tools = metadata.get("tools", [])
        if tools:
            tool_info = []
            for t in tools[:5]:
                name = t.get("name", "")
                desc = t.get("description", "")
                if desc:
                    tool_info.append(f"{name} ({desc[:50]})")
                else:
                    tool_info.append(name)
            context_parts.append(f"可用工具: {', '.join(tool_info)}")
        
        # SAP服务元数据
        sap_services = metadata.get("sap_services", [])
        if sap_services:
            service_info = [s.get("name", "") for s in sap_services[:5]]
            context_parts.append(f"SAP服务: {', '.join(service_info)}")
        
        # 业务实体元数据（重要：包含表名信息）
        business_entities = metadata.get("business_entities", [])
        if business_entities:
            entity_info = []
            for e in business_entities[:5]:
                name = e.get("name", "") or e.get("display_name", "")
                table_name = e.get("sap_table_name") or e.get("table_name") or e.get("metadata", {}).get("sap_table_name")
                if table_name:
                    entity_info.append(f"{name} (表: {table_name})")
                else:
                    entity_info.append(name)
            context_parts.append(f"业务实体: {', '.join(entity_info)}")
        else:
            # 如果没有业务实体元数据，提供默认映射提示
            context_parts.append("业务实体映射规则: 采购订单→I_PurchaseOrder, 销售订单→I_SalesOrder, 物料→I_Material, 客户→I_Customer, 供应商→I_Vendor")
        
        # 工作流元数据
        workflows = metadata.get("workflows", [])
        if workflows:
            workflow_names = [w.get("name", "") for w in workflows[:3]]
            context_parts.append(f"相关工作流: {', '.join(workflow_names)}")
        
        return "\n".join(context_parts) if context_parts else "暂无相关业务元数据"
    
    async def _dynamic_classification(
        self,
        understanding: Dict[str, Any],
        metadata: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        # 延迟导入以避免循环导入
        from .conversation_agent import IntentAnalysis, TaskType
        """动态分类（基于理解和元数据）"""
        
        # 提取信息
        operation = understanding.get("operation", "unknown")
        required_tools = understanding.get("required_tools", [])
        required_services = understanding.get("required_services", [])
        confidence = understanding.get("confidence", 0.5)
        
        # 动态确定任务类型
        task_type = self._determine_task_type(operation, required_tools, required_services, metadata)
        
        # 构建意图分析结果
        return IntentAnalysis(
            task_type=task_type,
            confidence=float(confidence),
            extracted_context={
                "entities": understanding.get("entities", []),
                "parameters": understanding.get("parameters", {}),
                "business_scenario": understanding.get("business_scenario", ""),
                "metadata": metadata
            },
            required_tools=required_tools,
            required_services=required_services,
            reasoning=f"基于元数据理解：{understanding.get('business_scenario', operation)}"
        )
    
    def _determine_task_type(
        self,
        operation: str,
        required_tools: List[str],
        required_services: List[str],
        metadata: Dict[str, Any]
    ):
        # 延迟导入以避免循环导入
        from .conversation_agent import TaskType
        """动态确定任务类型"""
        
        operation_lower = operation.lower()
        
        # 检查是否有工具需求
        if required_tools or metadata.get("tools"):
            return TaskType.TOOL_EXECUTION
        
        # 检查是否是SAP相关
        if "sap" in operation_lower or required_services or metadata.get("sap_services"):
            return TaskType.TOOL_EXECUTION
        
        # 检查是否是工作流相关
        if "workflow" in operation_lower or "流程" in operation_lower or metadata.get("workflows"):
            return TaskType.WORKFLOW_TASK
        
        # 检查是否是知识搜索
        if "search" in operation_lower or "查询" in operation_lower or "查找" in operation_lower:
            return TaskType.KNOWLEDGE_SEARCH
        
        # 检查是否是复杂分析
        if "分析" in operation_lower or "analysis" in operation_lower:
            return TaskType.COMPLEX_ANALYSIS
        
        # 默认简单查询
        return TaskType.SIMPLE_QUERY
    
    async def _fallback_to_basic_llm(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        # 延迟导入以避免循环导入
        from .conversation_agent import IntentAnalysis, TaskType
        """降级到基础LLM理解"""
        logger.warning("Falling back to basic LLM understanding")
        
        # 使用简单的LLM理解
        try:
            messages = []
            if conversation_history:
                messages.extend(conversation_history[-20:])  # 增加到20条，保持更长的对话上下文
            
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            response = await self.llm.chat(messages=messages, temperature=0.7)
            
            # 简单分类
            user_lower = user_input.lower()
            if any(kw in user_lower for kw in ["sap", "查询", "工具", "执行"]):
                task_type = TaskType.TOOL_EXECUTION
            else:
                task_type = TaskType.SIMPLE_QUERY
            
            return IntentAnalysis(
                task_type=task_type,
                confidence=0.5,
                extracted_context={"fallback": True},
                required_tools=[],
                required_services=[],
                reasoning="降级到基础LLM理解"
            )
        except Exception as e:
            logger.error(f"Error in fallback LLM: {str(e)}")
            return IntentAnalysis(
                task_type=TaskType.UNKNOWN,
                confidence=0.0,
                extracted_context={"error": str(e)},
                required_tools=[],
                required_services=[],
                reasoning="降级失败"
            )
    
    def _generate_cache_key(self, user_input: str, context: Optional[Dict] = None) -> str:
        """生成缓存键"""
        key_data = {
            "input": user_input.lower().strip(),
            "context": context or {}
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode()).hexdigest()

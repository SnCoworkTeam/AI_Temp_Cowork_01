"""
知识库智能体（增强版）
专门处理知识库查询、语义搜索、知识图谱操作
支持动态参数优化、智能路由、结果缓存等功能
"""
import logging
import hashlib
import time
from typing import Dict, Any, Optional, List
import json

from .base_agent import IntelligentAgent
from ..llm_integration import deepseek_llm

logger = logging.getLogger(__name__)


class KnowledgeBaseAgent(IntelligentAgent):
    """知识库智能体 - 增强版，支持动态优化、智能路由、缓存等"""
    
    def __init__(self, knowledge_client=None):
        """
        初始化知识库智能体
        
        Args:
            knowledge_client: Knowledge Base客户端（可选，默认使用service_clients）
        """
        super().__init__(
            agent_id="knowledge_base_agent",
            name="知识库智能体",
            description="专门处理知识库查询、语义搜索、知识图谱操作，包括智能检索、相关概念查找、知识图谱查询",
            capabilities={
                "semantic_search": "语义搜索",
                "keyword_search": "关键词搜索",
                "hybrid_search": "混合搜索",
                "knowledge_graph_query": "知识图谱查询",
                "related_concepts": "相关概念查找",
                "document_retrieval": "文档检索"
            }
        )
        # 延迟导入避免循环依赖
        if knowledge_client is None:
            from ..service_clients import service_clients
            self.knowledge_client = service_clients.knowledge_base
        else:
            self.knowledge_client = knowledge_client
        self.llm = deepseek_llm
        
        # 缓存机制
        self._query_cache: Dict[str, Dict[str, Any]] = {}
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 缓存有效期（秒）
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get("timestamp", 0)
        return time.time() - timestamp < self._cache_ttl
    
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析知识库查询需求（带缓存）
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            分析结果，包含查询类型、参数等
        """
        # 检查缓存
        cache_key = self._generate_cache_key("analyze_task", task_description, context)
        if cache_key in self._analysis_cache:
            cached = self._analysis_cache[cache_key]
            if self._is_cache_valid(cached):
                logger.debug(f"Using cached analysis for: {task_description[:50]}")
                return cached["data"]
            else:
                del self._analysis_cache[cache_key]
        
        if not self.llm:
            logger.warning("LLM not available for KnowledgeBaseAgent, falling back to basic analysis.")
            result = {
                "can_handle": True,
                "query_type": "semantic_search",
                "query": task_description,
                "reason": "LLM not available, using default semantic search."
            }
            # 缓存结果
            self._analysis_cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            return result
        
        prompt = f"""
作为知识库专家，分析以下查询需求，确定最佳的检索策略。

查询: {task_description}
上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

请分析：
1. **查询类型**：语义搜索、关键词搜索、混合搜索、知识图谱查询、相关概念查找？
2. **查询参数**：提取查询关键词、主题、实体等
3. **检索策略**：如何优化检索以获得最佳结果？
4. **结果需求**：需要多少结果？需要什么格式？

返回JSON格式的分析结果，例如：
{{
    "can_handle": true,
    "query_type": "semantic_search",  // semantic_search, keyword_search, hybrid_search, knowledge_graph, related_concepts
    "query": "提取的查询文本",
    "keywords": ["关键词1", "关键词2"],  // 用于关键词搜索或混合搜索
    "search_params": {{
        "top_k": 10,
        "min_score": 0.3,
        "semantic_weight": 0.7,  // 混合搜索时使用
        "keyword_weight": 0.3
    }},
    "knowledge_graph_params": {{
        "node_type": "概念",  // 可选
        "limit": 100
    }},
    "related_concepts_params": {{
        "concept": "概念名称",
        "limit": 10
    }},
    "reason": "分析原因和策略"
}}
如果无法处理，返回 {{"can_handle": false, "reason": "..."}}
"""
        
        try:
            # 从提示词模板获取系统提示词
            from ..prompt_utils import get_system_prompt
            system_prompt = get_system_prompt(
                "knowledge_base_agent",
                fallback="你是一个知识库专家，擅长分析查询需求并选择最佳检索策略。"
            )
            
            response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            analysis = json.loads(response.content)
            analysis["can_handle"] = analysis.get("can_handle", True)
            
            # 缓存结果
            self._analysis_cache[cache_key] = {
                "data": analysis,
                "timestamp": time.time()
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error in KnowledgeBaseAgent.analyze_task: {e}", exc_info=True)
            result = {
                "can_handle": True,
                "query_type": "semantic_search",
                "query": task_description,
                "reason": f"LLM analysis failed: {str(e)}, using default semantic search."
            }
            # 缓存失败结果（较短TTL）
            self._analysis_cache[cache_key] = {
                "data": result,
                "timestamp": time.time()
            }
            return result
    
    async def _parse_and_optimize_query(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        动态解析和优化查询（智能查询路由）
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            解析和优化后的查询信息
        """
        # 提取原始查询
        task = input_data.get("task", input_data.get("task_description", input_data.get("query", "")))
        
        # 尝试从analyze_task获取分析结果
        query_plan = input_data.get("query_plan")
        if not query_plan:
            query_plan = input_data.get("execution_plan", {})
        
        # 如果没有查询计划，使用analyze_task生成
        if not query_plan or not query_plan.get("query_type"):
            query_plan = await self.analyze_task(task, context)
        
        # 提取基本信息
        query_type = query_plan.get("query_type", "semantic_search")
        query = query_plan.get("query", task)
        
        # 动态优化参数
        optimized_params = await self._optimize_search_parameters(
            query=query,
            query_type=query_type,
            base_params=query_plan.get("search_params", {}),
            context=context
        )
        
        return {
            "original_query": task,
            "query": query,
            "query_type": query_type,
            "keywords": query_plan.get("keywords", []),
            "optimized_params": optimized_params,
            "knowledge_graph_params": query_plan.get("knowledge_graph_params", {}),
            "related_concepts_params": query_plan.get("related_concepts_params", {}),
            "confidence": query_plan.get("confidence", 0.8),
            "reason": query_plan.get("reason", "")
        }
    
    async def _optimize_search_parameters(
        self,
        query: str,
        query_type: str,
        base_params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        动态优化搜索参数
        
        Args:
            query: 查询文本
            query_type: 查询类型
            base_params: 基础参数
            context: 上下文信息
            
        Returns:
            优化后的参数
        """
        # 如果已经有明确的参数，直接使用
        if base_params and all(k in base_params for k in ["top_k", "min_score"]):
            return base_params
        
        # 对于简单查询，使用快速启发式规则
        query_length = len(query)
        if query_length < 10:
            # 短查询，可能需要更多结果
            optimized = {
                "top_k": base_params.get("top_k", 15),
                "min_score": base_params.get("min_score", 0.2),
                "semantic_weight": base_params.get("semantic_weight", 0.6),
                "keyword_weight": base_params.get("keyword_weight", 0.4)
            }
        elif query_length > 100:
            # 长查询，更精确匹配
            optimized = {
                "top_k": base_params.get("top_k", 5),
                "min_score": base_params.get("min_score", 0.5),
                "semantic_weight": base_params.get("semantic_weight", 0.8),
                "keyword_weight": base_params.get("keyword_weight", 0.2)
            }
        else:
            # 中等长度，使用默认值
            optimized = {
                "top_k": base_params.get("top_k", 10),
                "min_score": base_params.get("min_score", 0.3),
                "semantic_weight": base_params.get("semantic_weight", 0.7),
                "keyword_weight": base_params.get("keyword_weight", 0.3)
            }
        
        # 对于混合搜索，确保权重和为1
        if query_type == "hybrid_search":
            total_weight = optimized.get("semantic_weight", 0.7) + optimized.get("keyword_weight", 0.3)
            if total_weight != 1.0:
                optimized["semantic_weight"] = optimized.get("semantic_weight", 0.7) / total_weight
                optimized["keyword_weight"] = optimized.get("keyword_weight", 0.3) / total_weight
        
        return optimized
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行知识库查询（增强版）
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            查询结果（统一格式）
        """
        start_time = time.time()
        
        try:
            # 1. 智能查询解析和优化
            parsed_query = await self._parse_and_optimize_query(input_data, context)
            
            # 2. 检查查询缓存
            cache_key = self._generate_cache_key(
                "execute",
                parsed_query["query"],
                parsed_query["query_type"],
                parsed_query["optimized_params"]
            )
            if cache_key in self._query_cache:
                cached = self._query_cache[cache_key]
                if self._is_cache_valid(cached):
                    logger.debug(f"Using cached query result for: {parsed_query['query'][:50]}")
                    result = cached["data"].copy()
                    result["cached"] = True
                    return result
                else:
                    del self._query_cache[cache_key]
            
            # 3. 智能路由执行
            raw_result = await self._execute_intelligent_search(parsed_query)
            
            # 4. 统一结果处理
            standardized_result = self._standardize_and_enrich_result(
                raw_result=raw_result,
                parsed_query=parsed_query,
                execution_time=time.time() - start_time
            )
            
            # 5. 缓存结果
            self._query_cache[cache_key] = {
                "data": standardized_result,
                "timestamp": time.time()
            }
            
            return {
                "agent_type": self.name,
                "execution_success": True,
                "query_info": {
                    "query_type": parsed_query["query_type"],
                    "query": parsed_query["query"],
                    "confidence": parsed_query.get("confidence", 0.8)
                },
                "result": standardized_result,
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"KnowledgeBaseAgent execution failed: {e}", exc_info=True)
            # 错误降级处理
            return await self._handle_search_failure(e, input_data, context)
    
    async def _execute_intelligent_search(
        self,
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        智能路由执行搜索
        
        Args:
            parsed_query: 解析后的查询信息
            
        Returns:
            原始搜索结果
        """
        query_type = parsed_query["query_type"]
        query = parsed_query["query"]
        params = parsed_query["optimized_params"]
        
        logger.info(f"KnowledgeBaseAgent executing {query_type} query: {query}")
        
        # 根据查询类型路由
        if query_type == "semantic_search":
            return await self._semantic_search(query, params)
        elif query_type == "keyword_search":
            keywords = parsed_query.get("keywords", [])
            if not keywords:
                keywords = query.split()
            return await self._keyword_search(keywords, params)
        elif query_type == "hybrid_search":
            keywords = parsed_query.get("keywords", [])
            return await self._hybrid_search(query, keywords, params)
        elif query_type == "knowledge_graph":
            return await self._knowledge_graph_query(parsed_query.get("knowledge_graph_params", {}))
        elif query_type == "related_concepts":
            concept = parsed_query.get("related_concepts_params", {}).get("concept", query)
            return await self._related_concepts(concept, parsed_query.get("related_concepts_params", {}))
        else:
            # 默认降级到语义搜索
            logger.warning(f"Unknown query type: {query_type}, falling back to semantic_search")
            return await self._semantic_search(query, params)
    
    def _standardize_and_enrich_result(
        self,
        raw_result: Dict[str, Any],
        parsed_query: Dict[str, Any],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        统一不同查询类型的结果格式
        
        Args:
            raw_result: 原始搜索结果
            parsed_query: 解析后的查询信息
            execution_time: 执行时间
            
        Returns:
            标准化后的结果
        """
        query_type = parsed_query["query_type"]
        
        # 提取数据（处理不同格式）
        if query_type in ["semantic_search", "keyword_search", "hybrid_search"]:
            data = raw_result.get("results", [])
            total_count = raw_result.get("total", len(data))
        elif query_type == "knowledge_graph":
            # 知识图谱结果转换为统一格式
            nodes = raw_result.get("nodes", [])
            edges = raw_result.get("edges", [])
            data = {
                "nodes": nodes,
                "edges": edges
            }
            total_count = raw_result.get("total_nodes", len(nodes))
        elif query_type == "related_concepts":
            # 相关概念结果转换为统一格式
            concepts = raw_result.get("related_concepts", [])
            relationships = raw_result.get("relationships", [])
            data = {
                "concepts": concepts,
                "relationships": relationships
            }
            total_count = raw_result.get("total_related", len(concepts))
        else:
            data = raw_result
            total_count = 0
        
        # 生成格式化输出
        formatted_output = self._format_for_display(raw_result, query_type, parsed_query)
        
        return {
            "query_type": query_type,
            "data": data,
            "metadata": {
                "total_count": total_count,
                "search_params": parsed_query.get("optimized_params", {}),
                "execution_time": execution_time,
                "query": parsed_query["query"]
            },
            "formatted_output": formatted_output,
            "raw_result": raw_result  # 保留原始结果用于调试
        }
    
    def _format_for_display(
        self,
        raw_result: Dict[str, Any],
        query_type: str,
        parsed_query: Dict[str, Any]
    ) -> str:
        """
        格式化结果用于显示
        
        Args:
            raw_result: 原始结果
            query_type: 查询类型
            parsed_query: 解析后的查询信息
            
        Returns:
            格式化后的文本
        """
        if query_type in ["semantic_search", "keyword_search", "hybrid_search"]:
            results = raw_result.get("results", [])
            total = raw_result.get("total", 0)
            
            if not results:
                return f"未找到相关结果（查询：{parsed_query['query']}）"
            
            lines = [f"找到 {total} 条相关结果：\n"]
            for i, result in enumerate(results[:10], 1):  # 最多显示10条
                score = result.get("score", result.get("similarity", 0))
                content = result.get("content", result.get("text", ""))
                doc_id = result.get("document_id", result.get("id", ""))
                
                lines.append(f"{i}. [相似度: {score:.2f}] {content[:200]}...")
                if doc_id:
                    lines.append(f"   文档ID: {doc_id}\n")
            
            return "\n".join(lines)
        
        elif query_type == "knowledge_graph":
            nodes = raw_result.get("nodes", [])
            edges = raw_result.get("edges", [])
            return f"知识图谱查询结果：{len(nodes)} 个节点，{len(edges)} 条边"
        
        elif query_type == "related_concepts":
            concepts = raw_result.get("related_concepts", [])
            return f"找到 {len(concepts)} 个相关概念"
        
        return str(raw_result)
    
    async def _handle_search_failure(
        self,
        error: Exception,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理搜索失败（带降级策略）
        
        Args:
            error: 错误对象
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            错误结果或降级结果
        """
        error_msg = str(error)
        logger.error(f"Search failed: {error_msg}")
        
        # 尝试降级策略
        try:
            # 降级1: 尝试简单的语义搜索
            query = input_data.get("query", input_data.get("task", ""))
            if query:
                logger.info("Attempting fallback to simple semantic search")
                fallback_result = await self._semantic_search(
                    query=query,
                    params={"top_k": 5, "min_score": 0.1}
                )
                standardized = self._standardize_and_enrich_result(
                    raw_result=fallback_result,
                    parsed_query={
                        "query_type": "semantic_search",
                        "query": query,
                        "optimized_params": {}
                    },
                    execution_time=0
                )
                return {
                    "agent_type": self.name,
                    "execution_success": True,
                    "query_info": {
                        "query_type": "semantic_search",
                        "query": query
                    },
                    "result": standardized,
                    "warning": f"原始查询失败，已降级到简单搜索: {error_msg}",
                    "cached": False
                }
        except Exception as fallback_error:
            logger.error(f"Fallback search also failed: {fallback_error}")
        
        # 如果降级也失败，返回错误结果
        return {
            "agent_type": self.name,
            "execution_success": False,
            "error": error_msg,
            "message": f"知识库查询失败：{error_msg}",
            "result": {
                "query_type": "unknown",
                "data": [],
                "metadata": {
                    "total_count": 0,
                    "error": error_msg
                },
                "formatted_output": f"查询失败：{error_msg}"
            }
        }
    
    async def _semantic_search(
        self,
        query: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行语义搜索"""
        try:
            top_k = params.get("top_k", 10)
            min_score = params.get("min_score", 0.3)
            filters = params.get("filters", {})
            
            result = await self.knowledge_client.semantic_search(
                query=query,
                top_k=top_k,
                min_score=min_score,
                filters=filters
            )
            
            return {
                "search_type": "semantic",
                "query": query,
                "results": result.get("results", []),
                "total": result.get("total", 0),
                "top_k": top_k,
                "min_score": min_score
            }
        except Exception as e:
            logger.error(f"Semantic search failed: {e}", exc_info=True)
            raise
    
    async def _keyword_search(
        self,
        keywords: List[str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行关键词搜索"""
        try:
            match_all = params.get("match_all", False)
            page = params.get("page", 1)
            page_size = params.get("page_size", 10)
            
            result = await self.knowledge_client.keyword_search(
                keywords=keywords,
                match_all=match_all,
                page=page,
                page_size=page_size
            )
            
            return {
                "search_type": "keyword",
                "keywords": keywords,
                "results": result.get("results", []),
                "total": result.get("total", 0),
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"Keyword search failed: {e}", exc_info=True)
            raise
    
    async def _hybrid_search(
        self,
        query: str,
        keywords: List[str],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行混合搜索"""
        try:
            top_k = params.get("top_k", 10)
            semantic_weight = params.get("semantic_weight", 0.7)
            keyword_weight = params.get("keyword_weight", 0.3)
            
            result = await self.knowledge_client.hybrid_search(
                query=query,
                keywords=keywords,
                top_k=top_k,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight
            )
            
            return {
                "search_type": "hybrid",
                "query": query,
                "keywords": keywords,
                "results": result.get("results", []),
                "total": result.get("total", 0),
                "top_k": top_k,
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight
            }
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}", exc_info=True)
            raise
    
    async def _knowledge_graph_query(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """查询知识图谱"""
        try:
            node_type = params.get("node_type")
            limit = params.get("limit", 100)
            
            result = await self.knowledge_client.get_knowledge_graph(
                node_type=node_type,
                limit=limit
            )
            
            return {
                "query_type": "knowledge_graph",
                "node_type": node_type,
                "nodes": result.get("nodes", []),
                "edges": result.get("edges", []),
                "total_nodes": result.get("total_nodes", 0),
                "total_edges": result.get("total_edges", 0),
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}", exc_info=True)
            raise
    
    async def _related_concepts(
        self,
        concept: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """查找相关概念"""
        try:
            limit = params.get("limit", 10)
            
            result = await self.knowledge_client.get_related_concepts(
                concept=concept,
                limit=limit
            )
            
            return {
                "query_type": "related_concepts",
                "concept": concept,
                "matching_nodes": result.get("matching_nodes", []),
                "related_concepts": result.get("related_concepts", []),
                "relationships": result.get("relationships", []),
                "total_related": result.get("total_related", 0),
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Related concepts query failed: {e}", exc_info=True)
            raise

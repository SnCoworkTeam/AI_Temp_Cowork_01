"""
知识增强节点
集成知识搜索和图谱，增强原始内容
"""
from typing import Dict, Any, Optional, List
import logging

from .base_node import BaseNode, NodeExecutionError
from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings

logger = logging.getLogger(__name__)


class KnowledgeEnhancementNode(BaseNode):
    """知识增强节点 - 使用知识库和图谱增强内容"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        
        # 输入配置
        self.content_source = self.config.get("content_source", "input")  # 内容来源字段
        self.content_field = self.config.get("content_field", "content")  # 内容字段名
        
        # 增强策略配置
        self.enhancement_strategy = self.config.get(
            "enhancement_strategy",
            "search_and_merge"
        )  # search_and_merge, context_expansion, knowledge_graph
        
        # 知识搜索配置
        self.enable_search = self.config.get("enable_search", True)
        self.search_limit = self.config.get("search_limit", 5)
        self.search_min_score = self.config.get("search_min_score", 0.5)
        self.search_type = self.config.get("search_type", "semantic")
        
        # 知识图谱配置
        self.enable_graph = self.config.get("enable_graph", True)
        self.graph_expand_depth = self.config.get("graph_expand_depth", 2)
        self.graph_limit = self.config.get("graph_limit", 10)
        
        # 合并策略配置
        self.merge_mode = self.config.get("merge_mode", "append")  # append, prepend, replace, context
        self.context_format = self.config.get(
            "context_format",
            "markdown"
        )  # markdown, plain, json
        
        # MCP Gateway配置
        self.mcp_gateway_url = self.config.get(
            "mcp_gateway_url",
            settings.MCP_GATEWAY_URL
        )
        self.knowledge_base_url = self.config.get(
            "knowledge_base_url",
            settings.KNOWLEDGE_BASE_URL
        )
        self.timeout = self.config.get("timeout", 60)
        
        # 输出配置
        self.output_key = self.config.get("output_key", f"{self.name}_enhanced")
        self.include_sources = self.config.get("include_sources", True)  # 是否包含来源信息
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识增强节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            # 获取原始内容
            original_content = self._get_original_content(state)
            if not original_content:
                raise NodeExecutionError(
                    self.name,
                    f"Content not found in state field: {self.content_field}"
                )
            
            logger.info(
                f"Knowledge Enhancement Node '{self.name}' enhancing content "
                f"(strategy: {self.enhancement_strategy})"
            )
            
            # 执行增强
            enhancement_results = {}
            
            # 1. 知识搜索增强
            if self.enable_search:
                search_results = await self._enhance_with_search(original_content, state)
                enhancement_results["search"] = search_results
            
            # 2. 知识图谱增强
            if self.enable_graph:
                graph_results = await self._enhance_with_graph(original_content, state)
                enhancement_results["graph"] = graph_results
            
            # 3. 合并增强内容
            enhanced_content = self._merge_enhancement(
                original_content,
                enhancement_results
            )
            
            # 构建输出
            output = {
                "original_content": original_content,
                "enhanced_content": enhanced_content,
                "strategy": self.enhancement_strategy,
                "enhancement_results": enhancement_results,
            }
            
            # 添加来源信息
            if self.include_sources:
                sources = []
                if "search" in enhancement_results:
                    search_data = enhancement_results["search"]
                    for result in search_data.get("results", []):
                        sources.append({
                            "type": "document",
                            "document_id": result.get("document_id"),
                            "document_name": result.get("document_name"),
                            "score": result.get("score"),
                            "chunk_id": result.get("chunk_id"),
                        })
                if "graph" in enhancement_results:
                    graph_data = enhancement_results["graph"]
                    for concept in graph_data.get("related_concepts", []):
                        sources.append({
                            "type": "concept",
                            "concept_id": concept.get("id"),
                            "concept_label": concept.get("label"),
                            "concept_type": concept.get("type"),
                        })
                output["sources"] = sources
            
            # 将结果添加到状态
            state[self.output_key] = output
            state[f"{self.name}_enhanced_content"] = enhanced_content
            state[f"{self.name}_sources"] = output.get("sources", [])
            state[f"{self.name}_success"] = True
            
            logger.info(
                f"Knowledge Enhancement Node '{self.name}' completed: "
                f"enhanced {len(original_content)} chars to {len(enhanced_content)} chars"
            )
            
            return state
        
        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Knowledge Enhancement Node execution failed: {str(e)}",
                e
            )
    
    def _get_original_content(self, state: Dict[str, Any]) -> Optional[str]:
        """
        从状态中获取原始内容
        
        Args:
            state: 工作流状态
        
        Returns:
            原始内容文本
        """
        content = self.get_state_value(state, self.content_field)
        
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # 尝试从字典中获取常见的内容字段
            return content.get("content") or content.get("text") or content.get("message")
        elif isinstance(content, list):
            # 如果是列表，尝试连接
            return "\n".join(str(item) for item in content)
        
        return None
    
    async def _enhance_with_search(self, content: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用知识搜索增强内容
        
        Args:
            content: 原始内容
            state: 工作流状态
        
        Returns:
            搜索结果
        """
        logger.info(f"Enhancing with knowledge search: {content[:50]}...")
        
        # 构建搜索参数
        search_params = {
            "query": content,
            "search_type": self.search_type,
            "limit": self.search_limit,
            "filters": self._resolve_filters(state),
        }
        
        # 调用MCP Gateway的知识搜索工具
        try:
            async with HTTPClient(self.mcp_gateway_url, timeout=self.timeout) as client:
                response = await client.post(
                    "/api/tools/knowledge_search/execute",
                    data={
                        "parameters": search_params,
                        "timeout": self.timeout
                    }
                )
        except Exception as e:
            logger.warning(f"Knowledge search failed: {str(e)}")
            return {"success": False, "error": str(e), "results": []}
        
        if not response.get("success", False):
            return {"success": False, "error": response.get("error"), "results": []}
        
        search_result = response.get("result", {})
        results = search_result.get("results", [])
        
        # 过滤低分结果
        filtered_results = [
            r for r in results
            if r.get("score", 0) >= self.search_min_score
        ]
        
        return {
            "success": True,
            "results": filtered_results,
            "total": len(filtered_results),
        }
    
    async def _enhance_with_graph(self, content: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用知识图谱增强内容
        
        Args:
            content: 原始内容
            state: 工作流状态
        
        Returns:
            图谱结果
        """
        logger.info(f"Enhancing with knowledge graph")
        
        # 从内容中提取关键词（简单实现：取前几个词）
        keywords = content.split()[:5]  # 取前5个词作为种子概念
        
        if not keywords:
            return {"success": False, "error": "No keywords extracted", "related_concepts": []}
        
        # 调用知识图谱工具
        try:
            async with HTTPClient(self.mcp_gateway_url, timeout=self.timeout) as client:
                # 获取相关概念
                response = await client.post(
                    "/api/tools/knowledge_graph/execute",
                    data={
                        "parameters": {
                            "operation": "expand",
                            "seed_concepts": keywords,
                            "depth": self.graph_expand_depth,
                        },
                        "timeout": self.timeout
                    }
                )
        except Exception as e:
            logger.warning(f"Knowledge graph expansion failed: {str(e)}")
            return {"success": False, "error": str(e), "related_concepts": []}
        
        if not response.get("success", False):
            return {"success": False, "error": response.get("error"), "related_concepts": []}
        
        graph_result = response.get("result", {})
        
        return {
            "success": True,
            "related_concepts": graph_result.get("expanded_nodes", [])[:self.graph_limit],
            "relationships": graph_result.get("expanded_edges", []),
            "total_nodes": graph_result.get("total_nodes", 0),
        }
    
    def _resolve_filters(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """解析过滤条件"""
        filters = self.config.get("filters", {})
        if not filters:
            return {}
        
        resolved = {}
        for key, value in filters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = self.get_state_value(state, var_name, value)
            else:
                resolved[key] = value
        return resolved
    
    def _merge_enhancement(
        self,
        original_content: str,
        enhancement_results: Dict[str, Any]
    ) -> str:
        """
        合并增强内容
        
        Args:
            original_content: 原始内容
            enhancement_results: 增强结果
        
        Returns:
            增强后的内容
        """
        if self.merge_mode == "replace":
            # 使用增强内容替换
            return self._format_enhanced_content(enhancement_results)
        
        elif self.merge_mode == "prepend":
            # 在原始内容前添加增强内容
            enhanced = self._format_enhanced_content(enhancement_results)
            return f"{enhanced}\n\n---\n\n{original_content}"
        
        elif self.merge_mode == "append":
            # 在原始内容后添加增强内容
            enhanced = self._format_enhanced_content(enhancement_results)
            return f"{original_content}\n\n---\n\n{enhanced}"
        
        elif self.merge_mode == "context":
            # 将增强内容作为上下文
            context = self._format_enhanced_content(enhancement_results)
            return f"上下文信息：\n{context}\n\n---\n\n原始内容：\n{original_content}"
        
        else:
            # 默认：追加模式
            enhanced = self._format_enhanced_content(enhancement_results)
            return f"{original_content}\n\n---\n\n{enhanced}"
    
    def _format_enhanced_content(self, enhancement_results: Dict[str, Any]) -> str:
        """
        格式化增强内容
        
        Args:
            enhancement_results: 增强结果
        
        Returns:
            格式化后的内容
        """
        parts = []
        
        # 格式化搜索结果
        if "search" in enhancement_results:
            search_data = enhancement_results["search"]
            if search_data.get("success") and search_data.get("results"):
                if self.context_format == "markdown":
                    parts.append("## 相关知识")
                    for i, result in enumerate(search_data["results"], 1):
                        parts.append(
                            f"\n### {i}. {result.get('document_name', '未知文档')}\n"
                            f"{result.get('content', '')[:200]}...\n"
                        )
                else:
                    parts.append("相关知识：")
                    for result in search_data["results"]:
                        parts.append(
                            f"- [{result.get('document_name')}] "
                            f"{result.get('content', '')[:150]}..."
                        )
        
        # 格式化图谱结果
        if "graph" in enhancement_results:
            graph_data = enhancement_results["graph"]
            if graph_data.get("success") and graph_data.get("related_concepts"):
                if self.context_format == "markdown":
                    parts.append("\n## 相关概念")
                    for concept in graph_data["related_concepts"]:
                        parts.append(
                            f"- **{concept.get('label', '未知')}** "
                            f"({concept.get('type', 'concept')})"
                        )
                else:
                    parts.append("\n相关概念：")
                    for concept in graph_data["related_concepts"]:
                        parts.append(f"- {concept.get('label', '未知')}")
        
        return "\n".join(parts) if parts else ""
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        content = self._get_original_content(state)
        if not content:
            logger.warning(
                f"Knowledge Enhancement Node '{self.name}': "
                f"content not found in state field '{self.content_field}'"
            )
            return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        if self.output_key not in output:
            logger.warning(
                f"Knowledge Enhancement Node '{self.name}' did not produce output"
            )
            return False
        
        return True










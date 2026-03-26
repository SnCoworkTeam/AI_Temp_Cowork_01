"""
知识搜索节点
调用知识库MCP工具进行语义搜索和关键词搜索
"""
from typing import Dict, Any, Optional
import logging

from .base_node import BaseNode, NodeExecutionError
from shared_libs.luminaos_common.common.http_client import HTTPClient
from ..config import settings

logger = logging.getLogger(__name__)


class KnowledgeSearchNode(BaseNode):
    """知识搜索节点 - 调用知识库搜索工具"""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None,
        node_id: Optional[str] = None
    ):
        super().__init__(name, description, config, node_id)
        
        # 搜索配置
        self.search_type = self.config.get("search_type", "semantic")  # semantic 或 keyword
        self.query_source = self.config.get("query_source", "input")  # 从状态中的哪个字段获取查询
        self.query_field = self.config.get("query_field", "query")  # 查询字段名
        self.limit = self.config.get("limit", 5)  # 返回结果数量
        self.min_score = self.config.get("min_score", 0.3)  # 最小相似度分数
        self.filters = self.config.get("filters", {})  # 过滤条件
        self.match_all = self.config.get("match_all", False)  # 关键词搜索时是否匹配所有
        
        # MCP Gateway配置
        self.mcp_gateway_url = self.config.get(
            "mcp_gateway_url",
            settings.MCP_GATEWAY_URL
        )
        self.timeout = self.config.get("timeout", 30)
        
        # 输出配置
        self.output_key = self.config.get("output_key", f"{self.name}_results")
        self.summarize = self.config.get("summarize", True)  # 是否生成摘要
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行知识搜索节点
        
        Args:
            state: 当前工作流状态
        
        Returns:
            更新后的状态
        """
        try:
            # 获取搜索查询
            query = self._get_search_query(state)
            if not query:
                raise NodeExecutionError(
                    self.name,
                    f"Search query not found in state field: {self.query_field}"
                )
            
            logger.info(
                f"Knowledge Search Node '{self.name}' searching: {query} "
                f"(type: {self.search_type}, limit: {self.limit})"
            )
            
            # 构建搜索参数
            search_params = self._build_search_params(query, state)
            
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
                raise NodeExecutionError(
                    self.name,
                    f"Failed to call knowledge search tool: {str(e)}",
                    e
                )
            
            # 检查响应
            if not response.get("success", False):
                error_msg = response.get("error", "Unknown error")
                raise NodeExecutionError(
                    self.name,
                    f"Knowledge search failed: {error_msg}"
                )
            
            # 获取搜索结果
            search_result = response.get("result", {})
            results = search_result.get("results", [])
            total = search_result.get("total", 0)
            
            # 生成摘要（如果启用）
            summary = None
            if self.summarize and results:
                summary = self._generate_summary(results)
            
            # 将结果添加到状态
            state[self.output_key] = {
                "query": query,
                "search_type": self.search_type,
                "results": results,
                "total": total,
                "summary": summary,
                "top_results": results[:3] if results else [],
                "document_ids": list(set([r.get("document_id") for r in results if r.get("document_id")])),
            }
            
            # 也添加到根级别（方便访问）
            state[f"{self.name}_search_results"] = results
            state[f"{self.name}_summary"] = summary
            state[f"{self.name}_success"] = True
            
            logger.info(
                f"Knowledge Search Node '{self.name}' completed: "
                f"found {total} results, returning top {len(results)}"
            )
            
            return state
        
        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                self.name,
                f"Knowledge Search Node execution failed: {str(e)}",
                e
            )
    
    def _get_search_query(self, state: Dict[str, Any]) -> Optional[str]:
        """
        从状态中获取搜索查询
        
        Args:
            state: 工作流状态
        
        Returns:
            搜索查询文本
        """
        # 支持多种查询来源
        if self.query_source == "input":
            # 从指定的字段获取
            query = self.get_state_value(state, self.query_field)
            if isinstance(query, str):
                return query
            elif isinstance(query, dict):
                # 如果是字典，尝试获取常见的查询字段
                return query.get("query") or query.get("text") or query.get("content")
        elif self.query_source == "template":
            # 使用模板解析
            template = self.config.get("query_template", "")
            if template:
                return self.resolve_template(template, state)
        
        return None
    
    def _build_search_params(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建搜索参数
        
        Args:
            query: 搜索查询
            state: 工作流状态
        
        Returns:
            搜索参数字典
        """
        params = {
            "query": query,
            "search_type": self.search_type,
            "limit": self.limit,
        }
        
        # 解析过滤条件（支持状态变量引用）
        filters = self._resolve_filters(state)
        if filters:
            params["filters"] = filters
        
        # 关键词搜索特定参数
        if self.search_type == "keyword":
            params["match_all"] = self.match_all
        
        return params
    
    def _resolve_filters(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析过滤条件（支持状态变量引用）
        
        Args:
            state: 工作流状态
        
        Returns:
            解析后的过滤条件
        """
        if not self.filters:
            return {}
        
        resolved = {}
        for key, value in self.filters.items():
            resolved[key] = self._resolve_value(value, state)
        return resolved
    
    def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
        """
        解析值（支持状态变量引用）
        
        Args:
            value: 要解析的值
            state: 工作流状态
        
        Returns:
            解析后的值
        """
        if isinstance(value, str):
            # 检查是否是状态变量引用 ${variable_name}
            if value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                return self.get_state_value(state, var_name, value)
            # 检查是否包含模板变量
            if "${" in value:
                return self.resolve_template(value, state)
            return value
        elif isinstance(value, dict):
            return {k: self._resolve_value(v, state) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(item, state) for item in value]
        else:
            return value
    
    def _generate_summary(self, results: list) -> str:
        """
        生成搜索结果摘要
        
        Args:
            results: 搜索结果列表
        
        Returns:
            摘要文本
        """
        if not results:
            return "未找到相关结果"
        
        summary_parts = [f"找到 {len(results)} 条相关结果："]
        
        for i, result in enumerate(results[:3], 1):
            doc_name = result.get("document_name", "未知文档")
            content = result.get("content", "")
            score = result.get("score", 0)
            
            # 截取内容片段
            content_snippet = content[:100] + "..." if len(content) > 100 else content
            
            summary_parts.append(
                f"{i}. [{doc_name}] ({score:.0%} 匹配): {content_snippet}"
            )
        
        if len(results) > 3:
            summary_parts.append(f"... 还有 {len(results) - 3} 条结果")
        
        return "\n".join(summary_parts)
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """验证输入状态"""
        if not super().validate_input(state):
            return False
        
        # 检查查询字段是否存在
        query = self._get_search_query(state)
        if not query:
            logger.warning(
                f"Knowledge Search Node '{self.name}': "
                f"query not found in state field '{self.query_field}'"
            )
            return False
        
        # 验证搜索类型
        if self.search_type not in ["semantic", "keyword"]:
            logger.warning(
                f"Knowledge Search Node '{self.name}': "
                f"invalid search_type: {self.search_type}"
            )
            return False
        
        return True
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出状态"""
        if not super().validate_output(output):
            return False
        
        # 检查是否有输出
        if self.output_key not in output:
            logger.warning(
                f"Knowledge Search Node '{self.name}' did not produce output"
            )
            return False
        
        return True










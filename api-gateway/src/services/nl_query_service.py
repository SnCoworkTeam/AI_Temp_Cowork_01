"""
自然语言查询服务
将自然语言转换为结构化查询
"""
import logging
import httpx
import os
import json
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class NLQueryService:
    """自然语言查询服务"""
    
    def __init__(self):
        """
        初始化自然语言查询服务
        """
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://chat-service:8006")
        self.llm_api_key = os.getenv("OPENAI_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.enabled = os.getenv("NL_QUERY_ENABLED", "true").lower() == "true"
    
    async def parse_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        解析自然语言查询
        
        Args:
            query: 自然语言查询
            context: 上下文信息（可选）
        
        Returns:
            解析后的查询结构
        """
        if not self.enabled:
            # 降级到简单关键词搜索
            return {
                "type": "keyword_search",
                "keywords": query.split(),
                "intent": "search"
            }
        
        try:
            prompt = self._build_query_parsing_prompt(query, context)
            
            # 调用LLM API
            response = await self.http_client.post(
                f"{self.llm_base_url}/api/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个查询解析专家。将自然语言查询转换为结构化查询格式，返回JSON。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"LLM API returned {response.status_code}")
                return self._fallback_parse(query)
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
            # 解析JSON响应
            parsed_query = json.loads(content)
            return parsed_query
            
        except Exception as e:
            logger.error(f"Failed to parse query with LLM: {e}", exc_info=True)
            return self._fallback_parse(query)
    
    def _build_query_parsing_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """构建查询解析提示词"""
        context_str = ""
        if context:
            context_str = f"\n上下文信息:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
        
        return f"""
分析以下自然语言查询，返回JSON格式：

查询: {query}
{context_str}

请解析查询意图，返回JSON格式：
{{
    "intent": "search|question|recommendation|analysis",
    "entity_type": "entity|document|data_asset|workflow",
    "keywords": ["关键词1", "关键词2"],
    "filters": {{
        "domain": "metadata|knowledge|sap",
        "entity_type": "business_entity|data_asset",
        "relationship_type": "parent_of|related_to"
    }},
    "query_type": "graph_query|keyword_search|semantic_search",
    "graph_query": {{
        "type": "find_related|find_path|get_subgraph",
        "source_entity": "实体名称或ID",
        "target_entity": "实体名称或ID",
        "max_depth": 2
    }}
}}

查询类型说明：
- search: 搜索查询
- question: 问答查询
- recommendation: 推荐查询
- analysis: 分析查询
"""
    
    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """降级解析（简单关键词提取）"""
        keywords = query.split()
        return {
            "intent": "search",
            "keywords": keywords,
            "query_type": "keyword_search",
            "filters": {}
        }
    
    async def execute_graph_query(
        self,
        parsed_query: Dict[str, Any],
        metadata_service_url: str = "http://metadata-service:8005"
    ) -> Dict[str, Any]:
        """
        执行图查询
        
        Args:
            parsed_query: 解析后的查询
            metadata_service_url: metadata-service URL
        
        Returns:
            查询结果
        """
        try:
            graph_query = parsed_query.get("graph_query", {})
            query_type = graph_query.get("type")
            
            if query_type == "find_related":
                # 查找相关实体
                entity_id = graph_query.get("source_entity")
                if isinstance(entity_id, str):
                    # 需要先查找实体ID
                    # 简化处理：假设entity_id是数字
                    try:
                        entity_id = int(entity_id)
                    except ValueError:
                        return {"error": "Invalid entity ID"}
                
                response = await self.http_client.get(
                    f"{metadata_service_url}/api/recommendation/entities/{entity_id}/related",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    return response.json()
            
            elif query_type == "find_path":
                # 查找路径
                source_id = graph_query.get("source_entity")
                target_id = graph_query.get("target_entity")
                
                if isinstance(source_id, str):
                    try:
                        source_id = int(source_id)
                    except ValueError:
                        return {"error": "Invalid source entity ID"}
                
                if isinstance(target_id, str):
                    try:
                        target_id = int(target_id)
                    except ValueError:
                        return {"error": "Invalid target entity ID"}
                
                response = await self.http_client.post(
                    f"{metadata_service_url}/api/recommendation/decision/find-path",
                    json={
                        "source_entity_id": source_id,
                        "target_entity_id": target_id,
                        "max_depth": graph_query.get("max_depth", 5)
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
            
            elif query_type == "get_subgraph":
                # 获取子图
                entity_id = graph_query.get("source_entity")
                if isinstance(entity_id, str):
                    try:
                        entity_id = int(entity_id)
                    except ValueError:
                        return {"error": "Invalid entity ID"}
                
                response = await self.http_client.get(
                    f"{metadata_service_url}/api/knowledge-graph/subgraph/{entity_id}",
                    params={"max_depth": graph_query.get("max_depth", 2)}
                )
                
                if response.status_code == 200:
                    return response.json()
            
            return {"error": "Unsupported query type"}
            
        except Exception as e:
            logger.error(f"Failed to execute graph query: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def explain_result(
        self,
        query: str,
        result: Dict[str, Any]
    ) -> str:
        """
        用自然语言解释查询结果
        
        Args:
            query: 原始查询
            result: 查询结果
        
        Returns:
            自然语言解释
        """
        if not self.enabled:
            return f"找到 {len(result.get('results', []))} 个结果"
        
        try:
            prompt = f"""
用户查询: {query}

查询结果:
{json.dumps(result, indent=2, ensure_ascii=False)}

请用自然语言解释查询结果，简洁明了。
"""
            
            response = await self.http_client.post(
                f"{self.llm_base_url}/api/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个查询结果解释专家。用自然语言解释查询结果。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                explanation = result_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return explanation
            
            return f"找到 {len(result.get('results', []))} 个结果"
            
        except Exception as e:
            logger.error(f"Failed to explain result: {e}", exc_info=True)
            return f"找到 {len(result.get('results', []))} 个结果"
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()





"""
工具元数据向量化服务
将工具元数据转换为向量嵌入，支持语义搜索
"""
import logging
import os
from typing import Dict, Any, List, Optional
import httpx
import asyncio

logger = logging.getLogger(__name__)


class ToolVectorizationService:
    """工具元数据向量化服务"""
    
    def __init__(self):
        self.knowledge_base_url = os.getenv(
            "KNOWLEDGE_BASE_URL",
            "http://knowledge-base:8004"
        )
        self.vector_knowledge_base_id = os.getenv(
            "TOOL_METADATA_KB_ID",
            None  # 如果没有指定，使用默认知识库
        )
        self.timeout = httpx.Timeout(30.0)
    
    async def vectorize_tool_metadata(
        self,
        tool_name: str,
        tool_description: str,
        tool_parameters: Dict[str, Any],
        tool_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        向量化工具元数据
        
        Args:
            tool_name: 工具名称
            tool_description: 工具描述
            tool_parameters: 工具参数Schema
            tool_metadata: 工具元数据
            
        Returns:
            是否成功
        """
        try:
            # 构建工具元数据文档
            tool_doc = self._build_tool_document(
                tool_name, tool_description, tool_parameters, tool_metadata
            )
            
            # 存储到知识库（自动向量化）
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 如果没有指定知识库ID，先查找或创建
                kb_id = await self._get_or_create_tool_kb(client)
                
                if not kb_id:
                    logger.error("Failed to get or create tool metadata knowledge base")
                    return False
                
                # 创建文档（会自动向量化）
                response = await client.post(
                    f"{self.knowledge_base_url}/api/knowledge-bases/{kb_id}/documents",
                    json={
                        "filename": f"tool_{tool_name}.md",
                        "content": tool_doc,
                        "file_type": "text",
                        "tags": ["tool", "metadata", tool_name],
                        "category": "tool_metadata",
                        "process_async": False  # 同步处理，确保向量化完成
                    }
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Tool metadata vectorized: {tool_name}")
                    return True
                else:
                    logger.error(f"Failed to vectorize tool metadata: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error vectorizing tool metadata: {str(e)}", exc_info=True)
            return False
    
    def _build_tool_document(
        self,
        tool_name: str,
        tool_description: str,
        tool_parameters: Dict[str, Any],
        tool_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建工具元数据文档"""
        
        # 提取参数信息
        param_descriptions = []
        if isinstance(tool_parameters, dict) and "properties" in tool_parameters:
            for param_name, param_info in tool_parameters["properties"].items():
                param_desc = param_info.get("description", "")
                param_type = param_info.get("type", "string")
                param_descriptions.append(f"- {param_name} ({param_type}): {param_desc}")
        
        # 提取元数据标签
        tags = []
        if tool_metadata:
            tags = tool_metadata.get("tags", [])
            category = tool_metadata.get("category", "")
            if category:
                tags.append(category)
        
        # 构建文档
        doc = f"""# {tool_name}

## 描述
{tool_description}

## 功能
这是一个MCP工具，用于执行特定任务。

## 参数
{chr(10).join(param_descriptions) if param_descriptions else "无参数"}

## 使用场景
"""
        
        # 添加使用场景（从元数据中提取）
        if tool_metadata:
            use_cases = tool_metadata.get("use_cases", [])
            if use_cases:
                for use_case in use_cases:
                    doc += f"- {use_case}\n"
            else:
                # 从描述中推断使用场景
                doc += f"- {tool_description}\n"
        
        # 添加标签
        if tags:
            doc += f"\n## 标签\n{', '.join(tags)}\n"
        
        # 添加业务领域
        if tool_metadata:
            business_domain = tool_metadata.get("business_domain")
            if business_domain:
                doc += f"\n## 业务领域\n{business_domain}\n"
        
        return doc
    
    async def _get_or_create_tool_kb(self, client: httpx.AsyncClient) -> Optional[str]:
        """获取或创建工具元数据知识库"""
        try:
            # 先尝试查找现有的工具元数据知识库
            response = await client.get(
                f"{self.knowledge_base_url}/api/knowledge-bases",
                params={"search": "tool_metadata", "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                kb_list = data if isinstance(data, list) else data.get("items", [])
                
                # 查找工具元数据知识库
                for kb in kb_list:
                    if kb.get("name") == "工具元数据" or "tool_metadata" in kb.get("name", "").lower():
                        return kb.get("id")
            
            # 如果没有找到，创建一个新的
            response = await client.post(
                f"{self.knowledge_base_url}/api/knowledge-bases",
                json={
                    "name": "工具元数据",
                    "description": "MCP工具元数据向量化存储，用于语义搜索",
                    "embedding_model": "default",
                    "chunk_strategy": "semantic"
                }
            )
            
            if response.status_code in [200, 201]:
                kb_data = response.json()
                kb_id = kb_data.get("id") if isinstance(kb_data, dict) else kb_data
                logger.info(f"Created tool metadata knowledge base: {kb_id}")
                return kb_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting or creating tool KB: {str(e)}")
            return None
    
    async def search_tools_by_semantics(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        通过语义搜索工具
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            
        Returns:
            工具列表
        """
        try:
            # 获取工具元数据知识库ID
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                kb_id = await self._get_or_create_tool_kb(client)
                
                if not kb_id:
                    return []
                
                # 语义搜索
                response = await client.post(
                    f"{self.knowledge_base_url}/api/knowledge-bases/{kb_id}/search/semantic",
                    json={
                        "query": query,
                        "top_k": limit
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", []) if isinstance(data, dict) else data
                    
                    # 从搜索结果中提取工具信息
                    tools = []
                    for result in results:
                        # 从文档内容中解析工具名称
                        content = result.get("content", "")
                        metadata = result.get("metadata", {})
                        
                        # 尝试从文件名或标签中提取工具名称
                        filename = metadata.get("filename", "")
                        if filename.startswith("tool_"):
                            tool_name = filename.replace("tool_", "").replace(".md", "")
                            tools.append({
                                "name": tool_name,
                                "score": result.get("score", 0.0),
                                "content": content
                            })
                    
                    return tools
                
                return []
                
        except Exception as e:
            logger.error(f"Error searching tools by semantics: {str(e)}")
            return []


# 全局实例
_tool_vectorization_service = None


def get_tool_vectorization_service() -> ToolVectorizationService:
    """获取工具向量化服务实例（单例）"""
    global _tool_vectorization_service
    if _tool_vectorization_service is None:
        _tool_vectorization_service = ToolVectorizationService()
    return _tool_vectorization_service



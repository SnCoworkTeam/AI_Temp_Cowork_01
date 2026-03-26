"""
Memory Service客户端
用于与Memory Service交互
"""
import logging
import httpx
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryClient:
    """Memory Service客户端"""
    
    def __init__(self):
        self.base_url = os.getenv("MEMORY_SERVICE_URL", "http://memory-service:8013")
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def store_memory(
        self,
        user_id: str,
        agent_id: Optional[str],
        session_id: Optional[str],
        memory_type: str,
        content: dict,
        importance: float = 0.5,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """存储记忆"""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/memory/store",
                json={
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "type": memory_type,
                    "content": content,
                    "importance": importance,
                    "metadata": metadata,
                    "ttl": ttl
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            raise
    
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": query,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "memory_types": memory_types,
                    "limit": limit,
                    "min_importance": min_importance
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []
    
    async def get_conversation_context(
        self,
        session_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取对话上下文"""
        try:
            response = await self.http_client.get(
                f"{self.base_url}/api/sessions/{session_id}/context",
                params={"user_id": user_id, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}", exc_info=True)
            return []
    
    async def update_context(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        agent_response: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新对话上下文"""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/contexts/update",
                json={
                    "session_id": session_id,
                    "user_id": user_id,
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "agent_id": agent_id
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to update context: {e}", exc_info=True)
            raise
    
    async def build_enhanced_prompt(
        self,
        task: str,
        user_id: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """构建包含上下文的增强提示"""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/contexts/enhance-prompt",
                json={
                    "task": task,
                    "user_id": user_id,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "limit": limit
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("enhanced_prompt", task)
        except Exception as e:
            logger.error(f"Failed to build enhanced prompt: {e}", exc_info=True)
            return task
    
    async def close(self):
        """关闭客户端"""
        await self.http_client.aclose()





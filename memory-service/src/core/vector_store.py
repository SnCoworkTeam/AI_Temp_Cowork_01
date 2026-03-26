"""
向量存储
使用Qdrant存储和检索记忆向量
"""
import logging
import os
from typing import List, Optional, Dict, Any
import httpx
import json

from .memory_types import MemoryRecord, MemoryType

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储"""
    
    def __init__(self):
        self.qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = os.getenv("QDRANT_COLLECTION", "memories")
        self.base_url = f"http://{self.qdrant_host}:{self.qdrant_port}"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._collection_initialized = False
    
    async def _ensure_collection(self):
        """确保集合存在"""
        if self._collection_initialized:
            return
        
        try:
            # 检查集合是否存在
            response = await self.http_client.get(
                f"{self.base_url}/collections/{self.collection_name}"
            )
            if response.status_code == 200:
                self._collection_initialized = True
                return
            
            # 创建集合
            collection_config = {
                "vectors": {
                    "size": 1536,  # OpenAI embedding size，如果没有嵌入则使用0
                    "distance": "Cosine"
                }
            }
            
            response = await self.http_client.put(
                f"{self.base_url}/collections/{self.collection_name}",
                json=collection_config
            )
            
            if response.status_code in [200, 201]:
                self._collection_initialized = True
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.warning(f"Failed to create collection: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}", exc_info=True)
            # 如果Qdrant不可用，继续运行但不使用向量搜索
    
    async def store_memory(self, memory: MemoryRecord):
        """存储记忆"""
        try:
            await self._ensure_collection()
            
            # 如果没有嵌入向量，使用文本内容作为payload
            vector = memory.embedding if memory.embedding else []
            
            # 准备payload
            payload = {
                "id": memory.id,
                "user_id": memory.user_id,
                "agent_id": memory.agent_id or "",
                "session_id": memory.session_id or "",
                "type": memory.type.value,
                "content": memory.content,
                "importance": memory.importance,
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed,
                "created_at": memory.created_at,
                "metadata": memory.metadata or {}
            }
            
            # 如果向量为空，使用简单的文本向量（全0向量）
            if not vector:
                vector = [0.0] * 1536  # 默认向量大小
            
            # 上传点
            point = {
                "id": memory.id,
                "vector": vector,
                "payload": payload
            }
            
            response = await self.http_client.put(
                f"{self.base_url}/collections/{self.collection_name}/points",
                json={"points": [point]}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Stored memory vector: {memory.id}")
            else:
                logger.warning(f"Failed to store memory vector: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            # 即使向量存储失败，也不影响整体功能
    
    async def search_by_session(
        self,
        session_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """按会话ID搜索记忆"""
        try:
            await self._ensure_collection()
            
            # 使用过滤器搜索
            filter_config = {
                "must": [
                    {"key": "session_id", "match": {"value": session_id}},
                    {"key": "user_id", "match": {"value": user_id}}
                ]
            }
            
            response = await self.http_client.post(
                f"{self.base_url}/collections/{self.collection_name}/points/scroll",
                json={
                    "filter": filter_config,
                    "limit": limit,
                    "with_payload": True,
                    "with_vector": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                points = data.get("result", {}).get("points", [])
                
                memories = []
                for point in points:
                    payload = point.get("payload", {})
                    memory = MemoryRecord(
                        id=payload.get("id", point.get("id")),
                        user_id=payload.get("user_id"),
                        agent_id=payload.get("agent_id"),
                        session_id=payload.get("session_id"),
                        type=MemoryType(payload.get("type", "short_term")),
                        content=payload.get("content", {}),
                        importance=payload.get("importance", 0.5),
                        access_count=payload.get("access_count", 0),
                        last_accessed=payload.get("last_accessed", 0),
                        created_at=payload.get("created_at", 0),
                        metadata=payload.get("metadata")
                    )
                    memories.append(memory)
                
                return memories
            
            return []
        except Exception as e:
            logger.error(f"Failed to search by session: {e}", exc_info=True)
            return []
    
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        query_text: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[MemoryRecord]:
        """语义搜索记忆"""
        try:
            await self._ensure_collection()
            
            # 构建过滤器
            filter_parts = [{"key": "user_id", "match": {"value": user_id}}]
            
            if agent_id:
                filter_parts.append({"key": "agent_id", "match": {"value": agent_id}})
            
            if session_id:
                filter_parts.append({"key": "session_id", "match": {"value": session_id}})
            
            if memory_types:
                type_values = [mt.value for mt in memory_types]
                filter_parts.append({"key": "type", "match": {"any": type_values}})
            
            if min_importance > 0:
                filter_parts.append({"key": "importance", "range": {"gte": min_importance}})
            
            filter_config = {"must": filter_parts} if filter_parts else None
            
            # 如果没有查询向量，使用文本搜索
            if not query_embedding:
                # 使用过滤器搜索
                search_params = {
                    "filter": filter_config,
                    "limit": limit,
                    "with_payload": True,
                    "with_vector": False
                }
                
                response = await self.http_client.post(
                    f"{self.base_url}/collections/{self.collection_name}/points/scroll",
                    json=search_params
                )
            else:
                # 使用向量搜索
                search_params = {
                    "vector": query_embedding,
                    "limit": limit,
                    "with_payload": True,
                    "with_vector": False
                }
                
                if filter_config:
                    search_params["filter"] = filter_config
                
                response = await self.http_client.post(
                    f"{self.base_url}/collections/{self.collection_name}/points/search",
                    json=search_params
                )
            
            if response.status_code == 200:
                data = response.json()
                points = data.get("result", []) if isinstance(data, dict) else data
                
                memories = []
                for point in points:
                    payload = point.get("payload", {})
                    memory = MemoryRecord(
                        id=payload.get("id", point.get("id")),
                        user_id=payload.get("user_id"),
                        agent_id=payload.get("agent_id"),
                        session_id=payload.get("session_id"),
                        type=MemoryType(payload.get("type", "short_term")),
                        content=payload.get("content", {}),
                        importance=payload.get("importance", 0.5),
                        access_count=payload.get("access_count", 0),
                        last_accessed=payload.get("last_accessed", 0),
                        created_at=payload.get("created_at", 0),
                        metadata=payload.get("metadata")
                    )
                    memories.append(memory)
                
                return memories
            
            return []
        except Exception as e:
            logger.error(f"Failed to semantic search: {e}", exc_info=True)
            return []
    
    async def update_memory(self, memory: MemoryRecord):
        """更新记忆"""
        try:
            await self._ensure_collection()
            
            payload = {
                "access_count": memory.access_count,
                "last_accessed": memory.last_accessed
            }
            
            response = await self.http_client.post(
                f"{self.base_url}/collections/{self.collection_name}/points/payload",
                json={
                    "points": [memory.id],
                    "payload": payload
                }
            )
            
            if response.status_code == 200:
                logger.debug(f"Updated memory: {memory.id}")
        except Exception as e:
            logger.error(f"Failed to update memory: {e}", exc_info=True)
    
    async def delete_memory(self, memory_id: str):
        """删除记忆"""
        try:
            await self._ensure_collection()
            
            response = await self.http_client.post(
                f"{self.base_url}/collections/{self.collection_name}/points/delete",
                json={"points": [memory_id]}
            )
            
            if response.status_code == 200:
                logger.info(f"Deleted memory: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}", exc_info=True)
    
    async def close(self):
        """关闭连接"""
        await self.http_client.aclose()





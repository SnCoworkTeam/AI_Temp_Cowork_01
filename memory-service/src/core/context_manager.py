"""
上下文管理器
负责管理对话上下文和记忆检索
"""
import logging
import time
from typing import List, Optional, Dict, Any
import httpx
import json

from .memory_types import MemoryRecord, MemoryType, MemorySearchRequest
from .vector_store import VectorStore
from .redis_client import RedisClient

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.redis_client = RedisClient()
        self._embedding_client = None
    
    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入"""
        # 如果已经有嵌入客户端，使用它
        if self._embedding_client is None:
            # 这里可以使用 OpenAI 或其他嵌入模型
            # 暂时返回空列表，后续可以集成嵌入服务
            return []
        
        try:
            # 调用嵌入服务获取向量
            # embedding = await self._embedding_client.get_embedding(text)
            # return embedding
            return []
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return []
    
    async def get_conversation_context(
        self,
        session_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """获取对话上下文"""
        try:
            # 先从Redis缓存获取
            cached_context = await self.redis_client.get_session_context(session_id)
            if cached_context:
                return cached_context
            
            # 从向量数据库搜索
            memories = await self.vector_store.search_by_session(
                session_id=session_id,
                user_id=user_id,
                limit=limit
            )
            
            # 缓存到Redis
            if memories:
                await self.redis_client.set_session_context(session_id, memories)
            
            return memories
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}", exc_info=True)
            return []
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[MemoryRecord]:
        """检索相关记忆"""
        try:
            # 生成查询向量
            query_embedding = await self._get_embedding(query)
            
            # 从向量数据库搜索
            memories = await self.vector_store.semantic_search(
                user_id=user_id,
                query_embedding=query_embedding,
                query_text=query,
                agent_id=agent_id,
                session_id=session_id,
                memory_types=memory_types,
                limit=limit,
                min_importance=min_importance
            )
            
            # 更新访问统计
            for memory in memories:
                memory.access_count += 1
                memory.last_accessed = time.time()
                await self.vector_store.update_memory(memory)
            
            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve relevant memories: {e}", exc_info=True)
            return []
    
    async def store_memory(
        self,
        user_id: str,
        agent_id: Optional[str],
        session_id: Optional[str],
        memory_type: MemoryType,
        content: dict,
        importance: float = 0.5,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None
    ) -> MemoryRecord:
        """存储记忆"""
        try:
            # 生成向量嵌入
            content_text = json.dumps(content, ensure_ascii=False)
            embedding = await self._get_embedding(content_text)
            
            # 创建记忆记录
            memory = MemoryRecord(
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
                type=memory_type,
                content=content,
                embedding=embedding,
                importance=importance,
                metadata=metadata
            )
            
            # 存储到向量数据库
            await self.vector_store.store_memory(memory)
            
            # 如果是短期记忆，设置TTL
            if memory_type == MemoryType.SHORT_TERM and ttl:
                await self.redis_client.set_memory_ttl(memory.id, ttl)
            
            # 更新会话缓存
            if session_id:
                await self.redis_client.invalidate_session_cache(session_id)
            
            logger.info(f"Stored memory: {memory.id} for user {user_id}")
            return memory
        except Exception as e:
            logger.error(f"Failed to store memory: {e}", exc_info=True)
            raise
    
    async def update_context(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        agent_response: str,
        agent_id: Optional[str] = None
    ):
        """更新对话上下文"""
        try:
            # 存储短期记忆
            memory = await self.store_memory(
                user_id=user_id,
                agent_id=agent_id,
                session_id=session_id,
                memory_type=MemoryType.SHORT_TERM,
                content={
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "timestamp": time.time()
                },
                importance=0.6,  # 对话记忆中等重要性
                ttl=3600  # 1小时过期
            )
            
            logger.info(f"Updated context for session {session_id}")
            return memory
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
            # 检索相关记忆
            memories = await self.retrieve_relevant_memories(
                user_id=user_id,
                query=task,
                agent_id=agent_id,
                session_id=session_id,
                limit=limit
            )
            
            if not memories:
                return task
            
            # 构建上下文字符串
            context_parts = []
            for memory in memories:
                if memory.type == MemoryType.SHORT_TERM:
                    user_input = memory.content.get("user_input", "")
                    agent_response = memory.content.get("agent_response", "")
                    context_parts.append(f"之前对话：\n用户：{user_input}\n助手：{agent_response}")
                elif memory.type == MemoryType.LONG_TERM:
                    # 长期记忆通常是用户偏好
                    context_parts.append(f"用户偏好：{json.dumps(memory.content, ensure_ascii=False)}")
                elif memory.type == MemoryType.PROCEDURAL:
                    # 程序记忆是执行模式
                    context_parts.append(f"执行模式：{json.dumps(memory.content, ensure_ascii=False)}")
            
            context_str = "\n\n".join(context_parts)
            
            enhanced_prompt = f"""基于以下上下文信息：

{context_str}

当前任务：{task}

请基于之前的对话上下文和用户偏好来回应：
"""
            return enhanced_prompt
        except Exception as e:
            logger.error(f"Failed to build enhanced prompt: {e}", exc_info=True)
            return task
    
    async def close(self):
        """关闭连接"""
        await self.vector_store.close()
        await self.redis_client.close()


# 全局上下文管理器实例
context_manager = ContextManager()





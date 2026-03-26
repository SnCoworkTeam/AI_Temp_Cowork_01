"""
记忆管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..core.context_manager import context_manager
from ..core.memory_types import MemoryRecord, MemoryType, MemoryStoreRequest, MemorySearchRequest

router = APIRouter(tags=["记忆管理"])
logger = logging.getLogger(__name__)


@router.post("/store", response_model=MemoryRecord, summary="存储记忆")
async def store_memory(request: MemoryStoreRequest):
    """存储记忆"""
    try:
        memory = await context_manager.store_memory(
            user_id=request.user_id,
            agent_id=request.agent_id,
            session_id=request.session_id,
            memory_type=request.type,
            content=request.content,
            importance=request.importance,
            metadata=request.metadata,
            ttl=request.ttl
        )
        return memory
    except Exception as e:
        logger.error(f"Failed to store memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.post("/retrieve", response_model=List[MemoryRecord], summary="检索记忆")
async def retrieve_memories(request: MemorySearchRequest):
    """检索相关记忆"""
    try:
        memories = await context_manager.retrieve_relevant_memories(
            user_id=request.user_id,
            query=request.query,
            agent_id=request.agent_id,
            session_id=request.session_id,
            memory_types=request.memory_types,
            limit=request.limit,
            min_importance=request.min_importance
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.post("/search", response_model=List[MemoryRecord], summary="语义搜索记忆")
async def search_memories(request: MemorySearchRequest):
    """语义搜索记忆"""
    try:
        memories = await context_manager.retrieve_relevant_memories(
            user_id=request.user_id,
            query=request.query,
            agent_id=request.agent_id,
            session_id=request.session_id,
            memory_types=request.memory_types,
            limit=request.limit,
            min_importance=request.min_importance
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to search memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")


@router.delete("/{memory_id}", summary="删除记忆")
async def delete_memory(memory_id: str):
    """删除记忆"""
    try:
        from ..core.vector_store import VectorStore
        vector_store = VectorStore()
        await vector_store.delete_memory(memory_id)
        return {"success": True, "message": f"Memory {memory_id} deleted"}
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")





"""
会话管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import time
import uuid

from ..core.context_manager import context_manager
from ..core.memory_types import MemoryRecord

router = APIRouter(tags=["会话管理"])
logger = logging.getLogger(__name__)


class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    user_id: str = Field(..., description="用户ID")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    metadata: Optional[dict] = Field(None, description="元数据")


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    user_id: str
    agent_id: Optional[str]
    created_at: float
    metadata: Optional[dict]


@router.post("", response_model=SessionResponse, summary="创建会话")
async def create_session(request: SessionCreateRequest):
    """创建新会话"""
    try:
        session_id = str(uuid.uuid4())
        # 这里可以存储会话信息到数据库
        # 暂时只返回会话ID
        return SessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            created_at=time.time(),
            metadata=request.metadata
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}/context", response_model=List[MemoryRecord], summary="获取会话上下文")
async def get_session_context(session_id: str, user_id: str, limit: int = 10):
    """获取会话上下文"""
    try:
        memories = await context_manager.get_conversation_context(
            session_id=session_id,
            user_id=user_id,
            limit=limit
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to get session context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session context: {str(e)}")


@router.delete("/{session_id}", summary="删除会话")
async def delete_session(session_id: str):
    """删除会话及其所有记忆"""
    try:
        # 使缓存失效
        await context_manager.redis_client.invalidate_session_cache(session_id)
        # 这里可以添加删除会话相关记忆的逻辑
        return {"success": True, "message": f"Session {session_id} deleted"}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")





"""
上下文管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..core.context_manager import context_manager
from ..core.memory_types import MemoryRecord

router = APIRouter(tags=["上下文管理"])
logger = logging.getLogger(__name__)


class ContextUpdateRequest(BaseModel):
    """更新上下文请求"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    user_input: str = Field(..., description="用户输入")
    agent_response: str = Field(..., description="智能体响应")
    agent_id: Optional[str] = Field(None, description="智能体ID")


class EnhancedPromptRequest(BaseModel):
    """增强提示请求"""
    task: str = Field(..., description="任务描述")
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    agent_id: Optional[str] = Field(None, description="智能体ID")
    limit: int = Field(5, description="记忆数量限制")


class EnhancedPromptResponse(BaseModel):
    """增强提示响应"""
    enhanced_prompt: str
    memories_used: int


@router.get("/{session_id}", response_model=List[MemoryRecord], summary="获取增强上下文")
async def get_enhanced_context(session_id: str, user_id: str, limit: int = 10):
    """获取增强上下文（包含相关记忆）"""
    try:
        memories = await context_manager.get_conversation_context(
            session_id=session_id,
            user_id=user_id,
            limit=limit
        )
        return memories
    except Exception as e:
        logger.error(f"Failed to get enhanced context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced context: {str(e)}")


@router.post("/update", response_model=MemoryRecord, summary="更新上下文")
async def update_context(request: ContextUpdateRequest):
    """更新对话上下文"""
    try:
        memory = await context_manager.update_context(
            session_id=request.session_id,
            user_id=request.user_id,
            user_input=request.user_input,
            agent_response=request.agent_response,
            agent_id=request.agent_id
        )
        return memory
    except Exception as e:
        logger.error(f"Failed to update context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update context: {str(e)}")


@router.post("/enhance-prompt", response_model=EnhancedPromptResponse, summary="构建增强提示")
async def enhance_prompt(request: EnhancedPromptRequest):
    """构建包含上下文的增强提示"""
    try:
        enhanced_prompt = await context_manager.build_enhanced_prompt(
            task=request.task,
            user_id=request.user_id,
            session_id=request.session_id,
            agent_id=request.agent_id,
            limit=request.limit
        )
        
        # 获取使用的记忆数量
        memories = await context_manager.retrieve_relevant_memories(
            user_id=request.user_id,
            query=request.task,
            agent_id=request.agent_id,
            session_id=request.session_id,
            limit=request.limit
        )
        
        return EnhancedPromptResponse(
            enhanced_prompt=enhanced_prompt,
            memories_used=len(memories)
        )
    except Exception as e:
        logger.error(f"Failed to enhance prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to enhance prompt: {str(e)}")


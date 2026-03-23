"""
智能助手API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ..services.assistant_service import AssistantService
import logging

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")


class QuestionRequest(BaseModel):
    """问题请求"""
    question: str = Field(..., description="问题")
    knowledge_base: Optional[Dict[str, Any]] = Field(None, description="知识库上下文")


@router.post("/chat", summary="智能助手对话")
async def chat(
    request: ChatRequest
):
    """
    智能助手对话
    
    支持上下文感知和多轮对话
    """
    try:
        assistant = AssistantService()
        response = await assistant.chat(
            message=request.message,
            context=request.context,
            conversation_history=request.conversation_history
        )
        await assistant.close()
        
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        logger.error(f"Failed to chat with assistant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer", summary="回答问题")
async def answer_question(
    request: QuestionRequest
):
    """
    基于知识库回答问题
    """
    try:
        assistant = AssistantService()
        answer = await assistant.answer_question(
            question=request.question,
            knowledge_base=request.knowledge_base
        )
        await assistant.close()
        
        return {
            "success": True,
            "answer": answer
        }
    except Exception as e:
        logger.error(f"Failed to answer question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


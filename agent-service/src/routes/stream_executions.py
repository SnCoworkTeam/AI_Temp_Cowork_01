"""
流式执行路由
提供智能体的流式执行端点
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from ..core.stream_executor import stream_executor
from ..core.agent_manager import agent_manager

router = APIRouter(tags=["流式执行"])
logger = logging.getLogger(__name__)


class StreamChatRequest(BaseModel):
    """流式对话请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    user_context: Optional[Dict[str, Any]] = Field(None, description="用户上下文")
    session_id: Optional[str] = Field(None, description="会话ID（用于记忆管理）")


@router.post("/chat/stream", summary="流式智能对话")
async def stream_intelligent_chat(request: StreamChatRequest):
    """
    流式智能对话处理
    
    使用Server-Sent Events (SSE)实时返回执行过程
    
    - **message**: 用户消息
    - **conversation_history**: 对话历史（可选）
    - **user_context**: 用户上下文（可选）
    """
    try:
        async def generate_stream():
            import json
            async for message in stream_executor.stream_intelligent_chat(
                message=request.message,
                conversation_history=request.conversation_history,
                user_context=request.user_context
            ):
                # 将 StreamMessage 对象转换为 SSE 格式
                if hasattr(message, 'dict'):
                    # Pydantic 模型
                    data = message.dict()
                elif hasattr(message, '__dict__'):
                    # 普通对象
                    data = message.__dict__
                else:
                    # 字典
                    data = message
                
                # 格式化为 SSE 格式: data: {json}\n\n
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Stream chat failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Stream chat failed: {str(e)}"
        )


@router.post("/agents/{agent_id}/execute/stream", summary="流式执行智能体")
async def stream_execute_agent(
    agent_id: str,
    task: str,
    context: Optional[Dict[str, Any]] = None
):
    """
    流式执行智能体
    
    实时返回执行过程和结果
    
    - **agent_id**: 智能体ID
    - **task**: 任务描述
    - **context**: 上下文信息（可选）
    """
    try:
        async def generate_stream():
            # 发送开始消息
            import json
            import sys
            from pathlib import Path
            
            # 添加共享库路径
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared_libs"))
            
            try:
                from luminaos_common.schemas.stream_schemas import StreamMessageType
            except ImportError:
                from enum import Enum
                class StreamMessageType(str, Enum):
                    START = "start"
                    STEP = "step"
                    COMPLETE = "complete"
                    ERROR = "error"
            
            yield f"data: {json.dumps({'type': 'start', 'agent_id': agent_id, 'task': task})}\n\n"
            
            # 执行智能体
            result = await agent_manager.execute_agent(agent_id, task, context)
            
            # 发送步骤结果
            yield f"data: {json.dumps({'type': 'step_result', 'step': '执行', 'result': result})}\n\n"
            
            # 发送完成消息
            yield f"data: {json.dumps({'type': 'complete', 'result': result})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        logger.error(f"Stream agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Stream agent execution failed: {str(e)}"
        )


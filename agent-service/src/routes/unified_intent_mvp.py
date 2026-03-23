"""
统一意图识别MVP API路由（阶段1：伪流式MVP）
"""
import logging
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# 先定义logger
logger = logging.getLogger(__name__)

# 导入MVP服务
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from services.unified_intent_mvp import get_unified_intent_mvp
except ImportError as e:
    logger.warning(f"无法导入unified_intent_mvp: {e}，将使用降级方案")
    get_unified_intent_mvp = None

router = APIRouter(prefix="/api/v1/unified", tags=["unified-intent-mvp"])


class UnifiedRequest(BaseModel):
    """统一请求模型"""
    user_input: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")


@router.post("/process")
async def process_unified_request(request: UnifiedRequest):
    """
    统一处理请求（伪流式MVP）
    
    使用Server-Sent Events (SSE)返回流式结果
    """
    if get_unified_intent_mvp is None:
        raise HTTPException(status_code=503, detail="统一意图MVP服务未初始化")
    
    try:
        mvp_service = get_unified_intent_mvp()
        
        # 构建上下文
        context = request.context or {}
        if request.user_id:
            context['user_id'] = request.user_id
        if request.session_id:
            context['session_id'] = request.session_id
        # 默认启用流式LLM（如果未指定）
        if 'use_streaming_llm' not in context:
            context['use_streaming_llm'] = True
        
        async def generate_stream():
            """生成SSE流式响应"""
            try:
                async for chunk in mvp_service.process_hybrid(
                    user_input=request.user_input,
                    context=context
                ):
                    # 格式化为SSE格式
                    data = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"流式处理错误: {e}", exc_info=True)
                error_chunk = {
                    "stage": "error",
                    "status": "error",
                    "error": str(e),
                    "message": "流式处理过程中发生错误"
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
            }
        )
    
    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@router.get("/process")
async def process_unified_request_get(
    input: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_streaming_llm: Optional[str] = None
):
    """
    统一处理请求（GET方式，用于SSE）
    
    使用Server-Sent Events (SSE)返回流式结果
    
    Args:
        input: 用户输入
        session_id: 会话ID
        user_id: 用户ID
        use_streaming_llm: 是否使用流式LLM分析（"true"/"false"）
    """
    if get_unified_intent_mvp is None:
        raise HTTPException(status_code=503, detail="统一意图MVP服务未初始化")
    
    try:
        mvp_service = get_unified_intent_mvp()
        
        # 构建上下文
        context = {}
        if user_id:
            context['user_id'] = user_id
        if session_id:
            context['session_id'] = session_id
        if use_streaming_llm:
            context['use_streaming_llm'] = use_streaming_llm.lower() == "true"
        
        async def generate_stream():
            """生成SSE流式响应"""
            try:
                async for chunk in mvp_service.process_hybrid(
                    user_input=input,
                    context=context
                ):
                    # 格式化为SSE格式
                    data = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"流式处理错误: {e}", exc_info=True)
                error_chunk = {
                    "stage": "error",
                    "status": "error",
                    "error": str(e),
                    "message": "流式处理过程中发生错误"
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
            }
        )
    
    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


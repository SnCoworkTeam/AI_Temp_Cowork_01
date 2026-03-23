"""
智能对话路由
提供智能对话处理端点
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import json

from ..core.agent_manager import agent_manager
from ..core.orchestration_engine import orchestration_engine
from ..models.agent_models import AgentStatus

router = APIRouter(tags=["智能对话"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """对话请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    user_context: Optional[Dict[str, Any]] = Field(None, description="用户上下文")
    session_id: Optional[str] = Field(None, description="会话ID（用于记忆管理）")
    stream: bool = Field(False, description="是否流式返回")


class ChatResponse(BaseModel):
    """对话响应模型"""
    success: bool = Field(..., description="是否成功")
    output: Optional[str] = Field(None, description="响应内容")
    intent_analysis: Optional[Dict[str, Any]] = Field(None, description="意图分析结果")
    strategy: Optional[str] = Field(None, description="执行策略")
    error: Optional[str] = Field(None, description="错误信息")


@router.post("/chat", response_model=ChatResponse, summary="智能对话")
async def intelligent_chat(request: ChatRequest):
    """
    智能对话处理
    
    自动理解用户意图，分类任务，并路由到合适的服务执行
    
    - **message**: 用户消息
    - **conversation_history**: 对话历史（可选）
    - **user_context**: 用户上下文（可选）
    - **stream**: 是否流式返回（暂不支持）
    """
    try:
        result = await agent_manager.intelligent_chat(
            message=request.message,
            conversation_history=request.conversation_history,
            user_context=request.user_context,
            session_id=request.session_id
        )
        
        return ChatResponse(
            success=result.get("success", False),
            output=result.get("output"),
            intent_analysis=result.get("intent_analysis"),
            strategy=result.get("strategy"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Intelligent chat failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Intelligent chat failed: {str(e)}"
        )


@router.post("/intelligent", summary="智能对话入口 - 统一处理所有对话请求")
async def intelligent_chat_endpoint(request: ChatRequest):
    """
    智能对话入口 - 统一处理所有对话请求
    
    使用OrchestrationEngine进行统一编排处理
    
    - **message**: 用户消息
    - **conversation_history**: 对话历史（可选）
    - **user_context**: 用户上下文（可选）
    - **session_id**: 会话ID（可选）
    """
    try:
        # 获取可用智能体
        available_agents = await agent_manager.list_agents(status=AgentStatus.ACTIVE)
        agents_dict = [
            {"id": a.id, "name": a.name, "capabilities": a.capabilities}
            for a in available_agents
        ]
        
        # 构建上下文
        context = {
            'user_id': request.user_context.get('user_id') if request.user_context else None,
            'session_id': request.session_id,
            'history': request.conversation_history or [],
            'available_agents': agents_dict
        }
        
        # 合并user_context
        if request.user_context:
            context.update(request.user_context)
        
        # 使用编排引擎处理
        result = await orchestration_engine.orchestrate_request(
            user_input=request.message,
            context=context
        )
        
        # 提取输出内容
        output = result.get("final_response") or result.get("output")
        if not output and result.get("execution_path"):
            # 从执行路径中提取结果
            for step in reversed(result.get("execution_path", [])):
                if step.get("result") and step.get("result").get("output"):
                    output = step.get("result").get("output")
                    break
        
        # 如果没有输出，使用错误信息
        if not output:
            error = result.get("error") or "无法生成回复"
            output = f"抱歉，处理您的请求时遇到问题：{error}"
        
        return {
            "output": output,
            "success": result.get("success", False),
            "intent_analysis": result.get("intent_analysis"),
            "strategy": result.get("routing_decision", {}).get("strategy") if result.get("routing_decision") else None,
            "error": result.get("error"),
            "execution_path": result.get("execution_path", []),
            "used_services": result.get("used_services", []),
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"Intelligent chat orchestration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Intelligent chat orchestration failed: {str(e)}"
        )


@router.post("/intelligent/stream", summary="流式智能对话")
async def intelligent_chat_stream(request: ChatRequest):
    """
    流式智能对话
    
    使用OrchestrationEngine进行流式编排处理
    
    - **message**: 用户消息
    - **conversation_history**: 对话历史（可选）
    - **user_context**: 用户上下文（可选）
    - **session_id**: 会话ID（可选）
    """
    async def generate_stream():
        try:
            # 获取可用智能体
            available_agents = await agent_manager.list_agents(status=AgentStatus.ACTIVE)
            agents_dict = [
                {"id": a.id, "name": a.name, "capabilities": a.capabilities}
                for a in available_agents
            ]
            
            # 构建上下文
            context = {
                'user_id': request.user_context.get('user_id') if request.user_context else None,
                'session_id': request.session_id,
                'history': request.conversation_history or [],
                'available_agents': agents_dict
            }
            
            # 合并user_context
            if request.user_context:
                context.update(request.user_context)
            
            # 开始执行 - 使用SSE格式 (data: {...}\n\n)
            yield f"data: {json.dumps({'type': 'start', 'data': {'message': '开始处理请求'}, 'progress': 0})}\n\n"
            
            # 流式执行编排
            async for step_result in orchestration_engine.orchestrate_stream(
                request.message, context
            ):
                step_name = step_result.get("step_name", "处理中")
                progress = step_result.get("progress", 0)
                
                # 根据步骤类型发送不同的消息
                if step_name == "intent_analysis":
                    partial_result = step_result.get("partial_result", {})
                    yield f"data: {json.dumps({'type': 'step', 'step': '意图分析', 'data': {'status': '完成', 'task_type': partial_result.get('task_type'), 'confidence': partial_result.get('confidence')}, 'progress': progress})}\n\n"
                elif step_name == "routing_decision":
                    partial_result = step_result.get("partial_result", {})
                    yield f"data: {json.dumps({'type': 'step', 'step': '任务分类', 'data': {'status': '完成', 'strategy': partial_result.get('strategy'), 'target_service': partial_result.get('target_service')}, 'progress': progress})}\n\n"
                elif step_name == "execution":
                    # 执行步骤，流式返回内容
                    partial_result = step_result.get("partial_result", "")
                    if partial_result and isinstance(partial_result, str):
                        # 分块发送内容（模拟打字效果）
                        chunk_size = 20
                        for i in range(0, len(partial_result), chunk_size):
                            chunk = partial_result[i:i + chunk_size]
                            yield f"data: {json.dumps({'type': 'chunk', 'data': {'chunk': chunk}, 'progress': progress})}\n\n"
                    elif partial_result:
                        # 如果不是字符串，尝试转换为字符串
                        try:
                            result_str = str(partial_result) if not isinstance(partial_result, str) else partial_result
                            chunk_size = 20
                            for i in range(0, len(result_str), chunk_size):
                                chunk = result_str[i:i + chunk_size]
                                yield f"data: {json.dumps({'type': 'chunk', 'data': {'chunk': chunk}, 'progress': progress})}\n\n"
                        except:
                            yield f"data: {json.dumps({'type': 'step', 'step': '执行中', 'data': step_result.get('partial_result', {}), 'progress': progress})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'step', 'step': '执行中', 'data': step_result.get('partial_result', {}), 'progress': progress})}\n\n"
                elif step_name == "complete":
                    # 执行完成
                    final_result = step_result.get("final_result", {})
                    yield f"data: {json.dumps({'type': 'complete', 'data': {'result': {'response': final_result.get('final_response'), 'execution_path': final_result.get('execution_path', []), 'used_services': final_result.get('used_services', [])}}, 'progress': 100})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream orchestration failed: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


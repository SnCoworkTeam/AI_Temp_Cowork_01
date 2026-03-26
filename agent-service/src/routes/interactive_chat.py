"""
交互式聊天路由
提供WebSocket实时交互和交互式编排端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from ..core.websocket_manager.websocket_manager import websocket_manager
from ..core.interactive_orchestration_engine import InteractiveOrchestrationEngine
from ..core.agent_manager import agent_manager

router = APIRouter(tags=["交互式对话"])
logger = logging.getLogger(__name__)

# 创建交互式编排引擎实例
interactive_engine = InteractiveOrchestrationEngine()


class InteractiveChatRequest(BaseModel):
    """交互式聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    user_context: Optional[Dict[str, Any]] = Field(None, description="用户上下文")
    session_id: str = Field(..., description="会话ID（必需）")
    user_id: Optional[str] = Field(None, description="用户ID")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket端点 - 实时双向通信
    
    客户端连接后可以：
    - 接收执行状态更新
    - 发送控制命令（暂停、继续、取消）
    - 响应确认请求
    - 提供用户输入
    """
    try:
        await websocket_manager.handle_websocket(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)


@router.post("/chat/interactive")
async def interactive_chat(request: InteractiveChatRequest):
    """
    交互式聊天端点
    
    启动交互式编排，通过WebSocket实时反馈执行状态
    """
    try:
        # 获取可用智能体
        available_agents = await agent_manager.get_active_agents()
        
        # 构建上下文
        context = {
            'user_id': request.user_id,
            'session_id': request.session_id,
            'history': request.conversation_history or [],
            'available_agents': [agent.dict() for agent in available_agents],
            'user_profile': request.user_context.get('user_profile') if request.user_context else None,
            'task_context': request.user_context.get('task_context') if request.user_context else None,
            'available_tools': request.user_context.get('available_tools', []) if request.user_context else []
        }
        
        # 执行交互式编排
        result = await interactive_engine.orchestrate_interactive(
            user_input=request.message,
            context=context
        )
        
        return {
            "success": True,
            "execution_id": result.get('execution_id'),
            "result": result,
            "execution_status": "completed"
        }
    except Exception as e:
        logger.error(f"Interactive chat error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "execution_status": "error"
        }


@router.get("/executions/{execution_id}/state")
async def get_execution_state(execution_id: str):
    """
    获取执行状态
    
    查询指定执行ID的当前状态
    """
    state = interactive_engine.get_execution_state(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "execution_id": state.execution_id,
        "session_id": state.session_id,
        "status": state.status.value,
        "progress": state.progress,
        "current_step": state.current_step,
        "total_steps": state.total_steps,
        "paused": state.paused,
        "cancelled": state.cancelled,
        "waiting_for_input": state.waiting_for_input
    }


@router.get("/executions")
async def list_executions(session_id: Optional[str] = None):
    """
    列出活跃的执行
    
    查询当前活跃的执行任务
    """
    executions = interactive_engine.list_active_executions(session_id)
    return {
        "executions": [
            {
                "execution_id": e.execution_id,
                "session_id": e.session_id,
                "status": e.status.value,
                "progress": e.progress,
                "current_step": e.current_step,
                "total_steps": e.total_steps
            }
            for e in executions
        ]
    }


@router.get("/websocket/stats")
async def get_websocket_stats():
    """
    获取WebSocket连接统计
    
    查看当前WebSocket连接状态
    """
    stats = websocket_manager.get_connection_stats()
    return stats






































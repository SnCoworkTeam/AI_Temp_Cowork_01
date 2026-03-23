"""
智能体工作流API路由
提供前端AgentWorkflowInterface所需的API端点
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import logging
import uuid
from datetime import datetime

from ..dependencies.database import get_db
from ..core.dynamic_workflow_engine import DynamicWorkflowEngine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局工作流引擎实例
_workflow_engine: Optional[DynamicWorkflowEngine] = None

def get_workflow_engine() -> DynamicWorkflowEngine:
    """获取工作流引擎实例（单例模式）"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = DynamicWorkflowEngine()
    return _workflow_engine


# ==================== 请求/响应模型 ====================

class AdvanceWorkflowRequest(BaseModel):
    """推进工作流请求"""
    workflow_id: str
    current_state: Dict[str, Any]
    user_input: Optional[Dict[str, Any]] = None
    next_node: Optional[str] = None


class ContinueAgentRequest(BaseModel):
    """继续智能体工作流请求"""
    agent_id: str
    workflow_id: str
    user_input: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class StartWorkflowRequest(BaseModel):
    """启动工作流请求"""
    input_data: Dict[str, Any]
    thread_id: Optional[str] = None


# ==================== WebSocket连接管理器 ====================

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.workflow_connections: Dict[str, List[str]] = {}  # workflow_id -> [connection_id, ...]
    
    async def connect(self, websocket: WebSocket, workflow_id: str) -> str:
        """接受WebSocket连接并注册"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if workflow_id not in self.workflow_connections:
            self.workflow_connections[workflow_id] = []
        self.workflow_connections[workflow_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for workflow {workflow_id}")
        return connection_id
    
    def disconnect(self, connection_id: str, workflow_id: Optional[str] = None):
        """断开WebSocket连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if workflow_id and workflow_id in self.workflow_connections:
            if connection_id in self.workflow_connections[workflow_id]:
                self.workflow_connections[workflow_id].remove(connection_id)
            if not self.workflow_connections[workflow_id]:
                del self.workflow_connections[workflow_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(self, workflow_id: str, message: Dict[str, Any]):
        """向指定工作流的所有连接发送消息"""
        if workflow_id not in self.workflow_connections:
            return
        
        disconnected = []
        for connection_id in self.workflow_connections[workflow_id]:
            websocket = self.active_connections.get(connection_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to {connection_id}: {e}")
                    disconnected.append(connection_id)
            else:
                disconnected.append(connection_id)
        
        # 清理断开的连接
        for conn_id in disconnected:
            self.disconnect(conn_id, workflow_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """向所有连接广播消息"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        for conn_id in disconnected:
            self.disconnect(conn_id)


# 全局连接管理器
connection_manager = ConnectionManager()


# ==================== API端点 ====================

@router.post("/api/workflows/advance")
async def advance_workflow(request: AdvanceWorkflowRequest):
    """
    推进工作流到下一个节点
    
    - **workflow_id**: 工作流ID
    - **current_state**: 当前状态
    - **user_input**: 用户输入（可选）
    - **next_node**: 下一个节点ID（可选）
    """
    try:
        engine = get_workflow_engine()
        
        # 获取工作流定义
        workflow_def = engine.get_workflow_definition(request.workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail=f"Workflow '{request.workflow_id}' not found")
        
        # 更新状态
        updated_state = request.current_state.copy()
        if request.user_input:
            updated_state.update(request.user_input)
        
        # 如果有指定下一个节点，更新current_node
        if request.next_node:
            updated_state["current_node"] = request.next_node
        
        # 通过WebSocket发送更新
        await connection_manager.send_message(request.workflow_id, {
            "type": "WORKFLOW_PROGRESS",
            "payload": {
                "workflowId": request.workflow_id,
                "workflowName": workflow_def.name if hasattr(workflow_def, 'name') else request.workflow_id,
                "currentNode": updated_state.get("current_node"),
                "status": "running",
                "progress": 50  # 临时值，实际应从状态计算
            }
        })
        
        return {
            "success": True,
            "workflow_id": request.workflow_id,
            "current_state": updated_state,
            "message": "Workflow advanced successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to advance workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to advance workflow: {str(e)}")


@router.post("/api/agent/continue")
async def continue_agent_workflow(request: ContinueAgentRequest):
    """
    继续智能体工作流执行
    
    - **agent_id**: 智能体ID
    - **workflow_id**: 工作流ID
    - **user_input**: 用户输入（可选）
    - **session_id**: 会话ID（可选，用于恢复执行）
    """
    try:
        engine = get_workflow_engine()
        
        # 使用session_id作为thread_id，如果没有则生成新的
        thread_id = request.session_id or f"agent_{request.agent_id}_{uuid.uuid4().hex[:8]}"
        
        # 准备用户输入
        user_input = request.user_input or {}
        
        # 尝试恢复工作流
        try:
            result = await engine.resume_workflow(
                workflow_id=request.workflow_id,
                thread_id=thread_id,
                user_input=user_input
            )
        except ValueError:
            # 如果没有检查点，启动新的执行
            result = await engine.execute_workflow(
                workflow_id=request.workflow_id,
                input_data=user_input,
                thread_id=thread_id
            )
        
        # 通过WebSocket发送更新
        await connection_manager.send_message(request.workflow_id, {
            "type": "AGENT_RESPONSE",
            "payload": {
                "agentId": request.agent_id,
                "agentName": request.agent_id,  # 可以从数据库获取
                "workflowId": request.workflow_id,
                "executionId": result.get("thread_id", thread_id),
                "output": {
                    "content": str(result.get("result", {})),
                    "type": "text"
                },
                "success": result.get("success", True),
                "requires_further_input": False
            }
        })
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "workflow_id": request.workflow_id,
            "execution_id": thread_id,
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to continue agent workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to continue agent workflow: {str(e)}")


@router.post("/api/workflows/{workflow_id}/start")
async def start_workflow(workflow_id: str, request: StartWorkflowRequest):
    """
    启动特定工作流
    
    - **workflow_id**: 工作流ID（路径参数）
    - **input_data**: 输入数据
    - **thread_id**: 线程ID（可选）
    """
    try:
        engine = get_workflow_engine()
        
        # 检查工作流是否存在
        workflow_def = engine.get_workflow_definition(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        
        # 执行工作流
        result = await engine.execute_workflow(
            workflow_id=workflow_id,
            input_data=request.input_data,
            thread_id=request.thread_id
        )
        
        # 通过WebSocket发送启动通知
        await connection_manager.send_message(workflow_id, {
            "type": "WORKFLOW_PROGRESS",
            "payload": {
                "executionId": result.get("execution_id"),
                "workflowId": workflow_id,
                "workflowName": workflow_def.name if hasattr(workflow_def, 'name') else workflow_id,
                "status": "running",
                "progress": 0,
                "currentNode": None,
                "currentNodeName": None
            }
        })
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "execution_id": result.get("execution_id"),
            "thread_id": result.get("thread_id"),
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


# ==================== WebSocket端点 ====================

@router.websocket("/api/ws/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    工作流WebSocket连接
    
    提供实时工作流执行状态更新
    """
    connection_id = None
    try:
        # 接受连接
        connection_id = await connection_manager.connect(websocket, workflow_id)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "payload": {
                "workflowId": workflow_id,
                "connectionId": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # 监听客户端消息
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handle_websocket_message(workflow_id, connection_id, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "ERROR",
                    "payload": {
                        "message": "Invalid JSON message"
                    }
                })
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "ERROR",
                    "payload": {
                        "message": f"Error processing message: {str(e)}"
                    }
                })
    
    except WebSocketDisconnect:
        if connection_id:
            connection_manager.disconnect(connection_id, workflow_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if connection_id:
            connection_manager.disconnect(connection_id, workflow_id)


async def handle_websocket_message(workflow_id: str, connection_id: str, message: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = message.get("type")
    
    if message_type == "user_message":
        # 处理用户消息
        user_input = message.get("data", {}).get("content", "")
        
        # 通过WebSocket发送AI响应（这里可以调用智能体服务）
        await connection_manager.send_message(workflow_id, {
            "type": "AGENT_RESPONSE",
            "payload": {
                "agentId": message.get("data", {}).get("agentId", "default"),
                "workflowId": workflow_id,
                "output": {
                    "content": f"Received: {user_input}",
                    "type": "text"
                },
                "requires_further_input": False
            }
        })
    
    elif message_type == "get_status":
        # 返回工作流状态
        engine = get_workflow_engine()
        workflow_def = engine.get_workflow_definition(workflow_id)
        
        await connection_manager.send_message(workflow_id, {
            "type": "WORKFLOW_STATUS",
            "payload": {
                "workflowId": workflow_id,
                "workflowName": workflow_def.name if workflow_def and hasattr(workflow_def, 'name') else workflow_id,
                "status": "running",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    elif message_type == "ping":
        # 心跳响应
        await connection_manager.send_message(workflow_id, {
            "type": "pong",
            "payload": {
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    
    else:
        logger.warning(f"Unknown WebSocket message type: {message_type}")


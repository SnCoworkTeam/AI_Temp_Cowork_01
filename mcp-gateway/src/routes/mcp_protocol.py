"""
MCP协议端点实现
提供标准的MCP（Model Context Protocol）协议接口，支持JSON-RPC 2.0和SSE格式
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from datetime import datetime

from ..tools import tool_registry
from ..core.mcp_client import MCPConnectionError, MCPProtocolError

router = APIRouter()
logger = logging.getLogger(__name__)

# 会话管理（简化版，生产环境应使用Redis或数据库）
_sessions: Dict[str, Dict[str, Any]] = {}


def _generate_session_id() -> str:
    """生成会话ID"""
    return str(uuid.uuid4())


def _get_or_create_session(session_id: Optional[str] = None) -> str:
    """获取或创建会话"""
    if session_id and session_id in _sessions:
        return session_id
    
    new_session_id = _generate_session_id()
    _sessions[new_session_id] = {
        "session_id": new_session_id,
        "created_at": datetime.now(),
        "initialized": False
    }
    return new_session_id


def _is_initialize_request(body: Dict[str, Any]) -> bool:
    """检查是否是initialize请求"""
    return body.get("method") == "initialize"


def _is_initialized_notification(body: Dict[str, Any]) -> bool:
    """检查是否是initialized通知"""
    return body.get("method") == "initialized"


def _format_sse_response(data: Dict[str, Any]) -> str:
    """格式化SSE响应"""
    return f"event: message\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _handle_initialize(params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """处理initialize请求"""
    protocol_version = params.get("protocolVersion", "2024-11-05")
    client_info = params.get("clientInfo", {})
    
    # 获取所有可用工具
    tools = tool_registry.list_tools()
    
    # 转换为MCP工具格式
    mcp_tools = []
    for tool in tools:
        mcp_tools.append({
            "name": tool.get("name"),
            "description": tool.get("description", ""),
            "inputSchema": tool.get("parameters", {})
        })
    
    return {
        "jsonrpc": "2.0",
        "id": None,  # 将在调用处设置
        "result": {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "mcp-gateway",
                "version": "1.0.0"
            }
        }
    }


async def _handle_tools_list(params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """处理tools/list请求"""
    tools = tool_registry.list_tools()
    
    # 转换为MCP工具格式
    mcp_tools = []
    for tool in tools:
        mcp_tools.append({
            "name": tool.get("name"),
            "description": tool.get("description", ""),
            "inputSchema": tool.get("parameters", {})
        })
    
    return {
        "jsonrpc": "2.0",
        "id": None,  # 将在调用处设置
        "result": {
            "tools": mcp_tools
        }
    }


async def _handle_tools_call(
    params: Dict[str, Any],
    session_id: str,
    request_id: Any
) -> Dict[str, Any]:
    """处理tools/call请求"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": "Tool name is required"
            }
        }
    
    try:
        # 执行工具
        from ..models.tool_models import ToolExecutionRequest
        execution_request = ToolExecutionRequest(
            parameters=arguments,
            timeout=30
        )
        
        response = await tool_registry.execute_tool(
            tool_name=tool_name,
            execution_request=execution_request
        )
        
        if response.success:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(response.result, ensure_ascii=False, indent=2)
                        }
                    ],
                    "isError": False
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": "Tool execution failed",
                    "data": str(response.error) if hasattr(response, 'error') else "Unknown error"
                }
            }
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": "Tool execution error",
                "data": str(e)
            }
        }


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="mcp-session-id")
):
    """
    MCP协议主端点
    支持JSON-RPC 2.0协议，可返回JSON或SSE格式
    """
    try:
        # 解析请求体
        body = await request.json()
        
        # 验证JSON-RPC版本
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": "jsonrpc must be '2.0'"
                    }
                }
            )
        
        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})
        
        # 处理会话
        if _is_initialize_request(body):
            session_id = _get_or_create_session()
            _sessions[session_id]["initialized"] = False
        elif _is_initialized_notification(body):
            if not mcp_session_id or mcp_session_id not in _sessions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32001,
                            "message": "Invalid session",
                            "data": "Session ID required for initialized notification"
                        }
                    }
                )
            session_id = mcp_session_id
            _sessions[session_id]["initialized"] = True
            # initialized是通知，不需要响应
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                }
            )
        else:
            # 其他请求需要有效的会话
            if not mcp_session_id or mcp_session_id not in _sessions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32001,
                            "message": "Invalid session",
                            "data": "Valid session ID required"
                        }
                    }
                )
            session_id = mcp_session_id
        
        # 检查是否接受SSE格式
        accept_header = request.headers.get("accept", "")
        use_sse = "text/event-stream" in accept_header.lower()
        
        # 处理不同的方法
        if method == "initialize":
            response_data = await _handle_initialize(params, session_id)
            response_data["id"] = request_id
            
            # 添加会话ID到响应头
            headers = {"mcp-session-id": session_id}
            
            if use_sse:
                # SSE格式响应
                sse_data = _format_sse_response(response_data)
                return StreamingResponse(
                    iter([sse_data]),
                    media_type="text/event-stream",
                    headers=headers
                )
            else:
                # JSON格式响应
                return JSONResponse(content=response_data, headers=headers)
        
        elif method == "initialized":
            # 已在上面处理
            pass
        
        elif method == "tools/list":
            response_data = await _handle_tools_list(params, session_id)
            response_data["id"] = request_id
            
            if use_sse:
                sse_data = _format_sse_response(response_data)
                return StreamingResponse(
                    iter([sse_data]),
                    media_type="text/event-stream"
                )
            else:
                return JSONResponse(content=response_data)
        
        elif method == "tools/call":
            response_data = await _handle_tools_call(params, session_id, request_id)
            
            if use_sse:
                sse_data = _format_sse_response(response_data)
                return StreamingResponse(
                    iter([sse_data]),
                    media_type="text/event-stream"
                )
            else:
                return JSONResponse(content=response_data)
        
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Unknown method: {method}"
                    }
                }
            )
    
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": "Invalid JSON"
                }
            }
        )
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if 'body' in locals() else None,
                "error": {
                    "code": -32000,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
        )


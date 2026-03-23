"""
智能体管理 API 路由
提供智能体注册、管理、执行的完整REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from ..dependencies.database import get_db
from shared_libs.luminaos_common.schemas.agent_schemas import (
    CreateAgentRequest,
    CreateAgentResponse,
    AgentRegistry,
    ExecuteAgentRequest,
    ExecuteAgentResponse,
    ListAgentsResponse,
    AgentError,
    AgentNodeInput,
    AgentNodeOutput,
    AgentContext,
    AgentExecutionRecord,
    AgentStatus,
    AgentType,
    AgentExecutionState
)
from .agent_service import AgentService
from .permissions import check_agent_permissions

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# 智能体注册和管理接口

@router.post("/", response_model=CreateAgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    创建新的智能体

    - **agent**: 智能体完整信息
    - 需要admin权限
    """
    try:
        agent_service = AgentService(db)
        agent_id = await agent_service.create_agent(request.agent, current_user)

        return CreateAgentResponse(
            success=True,
            agent_id=agent_id,
            message="智能体创建成功",
            created_at=datetime.now()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体创建失败: {str(e)}")


@router.get("/", response_model=ListAgentsResponse)
async def list_agents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[AgentStatus] = Query(None, description="状态过滤"),
    agent_type: Optional[AgentType] = Query(None, description="类型过滤"),
    category: Optional[str] = Query(None, description="分类过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    获取智能体列表

    支持分页、过滤和搜索功能
    """
    try:
        agent_service = AgentService(db)
        result = await agent_service.list_agents(
            page=page,
            page_size=page_size,
            status=status,
            agent_type=agent_type,
            category=category,
            search=search,
            user_id=current_user
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体列表失败: {str(e)}")


@router.get("/{agent_id}", response_model=AgentRegistry)
async def get_agent(
    agent_id: str,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    获取指定智能体详情
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体详情失败: {str(e)}")


@router.put("/{agent_id}", response_model=CreateAgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentRegistry,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    更新智能体信息

    - 需要admin权限或智能体创建者权限
    """
    try:
        agent_service = AgentService(db)

        # 检查权限
        existing_agent = await agent_service.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 只有管理员或创建者可以更新
        if existing_agent.created_by != current_user:
            # TODO: 检查是否是管理员
            pass

        updated_agent_id = await agent_service.update_agent(agent_id, agent_data, current_user)

        return CreateAgentResponse(
            success=True,
            agent_id=updated_agent_id,
            message="智能体更新成功",
            created_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新智能体失败: {str(e)}")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    删除智能体

    - 需要admin权限或智能体创建者权限
    - 将会同时删除相关的节点和执行记录
    """
    try:
        agent_service = AgentService(db)

        # 检查权限
        existing_agent = await agent_service.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        # 只有管理员或创建者可以删除
        if existing_agent.created_by != current_user:
            # TODO: 检查是否是管理员
            pass

        await agent_service.delete_agent(agent_id)

        return {"success": True, "message": "智能体删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除智能体失败: {str(e)}")


# 智能体执行接口

@router.post("/{agent_id}/execute", response_model=ExecuteAgentResponse)
async def execute_agent(
    agent_id: str,
    request: ExecuteAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    执行智能体

    - **agent_id**: 要执行的智能体ID
    - **input_data**: 输入数据
    - **context**: 可选的执行上下文
    - **stream**: 是否流式返回结果
    """
    try:
        agent_service = AgentService(db)

        # 检查智能体是否存在且可执行
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        if agent.status != AgentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="智能体未激活，无法执行")

        # 执行智能体
        if request.stream:
            return await execute_agent_streaming(agent_id, request, agent_service, current_user)
        else:
            result = await agent_service.execute_agent(agent_id, request, current_user)
            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体执行失败: {str(e)}")


@router.post("/{agent_id}/execute/stream")
async def execute_agent_streaming(
    agent_id: str,
    request: ExecuteAgentRequest,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    流式执行智能体

    返回Server-Sent Events (SSE)流
    """
    try:
        agent_service = AgentService(db)

        # 检查智能体是否存在且可执行
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        async def generate_stream():
            try:
                async for chunk in agent_service.execute_agent_stream(agent_id, request, current_user):
                    yield f"data: {chunk}\\n\\n"
                yield "data: [DONE]\\n\\n"
            except Exception as e:
                error_data = {
                    "error": str(e),
                    "error_type": "execution_error"
                }
                yield f"data: {error_data}\\n\\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式执行失败: {str(e)}")


@router.get("/{agent_id}/executions")
async def get_execution_history(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    state: Optional[AgentExecutionState] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    获取智能体执行历史
    """
    try:
        agent_service = AgentService(db)

        result = await agent_service.get_execution_history(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
            state=state,
            start_time=start_time,
            end_time=end_time,
            user_id=current_user
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")


@router.get("/{agent_id}/statistics")
async def get_agent_statistics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    获取智能体执行统计信息
    """
    try:
        agent_service = AgentService(db)

        stats = await agent_service.get_agent_statistics(agent_id, days)

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 智能体状态管理接口

@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: str,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    激活智能体
    """
    try:
        agent_service = AgentService(db)
        await agent_service.update_agent_status(agent_id, AgentStatus.ACTIVE, current_user)

        return {"success": True, "message": "智能体已激活"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"激活智能体失败: {str(e)}")


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: str,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    停用智能体
    """
    try:
        agent_service = AgentService(db)
        await agent_service.update_agent_status(agent_id, AgentStatus.INACTIVE, current_user)

        return {"success": True, "message": "智能体已停用"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停用智能体失败: {str(e)}")


# 智能体节点管理接口

@router.post("/{agent_id}/nodes", response_model=Dict[str, Any])
async def create_agent_node(
    agent_id: str,
    workflow_id: str,
    node_data: Dict[str, Any],
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    在工作流中创建智能体节点
    """
    try:
        agent_service = AgentService(db)

        # 检查智能体是否存在
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        node_id = await agent_service.create_agent_node(
            agent_id=agent_id,
            workflow_id=workflow_id,
            node_data=node_data,
            user_id=current_user
        )

        return {
            "success": True,
            "node_id": node_id,
            "message": "智能体节点创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建智能体节点失败: {str(e)}")


@router.get("/{agent_id}/nodes")
async def list_agent_nodes(
    agent_id: str,
    workflow_id: Optional[str] = Query(None),
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    获取智能体的所有节点
    """
    try:
        agent_service = AgentService(db)

        nodes = await agent_service.list_agent_nodes(agent_id, workflow_id)

        return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体节点失败: {str(e)}")


# 智能体类型和分类管理接口

@router.get("/types")
async def get_agent_types():
    """
    获取所有可用的智能体类型
    """
    return {
        "types": [
            {
                "value": agent_type.value,
                "label": agent_type.value,
                "description": f"{agent_type.value.replace('_', ' ').title()} Agent"
            }
            for agent_type in AgentType
        ]
    }


@router.get("/categories")
async def get_agent_categories(
    db: Session = Depends(get_db)
):
    """
    获取所有智能体分类
    """
    try:
        agent_service = AgentService(db)
        categories = await agent_service.get_agent_categories()

        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取智能体分类失败: {str(e)}")


# 错误处理和监控接口

@router.get("/{agent_id}/health")
async def check_agent_health(
    agent_id: str,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    检查智能体健康状态
    """
    try:
        agent_service = AgentService(db)
        health_status = await agent_service.check_agent_health(agent_id)

        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查智能体健康状态失败: {str(e)}")


@router.post("/{agent_id}/test")
async def test_agent(
    agent_id: str,
    test_input: AgentNodeInput,
    current_user: str = Depends(check_agent_permissions),
    db: Session = Depends(get_db)
):
    """
    测试智能体功能

    提供简单的测试接口验证智能体配置
    """
    try:
        agent_service = AgentService(db)

        # 检查智能体是否存在
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="智能体不存在")

        test_result = await agent_service.test_agent(agent_id, test_input, current_user)

        return test_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试智能体失败: {str(e)}")
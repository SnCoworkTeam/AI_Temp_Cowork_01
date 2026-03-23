"""
注册管理路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.agent_spec import AgentSpec, AgentSpecCreate
from ..core.registry import agent_registry

router = APIRouter(tags=["注册管理"])
logger = logging.getLogger(__name__)


@router.post("/agents", response_model=AgentSpec, summary="注册智能体")
async def register_agent(spec_data: AgentSpecCreate):
    """
    注册智能体能力
    
    - **agent_id**: 智能体ID
    - **agent_name**: 智能体名称
    - **agent_url**: 智能体服务URL
    - **capabilities**: 能力列表
    - **description**: 描述（可选）
    - **metadata**: 元数据（可选）
    """
    try:
        spec = await agent_registry.register_agent(spec_data)
        return spec
    except Exception as e:
        logger.error(f"Failed to register agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to register agent: {str(e)}")


@router.delete("/agents/{agent_id}", summary="注销智能体")
async def unregister_agent(agent_id: str):
    """
    注销智能体
    
    - **agent_id**: 智能体ID
    """
    success = await agent_registry.unregister_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"message": "Agent unregistered successfully"}


@router.get("/agents/{agent_id}", response_model=AgentSpec, summary="获取智能体规格")
async def get_agent_spec(agent_id: str):
    """
    获取智能体规格
    
    - **agent_id**: 智能体ID
    """
    spec = await agent_registry.get_agent(agent_id)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return spec


@router.get("/agents", response_model=List[AgentSpec], summary="获取智能体列表")
async def list_agents(limit: int = 100, offset: int = 0):
    """
    获取智能体列表
    
    - **limit**: 限制数量（默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        agents = await agent_registry.list_agents(limit, offset)
        return agents
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.post("/agents/{agent_id}/heartbeat", summary="更新心跳")
async def update_heartbeat(agent_id: str):
    """
    更新智能体心跳
    
    - **agent_id**: 智能体ID
    """
    success = await agent_registry.update_heartbeat(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return {"message": "Heartbeat updated successfully"}


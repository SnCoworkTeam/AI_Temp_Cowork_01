"""
智能体注册表API路由
支持动态智能体注册、发现和查询
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from .dynamic_workflow import get_dynamic_execution_engine
from ..core.agents.protocols import AgentCapabilities

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRegistrationRequest(BaseModel):
    """智能体注册请求"""
    agent_id: str = Field(..., description="智能体ID")
    agent_type: str = Field(..., description="智能体类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="智能体元数据")


class AgentDiscoveryRequest(BaseModel):
    """智能体发现请求"""
    task_type: Optional[str] = Field(None, description="任务类型")
    capabilities: Optional[List[str]] = Field(None, description="所需能力列表")
    input_format: Optional[str] = Field(None, description="输入格式")
    output_format: Optional[str] = Field(None, description="输出格式")


@router.get("/agents")
async def list_agents():
    """列出所有已注册的智能体"""
    try:
        engine = get_dynamic_execution_engine()
        agents = await engine.agent_registry.list_agents()
        capabilities = await engine.agent_registry.get_all_capabilities()
        
        return {
            "success": True,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": capabilities.get(agent.agent_id, {}).to_dict() if capabilities.get(agent.agent_id) else {},
                    "status": agent.get_status()
                }
                for agent in agents
            ],
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取智能体详情"""
    try:
        engine = get_dynamic_execution_engine()
        agent = await engine.agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        capabilities = await engine.agent_registry.get_agent_capabilities(agent_id)
        metadata = await engine.agent_registry.get_agent_metadata(agent_id)
        stats = agent.get_stats()
        
        return {
            "success": True,
            "agent": {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "capabilities": capabilities.to_dict() if capabilities else {},
                "metadata": metadata or {},
                "stats": stats,
                "status": agent.get_status()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/discover")
async def discover_agents(request: AgentDiscoveryRequest):
    """根据需求发现智能体"""
    try:
        engine = get_dynamic_execution_engine()
        requirements = {}
        if request.task_type:
            requirements["task_type"] = request.task_type
        if request.capabilities:
            requirements["capabilities"] = request.capabilities
        if request.input_format:
            requirements["input_format"] = request.input_format
        if request.output_format:
            requirements["output_format"] = request.output_format
        
        agents = await engine.agent_discovery.discover_agents(requirements)
        
        return {
            "success": True,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "capabilities": agent.get_capabilities().to_dict()
                }
                for agent in agents
            ],
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Failed to discover agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/capabilities")
async def get_agent_capabilities(agent_id: str):
    """获取智能体能力描述"""
    try:
        engine = get_dynamic_execution_engine()
        capabilities = await engine.agent_registry.get_agent_capabilities(agent_id)
        if not capabilities:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "capabilities": capabilities.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent capabilities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """获取智能体统计信息"""
    try:
        engine = get_dynamic_execution_engine()
        agent = await engine.agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "stats": agent.get_stats()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/summary")
async def get_performance_summary():
    """获取性能摘要"""
    try:
        engine = get_dynamic_execution_engine()
        if not engine.performance_analyzer:
            return {
                "success": False,
                "message": "Performance analyzer not enabled"
            }
        
        summary = engine.performance_analyzer.get_performance_summary()
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


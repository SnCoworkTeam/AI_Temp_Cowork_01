"""
发现服务路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from ..models.agent_spec import AgentSpecResponse
from ..models.capability_models import CapabilityRequirement, CapabilityType
from ..core.registry import agent_registry

router = APIRouter(tags=["发现服务"])
logger = logging.getLogger(__name__)


@router.post("/discover", response_model=List[AgentSpecResponse], summary="发现智能体")
async def discover_agents(requirements: CapabilityRequirement):
    """
    发现具备特定能力的智能体
    
    - **capabilities**: 需要的能力列表
    - **min_match**: 最少匹配数量（可选）
    - **priority**: 优先级列表（可选）
    """
    try:
        agents = await agent_registry.discover_agents(requirements)
        
        # 转换为响应模型（包含匹配分数）
        results = []
        required_capabilities = set(requirements.capabilities)
        
        for agent in agents:
            agent_capabilities = set(agent.capabilities)
            matching_capabilities = required_capabilities & agent_capabilities
            match_score = len(matching_capabilities) / len(required_capabilities)
            
            result = AgentSpecResponse(
                **agent.dict(),
                match_score=match_score,
                match_reason=f"匹配能力: {', '.join(matching_capabilities)}"
            )
            results.append(result)
        
        return results
    except Exception as e:
        logger.error(f"Failed to discover agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to discover agents: {str(e)}")


@router.get("/capabilities", summary="获取能力列表")
async def list_capabilities():
    """
    获取所有可用的能力类型
    """
    return {
        "capabilities": [
            {
                "type": cap.value,
                "name": cap.name,
                "description": f"{cap.value} 能力"
            }
            for cap in CapabilityType
        ]
    }


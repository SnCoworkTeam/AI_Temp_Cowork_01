"""
智能体注册中心核心逻辑
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from ..models.agent_spec import AgentSpec, AgentSpecCreate
from ..models.capability_models import CapabilityType, CapabilityRequirement

logger = logging.getLogger(__name__)


class AgentRegistry:
    """智能体注册中心"""
    
    def __init__(self):
        # 内存存储（生产环境应使用Redis或数据库）
        self._agents: Dict[str, AgentSpec] = {}
        self._capability_index: Dict[CapabilityType, List[str]] = {}  # 能力到智能体ID的映射
    
    async def register_agent(self, spec_data: AgentSpecCreate) -> AgentSpec:
        """
        注册智能体
        
        Args:
            spec_data: 智能体规格数据
            
        Returns:
            注册的智能体规格
        """
        spec = AgentSpec(
            agent_id=spec_data.agent_id,
            agent_name=spec_data.agent_name,
            agent_url=spec_data.agent_url,
            capabilities=spec_data.capabilities,
            description=spec_data.description,
            metadata=spec_data.metadata,
            registered_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            status="active"
        )
        
        self._agents[spec.agent_id] = spec
        
        # 更新能力索引
        for capability in spec.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            if spec.agent_id not in self._capability_index[capability]:
                self._capability_index[capability].append(spec.agent_id)
        
        logger.info(f"Registered agent: {spec.agent_name} ({spec.agent_id})")
        return spec
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销智能体
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            是否成功注销
        """
        if agent_id not in self._agents:
            return False
        
        spec = self._agents[agent_id]
        
        # 从能力索引中移除
        for capability in spec.capabilities:
            if capability in self._capability_index:
                if agent_id in self._capability_index[capability]:
                    self._capability_index[capability].remove(agent_id)
        
        del self._agents[agent_id]
        logger.info(f"Unregistered agent: {spec.agent_name} ({agent_id})")
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[AgentSpec]:
        """获取智能体规格"""
        return self._agents.get(agent_id)
    
    async def list_agents(self, limit: int = 100, offset: int = 0) -> List[AgentSpec]:
        """列出所有智能体"""
        agents = list(self._agents.values())
        agents.sort(key=lambda x: x.registered_at, reverse=True)
        return agents[offset:offset + limit]
    
    async def discover_agents(
        self,
        requirements: CapabilityRequirement
    ) -> List[AgentSpec]:
        """
        发现具备特定能力的智能体
        
        Args:
            requirements: 能力需求
            
        Returns:
            匹配的智能体列表（按匹配度排序）
        """
        required_capabilities = set(requirements.capabilities)
        candidates = set()
        
        # 找到具备至少一个所需能力的智能体
        for capability in required_capabilities:
            if capability in self._capability_index:
                candidates.update(self._capability_index[capability])
        
        # 计算匹配分数
        matches = []
        for agent_id in candidates:
            agent = self._agents.get(agent_id)
            if not agent or agent.status != "active":
                continue
            
            agent_capabilities = set(agent.capabilities)
            matching_capabilities = required_capabilities & agent_capabilities
            
            # 计算匹配分数
            match_score = len(matching_capabilities) / len(required_capabilities)
            
            # 考虑优先级
            if requirements.priority:
                priority_bonus = sum(
                    0.1 for cap in matching_capabilities
                    if cap in requirements.priority
                )
                match_score += min(priority_bonus, 0.3)
            
            matches.append((agent, match_score))
        
        # 按匹配分数排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # 应用最少匹配数量过滤
        if requirements.min_match:
            matches = [
                (agent, score) for agent, score in matches
                if len(set(agent.capabilities) & required_capabilities) >= requirements.min_match
            ]
        
        return [agent for agent, _ in matches]
    
    async def update_heartbeat(self, agent_id: str) -> bool:
        """更新智能体心跳"""
        agent = self._agents.get(agent_id)
        if agent:
            agent.last_heartbeat = datetime.utcnow()
            return True
        return False


# 全局注册中心实例
agent_registry = AgentRegistry()


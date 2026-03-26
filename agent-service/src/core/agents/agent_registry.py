"""
智能体注册发现机制
支持动态智能体注册、发现和加载
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from .standardized_agent import StandardizedAgent
from .protocols import AgentCapabilities, StandardTask

logger = logging.getLogger(__name__)


class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self.agents: Dict[str, StandardizedAgent] = {}
        self.agent_capabilities: Dict[str, AgentCapabilities] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def register_agent(
        self,
        agent: StandardizedAgent,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        注册智能体
        
        Args:
            agent: 智能体实例
            metadata: 智能体元数据
        """
        async with self._lock:
            self.agents[agent.agent_id] = agent
            self.agent_capabilities[agent.agent_id] = agent.get_capabilities()
            self.agent_metadata[agent.agent_id] = metadata or {}
            self.agent_metadata[agent.agent_id]["registered_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Registered agent: {agent.agent_id} ({agent.name})")
    
    async def unregister_agent(self, agent_id: str):
        """注销智能体"""
        async with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                del self.agent_capabilities[agent_id]
                del self.agent_metadata[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")
    
    async def get_agent(self, agent_id: str) -> Optional[StandardizedAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)
    
    async def list_agents(self) -> List[StandardizedAgent]:
        """列出所有智能体"""
        return list(self.agents.values())
    
    async def discover_agents_by_capability(
        self,
        capability: str
    ) -> List[StandardizedAgent]:
        """
        根据能力发现智能体
        
        Args:
            capability: 能力名称
            
        Returns:
            具有该能力的智能体列表
        """
        matching_agents = []
        for agent in self.agents.values():
            capabilities = self.agent_capabilities[agent.agent_id]
            if capability in capabilities.capabilities:
                matching_agents.append(agent)
        return matching_agents
    
    async def discover_agents_by_task_type(
        self,
        task_type: str
    ) -> List[StandardizedAgent]:
        """
        根据任务类型发现智能体
        
        Args:
            task_type: 任务类型
            
        Returns:
            支持该任务类型的智能体列表
        """
        matching_agents = []
        for agent in self.agents.values():
            capabilities = self.agent_capabilities[agent.agent_id]
            if task_type in capabilities.supported_task_types:
                matching_agents.append(agent)
        return matching_agents
    
    async def find_best_agent_for_task(
        self,
        task: StandardTask
    ) -> Optional[StandardizedAgent]:
        """
        为任务找到最佳智能体
        
        Args:
            task: 标准化任务
            
        Returns:
            最佳智能体，如果没有则返回None
        """
        # 首先根据任务类型筛选
        candidates = await self.discover_agents_by_task_type(task.task_type)
        
        if not candidates:
            return None
        
        # 如果只有一个候选，直接返回
        if len(candidates) == 1:
            return candidates[0]
        
        # 如果有多个候选，选择最适合的
        # 这里可以根据历史性能、当前负载等因素选择
        # 目前简单返回第一个
        return candidates[0]
    
    async def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilities]:
        """获取智能体能力描述"""
        return self.agent_capabilities.get(agent_id)
    
    async def get_all_capabilities(self) -> Dict[str, AgentCapabilities]:
        """获取所有智能体的能力描述"""
        return self.agent_capabilities.copy()
    
    async def get_agent_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体元数据"""
        return self.agent_metadata.get(agent_id)
    
    async def update_agent_metadata(
        self,
        agent_id: str,
        metadata: Dict[str, Any]
    ):
        """更新智能体元数据"""
        async with self._lock:
            if agent_id in self.agent_metadata:
                self.agent_metadata[agent_id].update(metadata)
                self.agent_metadata[agent_id]["updated_at"] = datetime.utcnow().isoformat()


class AgentDiscoveryService:
    """智能体发现服务"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    async def discover_agents(
        self,
        requirements: Dict[str, Any]
    ) -> List[StandardizedAgent]:
        """
        根据需求发现智能体
        
        Args:
            requirements: 需求字典，包含：
                - task_type: 任务类型
                - capabilities: 所需能力列表
                - input_format: 输入格式
                - output_format: 输出格式
                
        Returns:
            匹配的智能体列表
        """
        candidates = []
        
        # 根据任务类型筛选
        if "task_type" in requirements:
            task_type_candidates = await self.registry.discover_agents_by_task_type(
                requirements["task_type"]
            )
            candidates.extend(task_type_candidates)
        
        # 根据能力筛选
        if "capabilities" in requirements:
            for capability in requirements["capabilities"]:
                capability_candidates = await self.registry.discover_agents_by_capability(
                    capability
                )
                candidates.extend(capability_candidates)
        
        # 去重
        unique_candidates = {agent.agent_id: agent for agent in candidates}.values()
        
        # 进一步筛选（根据输入输出格式等）
        filtered = []
        for agent in unique_candidates:
            capabilities = await self.registry.get_agent_capabilities(agent.agent_id)
            if not capabilities:
                continue
            
            # 检查输入格式
            if "input_format" in requirements:
                if requirements["input_format"] not in capabilities.supported_input_formats:
                    continue
            
            # 检查输出格式
            if "output_format" in requirements:
                if requirements["output_format"] not in capabilities.supported_output_formats:
                    continue
            
            filtered.append(agent)
        
        return list(filtered)
    
    async def rank_agents(
        self,
        agents: List[StandardizedAgent],
        task: StandardTask
    ) -> List[StandardizedAgent]:
        """
        对智能体进行排序（根据适合度）
        
        Args:
            agents: 智能体列表
            task: 任务
            
        Returns:
            排序后的智能体列表
        """
        # 简单实现：根据历史成功率排序
        # 可以扩展为更复杂的评分机制
        agent_scores = []
        for agent in agents:
            stats = agent.get_stats()
            score = stats.get("success_rate", 0.0) * 0.7 + (1.0 / (stats.get("average_execution_time", 1.0) + 1)) * 0.3
            agent_scores.append((score, agent))
        
        # 按分数降序排序
        agent_scores.sort(key=lambda x: x[0], reverse=True)
        return [agent for _, agent in agent_scores]



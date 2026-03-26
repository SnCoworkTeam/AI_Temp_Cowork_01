"""
基础智能体接口
所有智能体的基类

注意：为了保持向后兼容，保留IntelligentAgent作为旧接口。
新代码应该使用StandardizedAgent（在standardized_agent.py中）。
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class IntelligentAgent(ABC):
    """智能体基类"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Optional[Dict[str, str]] = None
    ):
        """
        初始化智能体
        
        Args:
            agent_id: 智能体ID
            name: 智能体名称
            description: 智能体描述
            capabilities: 智能体能力字典
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or {}
        self.created_at = datetime.utcnow()
        self.last_executed_at: Optional[datetime] = None
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    @abstractmethod
    async def analyze_task(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务（智能体特定的分析逻辑）
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果
        """
        pass
    
    async def execute_with_tracking(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行任务（带跟踪）
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            
        Returns:
            执行结果（包含执行元数据）
        """
        start_time = datetime.utcnow()
        self.execution_count += 1
        
        try:
            result = await self.execute(input_data, context)
            
            # 检查智能体返回的结果中是否包含 execution_success 或 success 字段
            # 如果智能体明确返回了 False，则视为失败
            execution_success = True
            if isinstance(result, dict):
                # 检查智能体返回的 execution_success 或 success 字段
                if result.get("execution_success") is False or result.get("success") is False:
                    execution_success = False
                    self.failure_count += 1
                else:
                    self.success_count += 1
            else:
                self.success_count += 1
            
            self.last_executed_at = datetime.utcnow()
            execution_time = (self.last_executed_at - start_time).total_seconds()
            
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "agent_type": self.__class__.__name__,
                "execution_success": execution_success,
                "result": result,
                "execution_metadata": {
                    "execution_time": execution_time,
                    "execution_count": self.execution_count,
                    "success_count": self.success_count,
                    "failure_count": self.failure_count
                }
            }
        except Exception as e:
            self.failure_count += 1
            self.last_executed_at = datetime.utcnow()
            execution_time = (self.last_executed_at - start_time).total_seconds()
            
            logger.error(f"Agent {self.name} execution failed: {e}", exc_info=True)
            
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "agent_type": self.__class__.__name__,
                "execution_success": False,
                "error": str(e),
                "execution_metadata": {
                    "execution_time": execution_time,
                    "execution_count": self.execution_count,
                    "success_count": self.success_count,
                    "failure_count": self.failure_count
                }
            }
    
    def get_capabilities(self) -> Dict[str, str]:
        """获取智能体能力"""
        return self.capabilities
    
    def get_stats(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.execution_count if self.execution_count > 0 else 0.0,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None
        }


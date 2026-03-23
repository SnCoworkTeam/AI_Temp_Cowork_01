"""
基础AI智能体
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """AI智能体基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools: List[Any] = []
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入并生成响应
        Args:
            input_data: 输入数据
            context: 上下文信息
        Returns:
            处理结果
        """
        pass
    
    def add_tool(self, tool: Any):
        """添加工具"""
        self.tools.append(tool)
        logger.info(f"Added tool to agent {self.name}: {tool}")










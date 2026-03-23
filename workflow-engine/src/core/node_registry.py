"""
节点注册表
支持动态添加节点类型，提供内置节点实现
"""
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from ..nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class NodeFactory:
    """节点工厂，用于创建节点实例"""
    
    def __init__(self):
        self._node_types: Dict[str, Callable] = {}
        self._register_builtin_nodes()
    
    def _register_builtin_nodes(self):
        """注册内置节点类型"""
        # LLM节点
        self.register_node_type("llm", self._create_llm_node)
        
        # 工具调用节点
        self.register_node_type("tool", self._create_tool_node)
        
        # 条件判断节点
        self.register_node_type("condition", self._create_condition_node)
        
        # 数据转换节点
        self.register_node_type("transform", self._create_transform_node)
        
        # HTTP请求节点
        self.register_node_type("http", self._create_http_node)
        
        # 开始节点
        self.register_node_type("start", self._create_start_node)
        
        # 结束节点
        self.register_node_type("end", self._create_end_node)
        
        # 延迟节点
        self.register_node_type("delay", self._create_delay_node)
        
        # 日志节点
        self.register_node_type("log", self._create_log_node)
        
        # 知识库相关节点
        self.register_node_type("knowledge_search", self._create_knowledge_search_node)
        self.register_node_type("document_processing", self._create_document_processing_node)
        self.register_node_type("knowledge_enhancement", self._create_knowledge_enhancement_node)
        
        # 智能体节点
        self.register_node_type("agent", self._create_agent_node)
    
    def register_node_type(
        self,
        node_type: str,
        factory_func: Callable[[Dict[str, Any]], BaseNode]
    ):
        """
        注册节点类型
        
        Args:
            node_type: 节点类型名称
            factory_func: 节点工厂函数
        """
        self._node_types[node_type] = factory_func
        logger.info(f"Registered node type: {node_type}")
    
    def create_node(self, node_config: Dict[str, Any]) -> BaseNode:
        """
        创建节点实例
        
        Args:
            node_config: 节点配置
        
        Returns:
            节点实例
        """
        node_type = node_config.get("type", "task")
        
        if node_type not in self._node_types:
            raise ValueError(f"Unknown node type: {node_type}")
        
        factory_func = self._node_types[node_type]
        return factory_func(node_config)
    
    def _create_llm_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建LLM节点"""
        # 使用src/nodes/llm_node.py中的完整实现（支持LangChain和DeepSeek）
        from ..nodes.llm_node import LLMNode
        return LLMNode(
            name=config.get("name", "llm_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_tool_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建工具调用节点"""
        from .nodes.tool_node import ToolNode
        return ToolNode(
            name=config.get("name", "tool_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_condition_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建条件判断节点"""
        from .nodes.condition_node import ConditionNode
        return ConditionNode(
            name=config.get("name", "condition_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_transform_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建数据转换节点"""
        from .nodes.transform_node import TransformNode
        return TransformNode(
            name=config.get("name", "transform_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_http_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建HTTP请求节点"""
        from .nodes.http_node import HTTPNode
        return HTTPNode(
            name=config.get("name", "http_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_start_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建开始节点"""
        from .nodes.start_node import StartNode
        return StartNode(
            name=config.get("name", "start"),
            description=config.get("description", "Start node")
        )
    
    def _create_end_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建结束节点"""
        from .nodes.end_node import EndNode
        return EndNode(
            name=config.get("name", "end"),
            description=config.get("description", "End node")
        )
    
    def _create_delay_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建延迟节点"""
        from .nodes.delay_node import DelayNode
        return DelayNode(
            name=config.get("name", "delay_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_log_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建日志节点"""
        from .nodes.log_node import LogNode
        return LogNode(
            name=config.get("name", "log_node"),
            description=config.get("description", ""),
            config=config.get("config", {})
        )
    
    def _create_knowledge_search_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建知识搜索节点"""
        from ..nodes.knowledge_search_node import KnowledgeSearchNode
        return KnowledgeSearchNode(
            name=config.get("name", "knowledge_search_node"),
            description=config.get("description", ""),
            config=config.get("config", {}),
            node_id=config.get("id")
        )
    
    def _create_document_processing_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建文档处理节点"""
        from ..nodes.document_processing_node import DocumentProcessingNode
        return DocumentProcessingNode(
            name=config.get("name", "document_processing_node"),
            description=config.get("description", ""),
            config=config.get("config", {}),
            node_id=config.get("id")
        )
    
    def _create_knowledge_enhancement_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建知识增强节点"""
        from ..nodes.knowledge_enhancement_node import KnowledgeEnhancementNode
        return KnowledgeEnhancementNode(
            name=config.get("name", "knowledge_enhancement_node"),
            description=config.get("description", ""),
            config=config.get("config", {}),
            node_id=config.get("id")
        )
    
    def _create_agent_node(self, config: Dict[str, Any]) -> BaseNode:
        """创建智能体节点"""
        from ..nodes.agent_node import AgentNode
        return AgentNode(
            name=config.get("name", "agent_node"),
            description=config.get("description", ""),
            config=config.get("config", {}),
            node_id=config.get("id")
        )
    
    def list_node_types(self) -> List[str]:
        """列出所有已注册的节点类型"""
        return list(self._node_types.keys())


class NodeRegistry:
    """节点注册表（单例）"""
    
    _instance: Optional['NodeRegistry'] = None
    _factory: Optional[NodeFactory] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._factory = NodeFactory()
        return cls._instance
    
    @property
    def factory(self) -> NodeFactory:
        """获取节点工厂"""
        return self._factory
    
    def register_node_type(
        self,
        node_type: str,
        factory_func: Callable[[Dict[str, Any]], BaseNode]
    ):
        """注册节点类型"""
        self._factory.register_node_type(node_type, factory_func)
    
    def create_node(self, node_config: Dict[str, Any]) -> BaseNode:
        """创建节点实例"""
        return self._factory.create_node(node_config)
    
    def list_node_types(self) -> List[str]:
        """列出所有节点类型"""
        return self._factory.list_node_types()


# 全局节点注册表实例
node_registry = NodeRegistry()


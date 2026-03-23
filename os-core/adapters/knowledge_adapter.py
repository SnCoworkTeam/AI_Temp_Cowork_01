"""
知识项适配器
从知识库/EA服务适配知识项为统一资源
"""
from typing import List, Dict, Any, Optional
import logging

try:
    from ..resource_model import KnowledgeItemResource, ResourceType
    from ..resource_registry import ResourceRegistry
except ImportError:
    from resource_model import KnowledgeItemResource, ResourceType
    from resource_registry import ResourceRegistry

logger = logging.getLogger(__name__)


class KnowledgeAdapter:
    """知识项适配器"""
    
    def __init__(self, registry: ResourceRegistry):
        """
        初始化知识项适配器
        
        Args:
            registry: 资源注册表
        """
        self.registry = registry
        logger.info("知识项适配器初始化完成")
    
    def adapt_from_knowledge_base(
        self,
        kb_item: Dict[str, Any]
    ) -> KnowledgeItemResource:
        """
        从知识库项适配为知识资源
        
        Args:
            kb_item: 知识库项信息字典
            
        Returns:
            KnowledgeItemResource: 知识项资源对象
        """
        resource = KnowledgeItemResource(
            id=f"kb:{kb_item.get('id', 'unknown')}",
            name=kb_item.get("title", kb_item.get("name", "未知知识项")),
            description=kb_item.get("description", kb_item.get("summary", "")),
            uri=f"kb://{kb_item.get('id', 'unknown')}",
            content=kb_item.get("content", kb_item.get("text", "")),
            content_type="document",
            source=kb_item.get("source", "knowledge_base"),
            vector_id=kb_item.get("vector_id"),
            knowledge_metadata={
                "source": "knowledge_base",
                "kb_id": kb_item.get("kb_id"),
                "category": kb_item.get("category"),
                "tags": kb_item.get("tags", []),
                "original_item": kb_item
            },
            capabilities=["query", "search", "analyze"]
        )
        
        return resource
    
    def adapt_from_ea_node(
        self,
        ea_node: Dict[str, Any]
    ) -> KnowledgeItemResource:
        """
        从EA节点适配为知识资源
        
        Args:
            ea_node: EA节点信息字典
            
        Returns:
            KnowledgeItemResource: 知识项资源对象
        """
        node_type = ea_node.get("type", "unknown")
        node_name = ea_node.get("name", "未知EA节点")
        
        # 构建描述
        description = ea_node.get("description", "")
        if not description:
            description = f"{node_type}: {node_name}"
        
        resource = KnowledgeItemResource(
            id=f"ea:{ea_node.get('id', 'unknown')}",
            name=node_name,
            description=description,
            uri=f"ea://{node_type}/{ea_node.get('id', 'unknown')}",
            content=self._extract_ea_content(ea_node),
            content_type="ea_node",
            source="enterprise_architecture",
            vector_id=ea_node.get("vector_id"),
            knowledge_metadata={
                "source": "enterprise_architecture",
                "ea_type": node_type,
                "ea_id": ea_node.get("id"),
                "business_domain": ea_node.get("business_domain"),
                "relationships": ea_node.get("relationships", {}),
                "original_node": ea_node
            },
            capabilities=["query", "search", "analyze"]
        )
        
        return resource
    
    def adapt_from_document(
        self,
        document: Dict[str, Any]
    ) -> KnowledgeItemResource:
        """
        从文档适配为知识资源
        
        Args:
            document: 文档信息字典
            
        Returns:
            KnowledgeItemResource: 知识项资源对象
        """
        resource = KnowledgeItemResource(
            id=f"doc:{document.get('id', 'unknown')}",
            name=document.get("title", document.get("filename", "未知文档")),
            description=document.get("description", document.get("summary", "")),
            uri=f"doc://{document.get('id', 'unknown')}",
            content=document.get("content", document.get("text", "")),
            content_type="document",
            source=document.get("source", "document_service"),
            vector_id=document.get("vector_id"),
            knowledge_metadata={
                "source": "document_service",
                "file_type": document.get("file_type"),
                "file_size": document.get("file_size"),
                "upload_date": document.get("upload_date"),
                "author": document.get("author"),
                "original_document": document
            },
            capabilities=["query", "search", "analyze"]
        )
        
        return resource
    
    def register_knowledge_items(
        self,
        items: List[Dict[str, Any]],
        source: str = "kb"
    ) -> int:
        """
        批量注册知识项
        
        Args:
            items: 知识项信息列表
            source: 数据源类型（"kb" | "ea" | "doc"）
            
        Returns:
            int: 成功注册的数量
        """
        registered_count = 0
        
        for item in items:
            try:
                if source == "kb":
                    resource = self.adapt_from_knowledge_base(item)
                elif source == "ea":
                    resource = self.adapt_from_ea_node(item)
                else:
                    resource = self.adapt_from_document(item)
                
                if self.registry.register(resource):
                    registered_count += 1
                    
            except Exception as e:
                logger.error(f"注册知识项失败: {e}")
        
        logger.info(f"批量注册知识项完成: {registered_count}/{len(items)}")
        return registered_count
    
    def _extract_ea_content(self, ea_node: Dict[str, Any]) -> str:
        """从EA节点中提取内容"""
        content_parts = []
        
        # 添加名称
        if "name" in ea_node:
            content_parts.append(f"名称: {ea_node['name']}")
        
        # 添加描述
        if "description" in ea_node:
            content_parts.append(f"描述: {ea_node['description']}")
        
        # 添加属性
        if "properties" in ea_node:
            for key, value in ea_node["properties"].items():
                content_parts.append(f"{key}: {value}")
        
        # 添加关系描述
        if "relationships" in ea_node:
            for rel_type, related_nodes in ea_node["relationships"].items():
                content_parts.append(f"{rel_type}: {', '.join(related_nodes)}")
        
        return "\n".join(content_parts)


"""
文档实体关联服务
将知识库文档与业务实体关联
"""
import logging
import httpx
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..services.metadata_catalog import MetadataCatalogService

logger = logging.getLogger(__name__)


class DocumentEntityLinker:
    """文档实体关联服务"""
    
    def __init__(self, db: Session):
        """
        初始化文档实体关联服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.kg_repo = KnowledgeGraphRepository(db)
        self.catalog = MetadataCatalogService(db)
        self.knowledge_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://knowledge-base:8004")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def link_documents_to_entities(
        self,
        document_ids: Optional[List[str]] = None,
        entity_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        将文档与实体关联
        
        Args:
            document_ids: 文档ID列表（如果为None，处理所有文档）
            entity_ids: 实体ID列表（如果为None，处理所有实体）
        
        Returns:
            关联结果统计
        """
        try:
            # 1. 获取文档列表
            documents = await self._get_documents(document_ids)
            
            # 2. 获取实体列表
            entities = self._get_entities(entity_ids)
            
            # 3. 提取文档中的实体
            document_entities = await self._extract_entities_from_documents(documents)
            
            # 4. 建立关联
            links_created = 0
            for doc_id, doc_entities in document_entities.items():
                for entity_name in doc_entities:
                    # 查找匹配的实体
                    matched_entity = self._find_matching_entity(entity_name, entities)
                    if matched_entity:
                        # 创建关联关系
                        link_created = await self._create_document_entity_link(
                            doc_id, matched_entity["id"]
                        )
                        if link_created:
                            links_created += 1
            
            self.db.commit()
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "entities_processed": len(entities),
                "links_created": links_created
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to link documents to entities: {e}", exc_info=True)
            raise
    
    async def _get_documents(self, document_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
        """获取文档列表"""
        try:
            if document_ids:
                # 获取指定文档
                documents = []
                for doc_id in document_ids:
                    response = await self.http_client.get(
                        f"{self.knowledge_base_url}/api/documents/{doc_id}"
                    )
                    if response.status_code == 200:
                        documents.append(response.json())
            else:
                # 获取所有文档
                response = await self.http_client.get(
                    f"{self.knowledge_base_url}/api/documents",
                    params={"limit": 1000}
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        documents = data
                    elif isinstance(data, dict):
                        # 尝试多种可能的字段名
                        documents = data.get("documents", data.get("items", data.get("data", [])))
                        # 如果还是空，检查是否有嵌套结构
                        if not documents and "data" in data:
                            documents = data["data"].get("documents", data["data"].get("items", []))
                    else:
                        documents = []
                else:
                    logger.warning(f"Failed to get documents: HTTP {response.status_code}")
                    documents = []
            
            logger.info(f"Retrieved {len(documents)} documents from knowledge-base")
            return documents
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []
    
    def _get_entities(self, entity_ids: Optional[List[int]]) -> List[Dict[str, Any]]:
        """获取实体列表"""
        entities = self.catalog.list_business_entities(limit=10000)
        
        if entity_ids:
            entities = [e for e in entities if e.id in entity_ids]
        
        # 转换为字典格式
        entity_list = []
        for entity in entities:
            if isinstance(entity, dict):
                entity_list.append(entity)
            else:
                entity_list.append({
                    "id": entity.id,
                    "name": entity.name,
                    "display_name": entity.display_name,
                    "description": entity.description
                })
        
        return entity_list
    
    async def _extract_entities_from_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        从文档中提取实体名称
        
        简单实现：基于实体名称在文档内容中的出现
        可以后续增强为NER（命名实体识别）
        """
        document_entities = {}
        
        # 获取所有实体名称（只获取一次）
        all_entities = self._get_entities(None)
        entity_names = [e.get("name") for e in all_entities if e.get("name")]
        entity_display_names = [e.get("display_name") for e in all_entities if e.get("display_name")]
        
        logger.info(f"Processing {len(documents)} documents, {len(entity_names)} entities available")
        
        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                continue
            
            # 尝试多种方式获取文档内容
            content = doc.get("content", "") or doc.get("summary", "") or doc.get("title", "") or doc.get("filename", "")
            
            # 如果文档内容为空，尝试从knowledge-base获取文档chunks
            if not content or len(content) < 10:
                try:
                    # 获取文档chunks
                    chunks_response = await self.http_client.get(
                        f"{self.knowledge_base_url}/api/documents/{doc_id}/chunks",
                        params={"limit": 10}
                    )
                    if chunks_response.status_code == 200:
                        chunks_data = chunks_response.json()
                        chunks = chunks_data.get("chunks", chunks_data.get("items", []))
                        if chunks:
                            # 合并chunks内容
                            content = " ".join([chunk.get("content", "") for chunk in chunks if chunk.get("content")])
                except Exception as e:
                    logger.debug(f"Failed to get chunks for document {doc_id}: {e}")
            
            if not content or len(content) < 10:
                logger.debug(f"Skipping document {doc_id}: no content available")
                continue
            
            # 查找文档中出现的实体（同时匹配name和display_name）
            found_entities = []
            content_lower = content.lower()
            
            for i, entity_name in enumerate(entity_names):
                if entity_name and entity_name.lower() in content_lower:
                    found_entities.append(entity_name)
                elif i < len(entity_display_names):
                    display_name = entity_display_names[i]
                    if display_name and display_name.lower() in content_lower:
                        found_entities.append(entity_name)  # 使用entity_name作为key
            
            # 也检查文档标题中的关键词匹配
            doc_title = doc.get("title", "") or doc.get("filename", "")
            if doc_title:
                for i, entity_name in enumerate(entity_names):
                    if entity_name and entity_name.lower() in doc_title.lower():
                        if entity_name not in found_entities:
                            found_entities.append(entity_name)
            
            if found_entities:
                document_entities[doc_id] = found_entities
                logger.debug(f"Found {len(found_entities)} entities in document {doc_id}")
        
        logger.info(f"Extracted entities from {len(document_entities)} documents")
        return document_entities
    
    def _find_matching_entity(
        self,
        entity_name: str,
        entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """查找匹配的实体"""
        entity_name_lower = entity_name.lower()
        
        for entity in entities:
            name = entity.get("name", "").lower()
            display_name = entity.get("display_name", "").lower()
            
            if name == entity_name_lower or display_name == entity_name_lower:
                return entity
        
        return None
    
    async def _create_document_entity_link(
        self,
        document_id: str,
        entity_id: int
    ) -> bool:
        """
        创建文档-实体关联关系
        
        在知识图谱中创建边，连接文档节点和实体节点
        """
        try:
            # 查找或创建文档节点
            doc_node = self.kg_repo.get_node_by_label(
                f"document_{document_id}",
                node_type="document"
            )
            
            if not doc_node:
                # 创建文档节点
                doc_node = self.kg_repo.create_node(
                    label=f"document_{document_id}",
                    node_type="document",
                    properties={
                        "document_id": document_id,
                        "source": "knowledge-base"
                    }
                )
            
            # 查找实体对应的知识图谱节点
            entity_node = None
            all_nodes = self.kg_repo.list_nodes(limit=10000, node_type="concept")
            for node in all_nodes:
                node_props = node.properties or {}
                if str(node_props.get("entity_id")) == str(entity_id):
                    entity_node = node
                    break
            
            if not entity_node:
                # 如果实体节点不存在，跳过
                logger.warning(f"Entity node not found for entity_id={entity_id}, skipping link creation")
                return False
            
            # 验证节点ID不为None
            if not doc_node.id or not entity_node.id:
                logger.warning(f"Node ID is None. doc_node.id={doc_node.id}, entity_node.id={entity_node.id}, skipping link creation")
                return False
            
            # 检查是否已存在边
            existing_edges = self.kg_repo.get_edges_by_node(str(doc_node.id), direction="out")
            for edge in existing_edges:
                if str(edge.target_node_id) == str(entity_node.id):
                    return False  # 已存在，不重复创建
            
            # 创建边
            edge = self.kg_repo.create_edge(
                source_id=str(doc_node.id),
                target_id=str(entity_node.id),
                relationship_type="mentions",
                properties={
                    "source_type": "document",
                    "target_type": "concept",
                    "document_id": document_id,
                    "entity_id": entity_id
                }
            )
            
            return edge is not None
            
        except Exception as e:
            logger.error(f"Failed to create document-entity link: {e}")
            return False
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()




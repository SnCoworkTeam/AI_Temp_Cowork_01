"""
本体构建器
从metadata-service获取业务实体，构建业务本体
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository

logger = logging.getLogger(__name__)


class OntologyBuilder:
    """本体构建器"""
    
    def __init__(self, db: Session, kg_repo: KnowledgeGraphRepository):
        self.db = db
        self.kg_repo = kg_repo
        self.metadata_service_url = os.getenv("METADATA_SERVICE_URL", "http://metadata-service:8005")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def build_business_ontology(self) -> Dict[str, Any]:
        """
        从metadata-service获取业务实体，构建业务本体
        
        Returns:
            本体数据
        """
        try:
            # 1. 从metadata-service获取业务实体
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 1000}
            )
            response.raise_for_status()
            entities = response.json()
            
            # 处理不同的响应格式
            if isinstance(entities, list):
                entity_list = entities
            elif isinstance(entities, dict):
                entity_list = entities.get("items", entities.get("data", []))
            else:
                entity_list = []
            
            # 2. 构建概念层次结构
            concepts = self._build_concept_hierarchy(entity_list)
            
            # 3. 定义实体关系和属性
            relationships = self._extract_relationships(entity_list)
            
            # 4. 存储到知识图谱
            ontology_id = await self._store_ontology(concepts, relationships)
            
            return {
                "success": True,
                "ontology_id": ontology_id,
                "concepts": len(concepts),
                "relationships": len(relationships),
                "concepts_detail": concepts[:10] if len(concepts) > 10 else concepts  # 返回前10个概念详情
            }
            
        except Exception as e:
            logger.error(f"Failed to build business ontology: {e}", exc_info=True)
            raise
    
    async def build_sap_business_ontology(self) -> Dict[str, Any]:
        """
        构建SAP业务本体（按模块层次组织）
        
        Returns:
            本体数据，包含模块层次结构
        """
        try:
            # 1. 从metadata-service获取SAP业务实体
            response = await self.http_client.get(
                f"{self.metadata_service_url}/api/business-entities",
                params={"limit": 10000}
            )
            response.raise_for_status()
            entities = response.json()
            
            if isinstance(entities, list):
                entity_list = entities
            elif isinstance(entities, dict):
                entity_list = entities.get("items", entities.get("data", []))
            else:
                entity_list = []
            
            # 2. 按模块组织实体
            organized_concepts = self._organize_by_module(entity_list)
            
            # 3. 构建模块层次结构
            module_hierarchy = self._build_module_hierarchy(organized_concepts)
            
            # 4. 提取关系
            relationships = self._extract_relationships(entity_list)
            
            # 5. 存储到知识图谱
            ontology_id = await self._store_sap_ontology(organized_concepts, relationships, module_hierarchy)
            
            return {
                "success": True,
                "ontology_id": ontology_id,
                "modules": len(module_hierarchy),
                "concepts": sum(len(concepts) for concepts in organized_concepts.values()),
                "relationships": len(relationships),
                "module_hierarchy": module_hierarchy
            }
            
        except Exception as e:
            logger.error(f"Failed to build SAP business ontology: {e}", exc_info=True)
            raise
    
    def _organize_by_module(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """按SAP模块组织实体"""
        organized = {}
        
        for entity in entities:
            metadata = entity.get("metadata", {}) or entity.get("extra_metadata", {})
            module = metadata.get("sap_module", "OTHER")
            sub_module = metadata.get("sap_sub_module", "General")
            
            # 创建模块键
            module_key = f"{module}/{sub_module}"
            
            if module_key not in organized:
                organized[module_key] = []
            
            organized[module_key].append(entity)
        
        return organized
    
    def _build_module_hierarchy(self, organized_concepts: Dict[str, List[Dict]]) -> List[Dict]:
        """构建模块层次结构"""
        hierarchy = []
        modules = {}
        
        # 提取模块和子模块
        for module_key, concepts in organized_concepts.items():
            module, sub_module = module_key.split("/", 1)
            
            if module not in modules:
                modules[module] = {
                    "name": module,
                    "display_name": self._get_module_display_name(module),
                    "sub_modules": {},
                    "concepts_count": 0
                }
            
            if sub_module not in modules[module]["sub_modules"]:
                modules[module]["sub_modules"][sub_module] = {
                    "name": sub_module,
                    "display_name": sub_module,
                    "concepts_count": 0
                }
            
            modules[module]["sub_modules"][sub_module]["concepts_count"] += len(concepts)
            modules[module]["concepts_count"] += len(concepts)
        
        # 转换为列表格式
        for module_name, module_data in modules.items():
            hierarchy.append({
                "module": module_name,
                "display_name": module_data["display_name"],
                "concepts_count": module_data["concepts_count"],
                "sub_modules": [
                    {
                        "name": sub_name,
                        "display_name": sub_data["display_name"],
                        "concepts_count": sub_data["concepts_count"]
                    }
                    for sub_name, sub_data in module_data["sub_modules"].items()
                ]
            })
        
        return hierarchy
    
    def _get_module_display_name(self, module: str) -> str:
        """获取模块显示名称"""
        module_names = {
            "FI": "财务会计",
            "CO": "管理会计",
            "SD": "销售与分销",
            "MM": "物料管理",
            "PP": "生产计划",
            "HR": "人力资源",
            "OTHER": "其他"
        }
        return module_names.get(module, module)
    
    async def _store_sap_ontology(
        self,
        organized_concepts: Dict[str, List[Dict]],
        relationships: List[Dict],
        module_hierarchy: List[Dict]
    ) -> str:
        """存储SAP本体到知识图谱"""
        try:
            stored_nodes = []
            stored_edges = []
            
            # 1. 存储模块节点
            for module_info in module_hierarchy:
                module_node = self.kg_repo.create_node(
                    label=f"SAP_{module_info['module']}_Module",
                    node_type="sap_module",
                    properties={
                        "name": module_info["module"],
                        "display_name": module_info["display_name"],
                        "concepts_count": module_info["concepts_count"]
                    }
                )
                stored_nodes.append(str(module_node.id))
                
                # 2. 存储子模块节点
                for sub_module_info in module_info["sub_modules"]:
                    sub_module_node = self.kg_repo.create_node(
                        label=f"SAP_{module_info['module']}_{sub_module_info['name']}_SubModule",
                        node_type="sap_sub_module",
                        properties={
                            "name": sub_module_info["name"],
                            "display_name": sub_module_info["display_name"],
                            "concepts_count": sub_module_info["concepts_count"],
                            "parent_module": module_info["module"]
                        }
                    )
                    stored_nodes.append(str(sub_module_node.id))
                    
                    # 创建子模块到模块的关系
                    edge = self.kg_repo.create_edge(
                        source_id=str(sub_module_node.id),
                        target_id=str(module_node.id),
                        relationship_type="part_of",
                        properties={"source_type": "sap_sub_module", "target_type": "sap_module"}
                    )
                    stored_edges.append(str(edge.id))
            
            # 3. 存储概念节点
            for module_key, concepts in organized_concepts.items():
                module, sub_module = module_key.split("/", 1)
                
                for concept_data in concepts:
                    entity = concept_data
                    concept_node = self.kg_repo.create_node(
                        label=entity.get("name", ""),
                        node_type="sap_business_concept",
                        properties={
                            "name": entity.get("name", ""),
                            "display_name": entity.get("display_name"),
                            "description": entity.get("description"),
                            "entity_id": entity.get("id"),
                            "module": module,
                            "sub_module": sub_module,
                            "metadata": entity.get("metadata", {})
                        }
                    )
                    stored_nodes.append(str(concept_node.id))
            
            # 4. 存储关系边
            for rel in relationships:
                try:
                    source_node = self.kg_repo.get_node_by_label(str(rel["source"]))
                    target_node = self.kg_repo.get_node_by_label(str(rel["target"]))
                    
                    if source_node and target_node:
                        edge = self.kg_repo.create_edge(
                            source_id=str(source_node.id),
                            target_id=str(target_node.id),
                            relationship_type=rel.get("relationship_type", "related_to"),
                            properties=rel.get("properties", {})
                        )
                        stored_edges.append(str(edge.id))
                except Exception as e:
                    logger.warning(f"Failed to store relationship edge: {e}")
                    continue
            
            self.db.commit()
            ontology_id = f"sap_ontology_{len(stored_nodes)}_{len(stored_edges)}"
            logger.info(f"Stored SAP ontology: {len(stored_nodes)} nodes, {len(stored_edges)} edges")
            return ontology_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store SAP ontology: {e}", exc_info=True)
            raise
    
    def _build_concept_hierarchy(self, entities: List[Dict]) -> List[Dict]:
        """构建概念层次结构"""
        concepts = []
        
        # 按实体类型分组
        entity_types = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "unknown")
            if isinstance(entity_type, dict):
                entity_type = entity_type.get("value", "unknown")
            elif hasattr(entity_type, 'value'):
                entity_type = entity_type.value
            
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)
        
        # 为每个实体类型创建概念节点
        for entity_type, type_entities in entity_types.items():
            # 创建类型概念
            type_concept = {
                "label": f"{entity_type}_type",
                "node_type": "concept_type",
                "properties": {
                    "name": entity_type,
                    "entity_count": len(type_entities),
                    "description": f"{entity_type}类型的概念"
                }
            }
            concepts.append(type_concept)
            
            # 为每个实体创建概念节点
            for entity in type_entities:
                concept = {
                    "label": entity.get("name", ""),
                    "node_type": "concept",
                    "properties": {
                        "name": entity.get("name", ""),
                        "display_name": entity.get("display_name"),
                        "description": entity.get("description"),
                        "entity_id": entity.get("id"),
                        "entity_type": entity_type,
                        "metadata": entity.get("metadata", {})
                    }
                }
                concepts.append(concept)
        
        return concepts
    
    def _extract_relationships(self, entities: List[Dict]) -> List[Dict]:
        """提取实体关系"""
        relationships = []
        
        for entity in entities:
            entity_id = entity.get("id")
            metadata = entity.get("metadata", {}) or entity.get("extra_metadata", {})
            
            # 从metadata中提取关系
            if isinstance(metadata, dict):
                # 检查是否有related_entities
                related_entities = entity.get("related_entities", [])
                if related_entities:
                    for related_id in related_entities:
                        relationships.append({
                            "source": entity_id,
                            "target": related_id,
                            "relationship_type": "related_to",
                            "properties": {
                                "source_type": "business_entity",
                                "target_type": "business_entity"
                            }
                        })
                
                # 检查是否有related_data_assets
                related_assets = entity.get("related_data_assets", [])
                if related_assets:
                    for asset_id in related_assets:
                        relationships.append({
                            "source": entity_id,
                            "target": asset_id,
                            "relationship_type": "uses",
                            "properties": {
                                "source_type": "business_entity",
                                "target_type": "data_asset"
                            }
                        })
        
        return relationships
    
    async def _store_ontology(self, concepts: List[Dict], relationships: List[Dict]) -> str:
        """存储本体到知识图谱"""
        try:
            stored_nodes = []
            stored_edges = []
            
            # 存储概念节点
            for concept in concepts:
                try:
                    node = self.kg_repo.create_node(
                        label=concept.get("label", ""),
                        node_type=concept.get("node_type", "concept"),
                        properties=concept.get("properties", {})
                    )
                    stored_nodes.append(str(node.id))
                except Exception as e:
                    logger.warning(f"Failed to store concept node: {e}")
                    continue
            
            # 存储关系边
            for rel in relationships:
                try:
                    # 查找源节点和目标节点
                    source_node = self.kg_repo.get_node_by_label(str(rel["source"]))
                    target_node = self.kg_repo.get_node_by_label(str(rel["target"]))
                    
                    if source_node and target_node:
                        edge = self.kg_repo.create_edge(
                            source_id=str(source_node.id),
                            target_id=str(target_node.id),
                            relationship_type=rel.get("relationship_type", "related_to"),
                            properties=rel.get("properties", {})
                        )
                        stored_edges.append(str(edge.id))
                except Exception as e:
                    logger.warning(f"Failed to store relationship edge: {e}")
                    continue
            
            self.db.commit()
            
            ontology_id = f"ontology_{len(stored_nodes)}_{len(stored_edges)}"
            logger.info(f"Stored ontology: {len(stored_nodes)} nodes, {len(stored_edges)} edges")
            
            return ontology_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store ontology: {e}", exc_info=True)
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()


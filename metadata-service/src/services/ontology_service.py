"""
本体服务
从业务实体构建业务本体（迁移自knowledge-base）
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..models.business_entity import BusinessEntity, BusinessEntitySchema
from ..services.metadata_catalog import MetadataCatalogService
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..services.relationship_discovery_service import RelationshipDiscoveryService

logger = logging.getLogger(__name__)


class OntologyService:
    """
    本体服务
    
    迁移自knowledge-base的OntologyBuilder，优化为直接使用metadata-service的数据库
    无需HTTP调用，性能更好
    """
    
    def __init__(self, db: Session, catalog: MetadataCatalogService, kg_repo: KnowledgeGraphRepository, use_llm: bool = True):
        """
        初始化本体服务
        
        Args:
            db: 数据库会话
            catalog: 元数据目录服务
            kg_repo: 知识图谱Repository
            use_llm: 是否使用LLM增强关系发现
        """
        self.db = db
        self.catalog = catalog
        self.kg_repo = kg_repo
        self.relationship_discovery = RelationshipDiscoveryService(db, use_llm=use_llm)
    
    async def clean_existing_ontology(self):
        """
        清理现有知识图谱数据（用于force_rebuild）
        """
        try:
            # 删除所有边（concept相关的边）
            all_edges = self.kg_repo.list_edges(limit=100000)
            edge_count = 0
            for edge in all_edges:
                # 只删除concept节点之间的边
                source_node = self.kg_repo.get_node_by_id(str(edge.source_node_id))
                target_node = self.kg_repo.get_node_by_id(str(edge.target_node_id))
                if source_node and target_node:
                    if (source_node.node_type == "concept" and target_node.node_type == "concept"):
                        self.kg_repo.delete_edge(str(edge.id))
                        edge_count += 1
            
            # 删除所有concept节点
            all_nodes = self.kg_repo.list_nodes(limit=100000, node_type="concept")
            node_count = 0
            for node in all_nodes:
                self.kg_repo.delete_node(str(node.id))
                node_count += 1
            
            self.db.commit()
            logger.info(f"Cleaned {node_count} concept nodes and {edge_count} edges")
        except Exception as e:
            logger.error(f"Failed to clean existing ontology: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    async def build_business_ontology(self, priority_entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        构建业务本体
        
        从metadata-service的业务实体构建业务本体，存储到知识图谱
        
        Args:
            priority_entities: 优先处理的实体列表（实体名称列表）
        
        Returns:
            本体数据
        """
        try:
            # 1. 从metadata-service获取业务实体（直接使用数据库，无需HTTP调用）
            entities = self.catalog.list_business_entities(limit=1000)
            
            # 如果指定了priority_entities，优先处理这些实体
            if priority_entities:
                logger.info(f"Priority entities specified: {priority_entities}")
                # 分离优先实体和其他实体
                priority_entity_list = []
                other_entity_list = []
                priority_names_lower = [name.lower() for name in priority_entities]
                
                for entity in entities:
                    entity_name = getattr(entity, "name", "") or getattr(entity, "display_name", "")
                    if entity_name.lower() in priority_names_lower:
                        priority_entity_list.append(entity)
                    else:
                        other_entity_list.append(entity)
                
                # 优先实体在前，其他实体在后
                entities = priority_entity_list + other_entity_list
                logger.info(f"Processing {len(priority_entity_list)} priority entities and {len(other_entity_list)} other entities")
            
            # 转换为字典格式
            entity_list = []
            for entity in entities:
                if isinstance(entity, BusinessEntitySchema):
                    entity_dict = entity.model_dump()
                elif isinstance(entity, dict):
                    entity_dict = entity
                else:
                    entity_dict = {
                        "id": getattr(entity, "id", None),
                        "name": getattr(entity, "name", ""),
                        "display_name": getattr(entity, "display_name", ""),
                        "description": getattr(entity, "description", ""),
                        "entity_type": getattr(entity, "entity_type", None),
                        "parent_id": getattr(entity, "parent_id", None),
                        "business_definition": getattr(entity, "business_definition", ""),
                        "business_rules": getattr(entity, "business_rules", {}),
                        "metadata": getattr(entity, "metadata", {}) or getattr(entity, "extra_metadata", {})
                    }
                entity_list.append(entity_dict)
            
            # 2. 构建概念层次结构
            concepts = self._build_concept_hierarchy(entity_list)
            
            # 3. 定义实体关系和属性（使用关系发现服务）
            relationships = await self._discover_relationships(entity_list)
            
            # 4. 存储到知识图谱
            ontology_id = await self._store_ontology(concepts, relationships)
            
            return {
                "success": True,
                "ontology_id": ontology_id,
                "concepts": len(concepts),
                "relationships": len(relationships),
                "concepts_detail": concepts[:10] if len(concepts) > 10 else concepts
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
            # 1. 从metadata-service获取业务实体（直接使用数据库）
            # 分批获取，避免一次性加载过多数据
            all_entities = []
            batch_size = 500
            skip = 0
            
            while True:
                entities = self.catalog.list_business_entities(skip=skip, limit=batch_size)
                if not entities:
                    break
                all_entities.extend(entities)
                skip += batch_size
                logger.info(f"Loaded {len(all_entities)} entities so far...")
                if len(entities) < batch_size:
                    break
            
            entities = all_entities
            
            # 转换为字典格式
            entity_list = []
            for entity in entities:
                if isinstance(entity, BusinessEntitySchema):
                    entity_dict = entity.model_dump()
                elif isinstance(entity, dict):
                    entity_dict = entity
                else:
                    entity_dict = {
                        "id": getattr(entity, "id", None),
                        "name": getattr(entity, "name", ""),
                        "display_name": getattr(entity, "display_name", ""),
                        "description": getattr(entity, "description", ""),
                        "entity_type": getattr(entity, "entity_type", None),
                        "parent_id": getattr(entity, "parent_id", None),
                        "metadata": getattr(entity, "metadata", {}) or getattr(entity, "extra_metadata", {})
                    }
                entity_list.append(entity_dict)
            
            # 2. 按模块组织实体
            organized_concepts = self._organize_by_module(entity_list)
            
            # 3. 构建模块层次结构
            module_hierarchy = self._build_module_hierarchy(organized_concepts)
            
            # 4. 提取关系（使用关系发现服务）- 分批处理以提高性能
            relationships = await self._discover_relationships_batch(entity_list)
            
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
    
    def _build_concept_hierarchy(self, entities: List[Dict]) -> List[Dict]:
        """
        构建概念层次结构
        
        Args:
            entities: 业务实体列表
        
        Returns:
            概念列表
        """
        concepts = []
        
        for entity in entities:
            concept = {
                "label": entity.get("name") or entity.get("display_name", ""),
                "node_type": "concept",
                "properties": {
                    "entity_id": entity.get("id"),
                    "entity_type": str(entity.get("entity_type", "")),
                    "display_name": entity.get("display_name", ""),
                    "description": entity.get("description", ""),
                    "business_definition": entity.get("business_definition", ""),
                    "business_rules": entity.get("business_rules", {}),
                    "parent_id": entity.get("parent_id"),
                    "source": "metadata-service"
                }
            }
            concepts.append(concept)
        
        return concepts
    
    async def _discover_relationships(self, entities: List[Dict]) -> List[Dict]:
        """
        发现实体关系（使用关系发现服务）
        
        Args:
            entities: 业务实体列表
        
        Returns:
            关系列表
        """
        # 使用关系发现服务（混合方案：规则引擎 + LLM增强）
        relationships = await self.relationship_discovery.discover_relationships(entities)
        
        # 转换为存储格式
        formatted_relationships = []
        for rel in relationships:
            formatted_relationships.append({
                "source": rel.get("source"),
                "target": rel.get("target"),
                "relationship_type": rel.get("relationship_type", "related_to"),
                "properties": rel.get("properties", {})
            })
        
        return formatted_relationships
    
    async def _discover_relationships_batch(self, entities: List[Dict]) -> List[Dict]:
        """
        分批发现实体关系（优化性能）
        
        Args:
            entities: 业务实体列表
        
        Returns:
            关系列表
        """
        all_relationships = []
        batch_size = 200  # 每批处理200个实体
        
        # 分批处理实体
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            logger.info(f"Discovering relationships for batch {i//batch_size + 1}/{(len(entities) + batch_size - 1)//batch_size} ({len(batch)} entities)...")
            
            # 使用关系发现服务
            batch_relationships = await self.relationship_discovery.discover_relationships(batch)
            
            # 转换为存储格式
            for rel in batch_relationships:
                all_relationships.append({
                    "source": rel.get("source"),
                    "target": rel.get("target"),
                    "relationship_type": rel.get("relationship_type", "related_to"),
                    "properties": rel.get("properties", {})
                })
            
            logger.info(f"Batch {i//batch_size + 1} discovered {len(batch_relationships)} relationships")
        
        logger.info(f"Total relationships discovered: {len(all_relationships)}")
        return all_relationships
    
    def _extract_relationships(self, entities: List[Dict]) -> List[Dict]:
        """
        提取实体关系（保留作为备用方法）
        
        Args:
            entities: 业务实体列表
        
        Returns:
            关系列表
        """
        relationships = []
        entity_map = {entity.get("id"): entity for entity in entities}
        
        for entity in entities:
            entity_id = entity.get("id")
            
            # 父子关系
            parent_id = entity.get("parent_id")
            if parent_id and parent_id in entity_map:
                relationships.append({
                    "source": str(parent_id),
                    "target": str(entity_id),
                    "relationship_type": "parent_of",
                    "properties": {
                        "source_type": "concept",
                        "target_type": "concept"
                    }
                })
            
            # 关联实体关系
            related_entities = entity.get("related_entities", [])
            if related_entities:
                for related_id in related_entities:
                    if related_id in entity_map:
                        relationships.append({
                            "source": str(entity_id),
                            "target": str(related_id),
                            "relationship_type": "related_to",
                            "properties": {
                                "source_type": "concept",
                                "target_type": "concept"
                            }
                        })
        
        return relationships
    
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
    
    async def _store_ontology(
        self,
        concepts: List[Dict],
        relationships: List[Dict]
    ) -> str:
        """存储本体到知识图谱"""
        try:
            stored_nodes = []
            stored_edges = []
            
            # 存储概念节点
            for concept in concepts:
                try:
                    # create_node方法已经处理了重复节点的情况
                    node = self.kg_repo.create_node(
                        label=concept.get("label", ""),
                        node_type=concept.get("node_type", "concept"),
                        properties=concept.get("properties", {})
                    )
                    if node:
                        stored_nodes.append(str(node.id))
                except Exception as e:
                    logger.warning(f"Failed to store concept node: {e}")
                    # 如果是因为重复，尝试获取现有节点
                    if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                        try:
                            existing_node = self.kg_repo.get_node_by_label(
                                concept.get("label", ""),
                                concept.get("node_type", "concept")
                            )
                            if existing_node:
                                stored_nodes.append(str(existing_node.id))
                        except:
                            pass
                    continue
            
            # 存储关系边
            for rel in relationships:
                try:
                    # 查找源节点和目标节点（通过entity_id）
                    source_entity_id = rel.get("source")
                    target_entity_id = rel.get("target")
                    
                    # 查找对应的知识图谱节点
                    source_node = None
                    target_node = None
                    
                    # 通过properties中的entity_id查找节点
                    all_nodes = self.kg_repo.list_nodes(limit=10000, node_type="concept")
                    for node in all_nodes:
                        node_props = node.properties or {}
                        if str(node_props.get("entity_id")) == str(source_entity_id):
                            source_node = node
                        if str(node_props.get("entity_id")) == str(target_entity_id):
                            target_node = node
                    
                    if source_node and target_node:
                        edge = self.kg_repo.create_edge(
                            source_id=str(source_node.id),
                            target_id=str(target_node.id),
                            relationship_type=rel.get("relationship_type", "related_to"),
                            properties=rel.get("properties", {})
                        )
                        if edge:
                            stored_edges.append(str(edge.id))
                except Exception as e:
                    logger.warning(f"Failed to store relationship edge: {e}")
                    continue
            
            self.db.commit()
            
            ontology_id = f"ontology_{len(stored_nodes)}_{len(stored_edges)}"
            logger.info(f"Stored ontology: {len(stored_nodes)} nodes, {len(stored_edges)} edges")
            
            return ontology_id
            
        except Exception as e:
            logger.error(f"Failed to store ontology: {e}", exc_info=True)
            self.db.rollback()
            raise
    
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
            module_nodes = {}
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
                if module_node:
                    stored_nodes.append(str(module_node.id))
                    module_nodes[module_info["module"]] = module_node
                    
                    # 2. 存储子模块节点
                    sub_module_nodes = {}
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
                        if sub_module_node:
                            stored_nodes.append(str(sub_module_node.id))
                            sub_module_nodes[sub_module_info["name"]] = sub_module_node
                            
                            # 创建子模块到模块的关系
                            edge = self.kg_repo.create_edge(
                                source_id=str(sub_module_node.id),
                                target_id=str(module_node.id),
                                relationship_type="part_of",
                                properties={"source_type": "sap_sub_module", "target_type": "sap_module"}
                            )
                            if edge:
                                stored_edges.append(str(edge.id))
            
            # 3. 存储概念节点
            concept_nodes = {}
            for module_key, concepts in organized_concepts.items():
                module, sub_module = module_key.split("/", 1)
                
                for concept_data in concepts:
                    entity = concept_data
                    # create_node方法已经处理了重复节点的情况
                    try:
                        concept_node = self.kg_repo.create_node(
                            label=entity.get("name") or entity.get("display_name", ""),
                            node_type="concept",
                            properties={
                                "entity_id": entity.get("id"),
                                "entity_type": str(entity.get("entity_type", "")),
                                "display_name": entity.get("display_name", ""),
                                "description": entity.get("description", ""),
                                "sap_module": module,
                                "sap_sub_module": sub_module,
                                "source": "metadata-service"
                            }
                        )
                        if concept_node:
                            stored_nodes.append(str(concept_node.id))
                            concept_nodes[str(entity.get("id"))] = concept_node
                    except Exception as e:
                        # 如果创建失败（可能是重复），尝试获取现有节点
                        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                            try:
                                existing_node = self.kg_repo.get_node_by_label(
                                    entity.get("name") or entity.get("display_name", ""),
                                    "concept"
                                )
                                if existing_node:
                                    concept_nodes[str(entity.get("id"))] = existing_node
                                    stored_nodes.append(str(existing_node.id))
                            except:
                                pass
                        logger.warning(f"Failed to create concept node for {entity.get('name')}: {e}")
                        continue
                        
                        # 创建概念到子模块的关系
                        if module in module_nodes:
                            # 找到对应的子模块节点
                            sub_module_node = None
                            all_nodes = self.kg_repo.list_nodes(limit=10000, node_type="sap_sub_module")
                            for node in all_nodes:
                                node_props = node.properties or {}
                                if (node_props.get("name") == sub_module and 
                                    node_props.get("parent_module") == module):
                                    sub_module_node = node
                                    break
                            
                            if sub_module_node:
                                edge = self.kg_repo.create_edge(
                                    source_id=str(concept_node.id),
                                    target_id=str(sub_module_node.id),
                                    relationship_type="belongs_to",
                                    properties={"source_type": "concept", "target_type": "sap_sub_module"}
                                )
                                if edge:
                                    stored_edges.append(str(edge.id))
            
            # 4. 存储实体关系
            logger.info(f"Storing {len(relationships)} relationships, concept_nodes has {len(concept_nodes)} entries")
            stored_count = 0
            skipped_count = 0
            
            for rel in relationships:
                try:
                    source_entity_id = str(rel.get("source"))
                    target_entity_id = str(rel.get("target"))
                    
                    # 调试：打印前几个关系的ID
                    if stored_count + skipped_count < 5:
                        logger.debug(f"Relationship: source={source_entity_id}, target={target_entity_id}, "
                                   f"source_in_dict={source_entity_id in concept_nodes}, "
                                   f"target_in_dict={target_entity_id in concept_nodes}")
                    
                    if source_entity_id in concept_nodes and target_entity_id in concept_nodes:
                        source_node = concept_nodes[source_entity_id]
                        target_node = concept_nodes[target_entity_id]
                        
                        # 验证节点ID不为None
                        if not source_node or not target_node:
                            logger.warning(f"Skipping edge: node is None. source_entity_id={source_entity_id}, target_entity_id={target_entity_id}")
                            skipped_count += 1
                            continue
                        
                        if not source_node.id or not target_node.id:
                            logger.warning(f"Skipping edge: node.id is None. source_node.id={source_node.id}, target_node.id={target_node.id}")
                            skipped_count += 1
                            continue
                        
                        # 详细日志记录
                        logger.debug(f"Creating edge: source={source_entity_id}({source_node.id}) -> target={target_entity_id}({target_node.id}), type={rel.get('relationship_type', 'related_to')}")
                        
                        edge = self.kg_repo.create_edge(
                            source_id=str(source_node.id),
                            target_id=str(target_node.id),
                            relationship_type=rel.get("relationship_type", "related_to"),
                            properties=rel.get("properties", {})
                        )
                        if edge:
                            stored_edges.append(str(edge.id))
                            stored_count += 1
                            logger.debug(f"Successfully created edge: {edge.id}")
                        else:
                            logger.warning(f"Failed to create edge for {source_entity_id} -> {target_entity_id}")
                            skipped_count += 1
                    else:
                        skipped_count += 1
                        if skipped_count <= 5:  # 只打印前5个跳过的
                            logger.debug(f"Skipped relationship: source={source_entity_id} (in dict: {source_entity_id in concept_nodes}), "
                                       f"target={target_entity_id} (in dict: {target_entity_id in concept_nodes})")
                except Exception as e:
                    logger.warning(f"Failed to store entity relationship: {e}", exc_info=True)
                    skipped_count += 1
                    continue
            
            logger.info(f"Stored {stored_count} relationships, skipped {skipped_count}")
            
            self.db.commit()
            
            ontology_id = f"sap_ontology_{len(stored_nodes)}_{len(stored_edges)}"
            logger.info(f"Stored SAP ontology: {len(stored_nodes)} nodes, {len(stored_edges)} edges")
            
            return ontology_id
            
        except Exception as e:
            logger.error(f"Failed to store SAP ontology: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    async def get_concepts(
        self,
        skip: int = 0,
        limit: int = 100,
        node_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取概念列表
        
        Args:
            skip: 跳过数量
            limit: 返回数量限制
            node_type: 节点类型过滤（可选）
        
        Returns:
            概念列表
        """
        try:
            nodes = self.kg_repo.list_nodes(
                skip=skip,
                limit=limit,
                node_type=node_type or "concept"
            )
            
            return [
                {
                    "id": str(node.id),
                    "label": node.label,
                    "node_type": node.node_type,
                    "properties": node.properties or {}
                }
                for node in nodes
            ]
        except Exception as e:
            logger.error(f"Failed to get concepts: {e}", exc_info=True)
            raise


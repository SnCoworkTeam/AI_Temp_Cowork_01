"""
业务实体建模器
从sap-metadata-agent获取数据资产，自动识别业务实体并构建关系图谱
"""
import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.business_entity import BusinessEntity, BusinessEntitySchema, BusinessEntityCreate, EntityType
from ..services.metadata_catalog import MetadataCatalogService
from ..services.data_lineage import DataLineageService

logger = logging.getLogger(__name__)


class BusinessEntityModeler:
    """业务实体建模器"""
    
    def __init__(self, db: Session, metadata_catalog: MetadataCatalogService, lineage_service: DataLineageService):
        self.db = db
        self.catalog = metadata_catalog
        self.lineage_service = lineage_service
        self.sap_agent_url = os.getenv("SAP_METADATA_AGENT_URL", "http://sap-metadata-agent:8015")
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def identify_entities_from_sap(self) -> List[BusinessEntitySchema]:
        """
        从sap-metadata-agent获取数据资产，自动识别业务实体
        
        Returns:
            识别的业务实体列表
        """
        try:
            # 1. 从sap-metadata-agent获取数据资产
            response = await self.http_client.get(f"{self.sap_agent_url}/api/sap-metadata/assets")
            response.raise_for_status()
            sap_response = response.json()
            
            # 使用正确的字段名
            sap_assets = sap_response.get("assets", [])
            
            # 2. 基于命名模式识别实体
            entity_patterns = {
                "KNA1": "客户",
                "LFA1": "供应商",
                "MARA": "物料",
                "BKPF": "会计凭证",
                "VBAK": "销售订单",
                "VBAP": "销售订单行项目",
                "VBUK": "销售订单状态",
                "VBKD": "销售订单业务数据",
                "KONV": "条件",
                "T001": "公司代码",
                "T001W": "工厂",
                "T024": "采购组织",
                "T024E": "采购组",
                "EKPO": "采购订单行项目",
                "EKBE": "采购订单历史",
                "MSEG": "物料凭证",
                "MKPF": "物料凭证抬头",
                "MBEW": "物料评估",
                "MARD": "物料仓储位置",
            }
            
            identified_entities = []
            for asset in sap_assets:
                # 使用正确的字段名
                table_name = asset.get("sap_table_name", "").upper()
                if not table_name:
                    # 如果没有sap_table_name，尝试从name中提取
                    table_name = asset.get("name", "").upper()
                
                if table_name in entity_patterns:
                    entity_name = entity_patterns[table_name]
                    
                    # 使用list_business_entities搜索，而不是不存在的get_business_entity_by_name
                    existing_entities = self.catalog.list_business_entities(search=entity_name, limit=10)
                    existing = None
                    for e in existing_entities:
                        if e.name == entity_name:
                            existing = e
                            break
                    
                    if not existing:
                        # 创建业务实体
                        entity_data = BusinessEntityCreate(
                            name=entity_name,
                            display_name=f"{entity_name}实体",
                            description=f"从SAP表{table_name}识别的{entity_name}实体",
                            entity_type=EntityType.CONCEPT,  # 使用枚举值
                            metadata={
                                "table_name": table_name,
                                "asset_id": asset.get("id"),
                                "source_system": "SAP",
                                "sap_module": asset.get("sap_module"),
                                "asset_type": asset.get("asset_type")
                            }
                        )
                        entity = self.catalog.create_business_entity(entity_data)
                        identified_entities.append(entity)
                        logger.info(f"Created business entity: {entity_name} from SAP table {table_name}")
            
            logger.info(f"Identified {len(identified_entities)} business entities from SAP")
            return identified_entities
            
        except Exception as e:
            logger.error(f"Failed to identify entities from SAP: {e}", exc_info=True)
            raise
    
    async def build_entity_relationship_graph(self, entity_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        构建实体关系图谱
        
        Args:
            entity_ids: 实体ID列表（可选，不提供则构建所有实体）
        
        Returns:
            关系图谱数据
        """
        try:
            # 1. 获取实体列表
            if entity_ids:
                entities = [self.catalog.get_business_entity(eid) for eid in entity_ids]
                entities = [e for e in entities if e]
            else:
                entities = self.catalog.list_business_entities(limit=1000)
            
            # 2. 获取实体间的血缘关系
            relationships = []
            for entity in entities:
                # 从metadata中获取asset_id
                metadata = entity.metadata or {}
                asset_id = metadata.get("asset_id")
                
                if asset_id:
                    # 血缘服务是同步方法，不需要await
                    # 返回LineageGraph对象，需要提取edges
                    upstream_graph = self.lineage_service.get_upstream_lineage("data_asset", str(asset_id))
                    downstream_graph = self.lineage_service.get_downstream_lineage("data_asset", str(asset_id))
                    
                    # 合并所有边
                    all_edges = upstream_graph.edges + downstream_graph.edges
                    
                    # 构建关系
                    for edge in all_edges:
                        # 解析节点ID: "type:id"
                        try:
                            source_type, source_id_str = edge.source.split(":", 1)
                            target_type, target_id_str = edge.target.split(":", 1)
                            
                            # 查找目标实体ID（如果存在）
                            target_entity = None
                            if target_type == "data_asset":
                                # 尝试查找对应的业务实体
                                target_entities = self.catalog.list_business_entities(limit=1000)
                                for te in target_entities:
                                    te_metadata = te.metadata or {}
                                    if str(te_metadata.get("asset_id")) == target_id_str:
                                        target_entity = te
                                        break
                            
                            relationships.append({
                                "source_entity_id": entity.id,
                                "target_entity_id": target_entity.id if target_entity else None,
                                "target_asset_id": target_id_str,
                                "relationship_type": edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type),
                                "lineage_type": edge.lineage_type.value if hasattr(edge.lineage_type, 'value') else str(edge.lineage_type),
                                "transformation_logic": edge.transformation_logic,
                                "metadata": edge.metadata or {}
                            })
                        except ValueError:
                            logger.warning(f"Failed to parse lineage edge: {edge.source} -> {edge.target}")
                            continue
            
            # 3. 构建图谱结构
            graph = {
                "nodes": [
                    {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type),
                        "display_name": entity.display_name,
                        "metadata": entity.metadata
                    }
                    for entity in entities
                ],
                "edges": relationships,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Built relationship graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
            return graph
            
        except Exception as e:
            logger.error(f"Failed to build entity relationship graph: {e}", exc_info=True)
            raise
    
    async def calculate_entity_similarity(self, entity_id1: int, entity_id2: int) -> float:
        """
        计算实体相似度
        
        Args:
            entity_id1: 实体1 ID
            entity_id2: 实体2 ID
        
        Returns:
            相似度分数 (0-1)
        """
        try:
            entity1 = self.catalog.get_business_entity(entity_id1)
            entity2 = self.catalog.get_business_entity(entity_id2)
            
            if not entity1 or not entity2:
                return 0.0
            
            # 基于名称、类型、元数据的相似度计算
            similarity_score = 0.0
            
            # 名称相似度
            if entity1.name == entity2.name:
                similarity_score += 0.3
            
            # 类型相似度
            entity_type1 = entity1.entity_type.value if hasattr(entity1.entity_type, 'value') else str(entity1.entity_type)
            entity_type2 = entity2.entity_type.value if hasattr(entity2.entity_type, 'value') else str(entity2.entity_type)
            if entity_type1 == entity_type2:
                similarity_score += 0.2
            
            # 元数据相似度
            metadata1 = entity1.metadata or {}
            metadata2 = entity2.metadata or {}
            if metadata1 and metadata2:
                common_keys = set(metadata1.keys()) & set(metadata2.keys())
                if common_keys:
                    similarity_score += 0.5 * (len(common_keys) / max(len(metadata1), len(metadata2), 1))
            
            return min(similarity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate entity similarity: {e}", exc_info=True)
            return 0.0
    
    async def build_sap_entity_relationships(
        self,
        entity_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        基于SAP NavigationProperty构建实体关系
        
        Args:
            entity_ids: 实体ID列表（可选，不提供则处理所有SAP实体）
        
        Returns:
            关系构建结果
        """
        try:
            # 1. 获取SAP实体列表
            if entity_ids:
                entities = [self.catalog.get_business_entity(eid) for eid in entity_ids]
                entities = [e for e in entities if e]
            else:
                # 获取所有SAP实体
                all_entities = self.catalog.list_business_entities(limit=10000)
                entities = [
                    e for e in all_entities
                    if e.metadata and e.metadata.get("source_system") == "SAP"
                ]
            
            logger.info(f"Building SAP relationships for {len(entities)} entities")
            
            # 2. 构建实体名称映射
            entity_name_map = {e.name: e for e in entities}
            
            # 3. 从navigation_properties构建关系
            relationships = []
            for entity in entities:
                metadata = entity.metadata or {}
                nav_props = metadata.get("navigation_properties", [])
                
                if not nav_props:
                    continue
                
                for nav_prop in nav_props:
                    nav_name = nav_prop.get("name", "")
                    nav_type = nav_prop.get("type", "")
                    
                    # 从类型中提取目标实体名称
                    # 格式: Collection(Namespace.EntityType) 或 Namespace.EntityType
                    target_entity_name = self._extract_entity_name_from_type(nav_type)
                    
                    if target_entity_name and target_entity_name in entity_name_map:
                        target_entity = entity_name_map[target_entity_name]
                        
                        # 推断关系类型
                        relationship_type = self._infer_relationship_type(nav_name, nav_type)
                        
                        relationships.append({
                            "source_entity_id": entity.id,
                            "target_entity_id": target_entity.id,
                            "relationship_type": relationship_type,
                            "navigation_property": nav_name,
                            "cardinality": "one_to_many" if "Collection" in nav_type else "many_to_one",
                            "metadata": {
                                "nav_prop_name": nav_name,
                                "nav_prop_type": nav_type,
                                "source": "sap_navigation_property"
                            }
                        })
            
            # 4. 更新实体的related_entities字段
            updated_count = 0
            for rel in relationships:
                source_entity = self.catalog.get_business_entity(rel["source_entity_id"])
                if source_entity:
                    related_entities = source_entity.related_entities or []
                    if rel["target_entity_id"] not in related_entities:
                        related_entities.append(rel["target_entity_id"])
                        
                        # 更新实体
                        from ..models.business_entity import BusinessEntityUpdate
                        update_data = BusinessEntityUpdate(related_entities=related_entities)
                        self.catalog.update_business_entity(rel["source_entity_id"], update_data)
                        updated_count += 1
            
            logger.info(
                f"Built {len(relationships)} SAP relationships, "
                f"updated {updated_count} entities"
            )
            
            return {
                "success": True,
                "relationships_count": len(relationships),
                "entities_updated": updated_count,
                "relationships": relationships[:100]  # 只返回前100个，避免响应过大
            }
            
        except Exception as e:
            logger.error(f"Failed to build SAP entity relationships: {e}", exc_info=True)
            raise
    
    def _extract_entity_name_from_type(self, nav_type: str) -> Optional[str]:
        """从NavigationProperty类型中提取实体名称"""
        if not nav_type:
            return None
        
        # 处理Collection类型: Collection(Namespace.EntityType) -> EntityType
        if nav_type.startswith("Collection("):
            nav_type = nav_type[11:-1]  # 去掉Collection(和)
        
        # 提取简单名称（去掉命名空间）
        # 格式: Namespace.EntityType 或 EntityType
        if "." in nav_type:
            simple_name = nav_type.split(".")[-1]
        else:
            simple_name = nav_type
        
        # 去掉Type后缀（如果有）
        if simple_name.endswith("Type"):
            simple_name = simple_name[:-4]
        
        return simple_name
    
    def _infer_relationship_type(self, nav_name: str, nav_type: str) -> str:
        """推断关系类型"""
        nav_name_lower = nav_name.lower()
        
        # 基于命名模式推断
        if nav_name_lower.startswith("to_"):
            return "belongs_to"
        elif "Collection" in nav_type:
            return "has_many"
        elif "parent" in nav_name_lower or "parent" in nav_name_lower:
            return "parent_of"
        elif "child" in nav_name_lower or "children" in nav_name_lower:
            return "child_of"
        else:
            return "related_to"
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()


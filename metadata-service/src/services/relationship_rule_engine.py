"""
关系发现规则引擎
基于规则快速识别明确的关系模式
"""
import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RelationshipRuleEngine:
    """关系发现规则引擎"""
    
    def __init__(self, db: Session):
        """
        初始化规则引擎
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载关系发现规则"""
        return [
            {
                "name": "parent_child_naming",
                "pattern": r"(.+)_主数据|(.+)_明细|(.+)_抬头|(.+)_行项目",
                "relationship": "parent_of",
                "confidence": 0.9,
                "description": "基于命名规则的父子关系（如：客户_主数据 -> 客户）"
            },
            {
                "name": "sap_module_hierarchy",
                "pattern": r"SAP_(.+)_Module",
                "relationship": "part_of",
                "confidence": 0.95,
                "description": "SAP模块层次结构"
            },
            {
                "name": "same_module_same_submodule",
                "relationship": "related_to",
                "confidence": 0.8,
                "description": "同模块同子模块的实体相关"
            },
            {
                "name": "parent_id_hierarchy",
                "relationship": "parent_of",
                "confidence": 1.0,
                "description": "基于parent_id的层次关系"
            },
            {
                "name": "related_entities_list",
                "relationship": "related_to",
                "confidence": 0.85,
                "description": "基于related_entities列表的关联关系"
            }
        ]
    
    def discover_relationships(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        基于规则发现实体关系
        
        Args:
            entities: 实体列表
        
        Returns:
            关系列表
        """
        relationships = []
        entity_map = {entity.get("id"): entity for entity in entities}
        
        for entity in entities:
            entity_id = entity.get("id")
            
            # 规则1: parent_id层次关系
            parent_id = entity.get("parent_id")
            if parent_id and parent_id in entity_map:
                relationships.append({
                    "source": str(parent_id),
                    "target": str(entity_id),
                    "relationship_type": "parent_of",
                    "confidence": 1.0,
                    "rule": "parent_id_hierarchy",
                    "properties": {
                        "source_type": "concept",
                        "target_type": "concept"
                    }
                })
            
            # 规则2: related_entities关联关系
            related_entities = entity.get("related_entities", [])
            if related_entities:
                for related_id in related_entities:
                    if related_id in entity_map:
                        relationships.append({
                            "source": str(entity_id),
                            "target": str(related_id),
                            "relationship_type": "related_to",
                            "confidence": 0.85,
                            "rule": "related_entities_list",
                            "properties": {
                                "source_type": "concept",
                                "target_type": "concept"
                            }
                        })
            
            # 规则3: 命名规则匹配（父子关系）
            name = entity.get("name", "")
            parent_match = self._match_parent_child_naming(name, entities)
            if parent_match:
                relationships.append({
                    "source": str(parent_match["parent_id"]),
                    "target": str(entity_id),
                    "relationship_type": "parent_of",
                    "confidence": 0.9,
                    "rule": "parent_child_naming",
                    "properties": {
                        "source_type": "concept",
                        "target_type": "concept"
                    }
                })
            
            # 规则4: 同模块同子模块关系
            same_module_relations = self._find_same_module_relations(entity, entities)
            relationships.extend(same_module_relations)
        
        # 去重
        unique_relationships = self._deduplicate_relationships(relationships)
        
        logger.info(f"Rule engine discovered {len(unique_relationships)} relationships")
        return unique_relationships
    
    def _match_parent_child_naming(
        self,
        name: str,
        entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """匹配父子命名规则"""
        pattern = r"(.+)_(主数据|明细|抬头|行项目)"
        match = re.match(pattern, name)
        
        if match:
            parent_name = match.group(1)
            # 查找父实体
            for entity in entities:
                if entity.get("name") == parent_name:
                    return {
                        "parent_id": entity.get("id"),
                        "parent_name": parent_name
                    }
        
        return None
    
    def _find_same_module_relations(
        self,
        entity: Dict[str, Any],
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """查找同模块同子模块的关系"""
        relationships = []
        entity_id = entity.get("id")
        
        # 尝试多种方式获取模块信息
        metadata = entity.get("metadata", {}) or entity.get("extra_metadata", {})
        module = metadata.get("sap_module")
        sub_module = metadata.get("sap_sub_module")
        
        # 如果metadata中没有，尝试从description或business_definition中提取
        if not module:
            description = entity.get("description", "") or entity.get("business_definition", "")
            if "MM" in description or "物料" in description or "采购" in description:
                module = "MM"
            elif "SD" in description or "销售" in description:
                module = "SD"
            elif "FI" in description or "财务" in description:
                module = "FI"
        
        if not module:
            return relationships
        
        if not sub_module:
            sub_module = "General"
        
        # 查找同模块同子模块的其他实体（限制数量，避免过多关系）
        count = 0
        max_relations = 5  # 每个实体最多5个同模块关系
        
        for other_entity in entities:
            if count >= max_relations:
                break
                
            other_id = other_entity.get("id")
            if other_id == entity_id:
                continue
            
            # 尝试多种方式获取其他实体的模块信息
            other_metadata = other_entity.get("metadata", {}) or other_entity.get("extra_metadata", {})
            other_module = other_metadata.get("sap_module")
            other_sub_module = other_metadata.get("sap_sub_module")
            
            if not other_module:
                other_description = other_entity.get("description", "") or other_entity.get("business_definition", "")
                if "MM" in other_description or "物料" in other_description or "采购" in other_description:
                    other_module = "MM"
                elif "SD" in other_description or "销售" in other_description:
                    other_module = "SD"
                elif "FI" in other_description or "财务" in other_description:
                    other_module = "FI"
            
            if not other_module:
                other_module = "OTHER"
            
            if not other_sub_module:
                other_sub_module = "General"
            
            # 同模块的实体建立关系
            if module == other_module:
                relationships.append({
                    "source": str(entity_id),
                    "target": str(other_id),
                    "relationship_type": "related_to",
                    "confidence": 0.7 if sub_module == other_sub_module else 0.6,
                    "rule": "same_module_same_submodule" if sub_module == other_sub_module else "same_module",
                    "properties": {
                        "source_type": "concept",
                        "target_type": "concept",
                        "module": module,
                        "sub_module": sub_module,
                        "target_sub_module": other_sub_module
                    }
                })
                count += 1
        
        return relationships
    
    def _deduplicate_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重关系"""
        seen = set()
        unique = []
        
        for rel in relationships:
            key = (rel["source"], rel["target"], rel["relationship_type"])
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        return unique




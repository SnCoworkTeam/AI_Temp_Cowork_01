"""
关系发现服务
整合规则引擎和LLM增强，提供统一的关系发现接口
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .relationship_rule_engine import RelationshipRuleEngine
from .relationship_llm_discovery import RelationshipLLMDiscovery

logger = logging.getLogger(__name__)


class RelationshipDiscoveryService:
    """关系发现服务"""
    
    def __init__(self, db: Session, use_llm: bool = True):
        """
        初始化关系发现服务
        
        Args:
            db: 数据库会话
            use_llm: 是否使用LLM增强
        """
        self.db = db
        self.rule_engine = RelationshipRuleEngine(db)
        self.llm_discovery = RelationshipLLMDiscovery(db) if use_llm else None
        self.use_llm = use_llm and self.llm_discovery is not None
    
    async def discover_relationships(
        self,
        entities: List[Dict[str, Any]],
        use_llm: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        发现实体之间的关系
        
        采用混合方案：
        1. 第一层：规则引擎（快速、准确）
        2. 第二层：LLM增强（灵活、智能）
        
        Args:
            entities: 实体列表
            use_llm: 是否使用LLM（覆盖初始化设置）
        
        Returns:
            关系列表
        """
        relationships = []
        
        # 第一层：规则引擎
        logger.info("Starting rule-based relationship discovery...")
        rule_relationships = self.rule_engine.discover_relationships(entities)
        relationships.extend(rule_relationships)
        logger.info(f"Rule engine discovered {len(rule_relationships)} relationships")
        
        # 第二层：LLM增强（如果需要）
        should_use_llm = use_llm if use_llm is not None else self.use_llm
        if should_use_llm and self.llm_discovery:
            logger.info("Starting LLM-enhanced relationship discovery...")
            
            # 获取规则未识别的实体对
            unprocessed_pairs = self._get_unprocessed_pairs(entities, rule_relationships)
            
            if unprocessed_pairs:
                logger.info(f"Processing {len(unprocessed_pairs)} entity pairs with LLM...")
                llm_relationships = await self.llm_discovery.discover_relationships_batch(
                    unprocessed_pairs,
                    batch_size=10
                )
                relationships.extend(llm_relationships)
                logger.info(f"LLM discovered {len(llm_relationships)} additional relationships")
        
        # 验证和过滤
        validated_relationships = self._validate_relationships(relationships)
        
        logger.info(f"Total discovered relationships: {len(validated_relationships)}")
        return validated_relationships
    
    def _get_unprocessed_pairs(
        self,
        entities: List[Dict[str, Any]],
        rule_relationships: List[Dict[str, Any]]
    ) -> List[tuple]:
        """
        获取规则未识别的实体对
        
        Args:
            entities: 实体列表
            rule_relationships: 规则发现的关系
        
        Returns:
            未处理的实体对列表
        """
        # 构建已识别关系的集合
        processed_pairs = set()
        for rel in rule_relationships:
            source = rel.get("source")
            target = rel.get("target")
            if source and target:
                processed_pairs.add((source, target))
                processed_pairs.add((target, source))  # 双向
        
        # 找出未处理的实体对
        unprocessed_pairs = []
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], start=i+1):
                entity1_id = str(entity1.get("id"))
                entity2_id = str(entity2.get("id"))
                
                if (entity1_id, entity2_id) not in processed_pairs:
                    # 只处理有描述或业务定义的实体对（LLM需要上下文）
                    if (entity1.get("description") or entity1.get("business_definition")) and \
                       (entity2.get("description") or entity2.get("business_definition")):
                        unprocessed_pairs.append((entity1, entity2))
        
        return unprocessed_pairs
    
    def _validate_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        验证和过滤关系
        
        Args:
            relationships: 关系列表
        
        Returns:
            验证后的关系列表
        """
        validated = []
        
        for rel in relationships:
            # 基本验证
            if not rel.get("source") or not rel.get("target"):
                continue
            
            if rel.get("source") == rel.get("target"):
                continue  # 跳过自引用
            
            # 置信度过滤
            confidence = rel.get("confidence", 0.0)
            if confidence < 0.5:
                continue  # 跳过低置信度关系
            
            validated.append(rel)
        
        return validated
    
    async def close(self):
        """关闭资源"""
        if self.llm_discovery:
            await self.llm_discovery.close()







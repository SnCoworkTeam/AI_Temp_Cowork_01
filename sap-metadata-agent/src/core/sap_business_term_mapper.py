"""
SAP业务术语映射器
建立业务术语到技术资产的映射关系，支持语义搜索和意图识别
"""
import logging
from typing import List, Dict, Any, Optional
from ..models.sap_metadata_models import SAPDataAsset, SAPBusinessEntity

logger = logging.getLogger(__name__)


class SAPBusinessTermMapper:
    """SAP业务术语映射器"""
    
    def __init__(self):
        """初始化业务术语映射器"""
        self.term_patterns = self._init_term_patterns()
    
    def _init_term_patterns(self) -> Dict[str, Dict[str, Any]]:
        """初始化业务术语模式"""
        return {
            # 客户相关术语
            "customer": {
                "terms": ["客户", "Customer", "Kunde", "客户主数据", "客户信息"],
                "technical_assets": ["KNA1", "KNB1", "KNVV", "KNVP"],
                "entity_types": ["customer"],
                "search_keywords": ["customer", "client", "kunde", "客户", "客户主数据"]
            },
            # 供应商相关术语
            "vendor": {
                "terms": ["供应商", "Vendor", "Lieferant", "供应商主数据", "供应商信息"],
                "technical_assets": ["LFA1", "LFB1", "LFM1", "LFM2"],
                "entity_types": ["vendor", "supplier"],
                "search_keywords": ["vendor", "supplier", "lieferant", "供应商", "供应商主数据"]
            },
            # 物料相关术语
            "material": {
                "terms": ["物料", "Material", "Material", "物料主数据", "物料信息"],
                "technical_assets": ["MARA", "MARC", "MARD", "MVKE"],
                "entity_types": ["material", "product"],
                "search_keywords": ["material", "product", "物料", "物料主数据", "产品"]
            },
            # 销售订单相关术语
            "sales_order": {
                "terms": ["销售订单", "Sales Order", "Verkaufsauftrag", "订单"],
                "technical_assets": ["VBAK", "VBAP"],
                "entity_types": ["sales_order", "order"],
                "search_keywords": ["sales order", "verkaufsauftrag", "销售订单", "订单", "SO"]
            },
            # 采购订单相关术语
            "purchase_order": {
                "terms": ["采购订单", "Purchase Order", "Einkaufsauftrag", "采购单"],
                "technical_assets": ["EKKO", "EKPO"],
                "entity_types": ["purchase_order", "PO"],
                "search_keywords": ["purchase order", "einkaufsauftrag", "采购订单", "采购单", "PO"]
            },
            # 交货单相关术语
            "delivery": {
                "terms": ["交货单", "Delivery", "Lieferung", "发货单"],
                "technical_assets": ["LIKP", "LIPS"],
                "entity_types": ["delivery"],
                "search_keywords": ["delivery", "lieferung", "交货单", "发货单", "交货"]
            },
            # 发票相关术语
            "invoice": {
                "terms": ["发票", "Invoice", "Rechnung", "账单"],
                "technical_assets": ["VBRK", "VBRP"],
                "entity_types": ["invoice", "billing"],
                "search_keywords": ["invoice", "rechnung", "发票", "账单", "开票"]
            }
        }
    
    def create_term_mapping(
        self,
        business_term: str,
        technical_assets: List[str],
        semantic_relationships: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        创建业务术语映射
        
        Args:
            business_term: 业务术语
            technical_assets: 关联的技术资产列表
            semantic_relationships: 语义关系列表
            
        Returns:
            业务术语映射字典
        """
        # 查找匹配的模式
        matched_pattern = None
        for pattern_key, pattern in self.term_patterns.items():
            if business_term.lower() in [t.lower() for t in pattern["terms"]]:
                matched_pattern = pattern
                break
        
        mapping = {
            "business_term": business_term,
            "technical_assets": technical_assets,
            "semantic_relationships": semantic_relationships or [],
            "search_keywords": [business_term.lower()],
            "entity_types": [],
            "pattern_key": None
        }
        
        if matched_pattern:
            mapping["search_keywords"].extend(matched_pattern.get("search_keywords", []))
            mapping["entity_types"] = matched_pattern.get("entity_types", [])
            mapping["pattern_key"] = matched_pattern.get("pattern_key")
            # 合并技术资产
            mapping["technical_assets"] = list(set(
                technical_assets + matched_pattern.get("technical_assets", [])
            ))
        
        return mapping
    
    def extract_business_terms_from_asset(
        self,
        asset: SAPDataAsset
    ) -> List[Dict[str, Any]]:
        """
        从数据资产中提取业务术语
        
        Args:
            asset: SAP数据资产
            
        Returns:
            业务术语映射列表
        """
        terms = []
        
        # 从表名提取
        if asset.sap_table_name:
            table_term = self._extract_term_from_table_name(asset.sap_table_name)
            if table_term:
                terms.append(self.create_term_mapping(
                    business_term=table_term,
                    technical_assets=[asset.sap_table_name]
                ))
        
        # 从描述提取
        if asset.description:
            desc_terms = self._extract_terms_from_description(asset.description)
            for term in desc_terms:
                terms.append(self.create_term_mapping(
                    business_term=term,
                    technical_assets=[asset.sap_table_name] if asset.sap_table_name else []
                ))
        
        # 从ABAP字典字段描述提取
        if asset.schema_info and asset.schema_info.get('fields'):
            for field in asset.schema_info['fields']:
                if field.get('field_description'):
                    field_term = self._extract_term_from_field_description(
                        field['field_description']
                    )
                    if field_term:
                        terms.append(self.create_term_mapping(
                            business_term=field_term,
                            technical_assets=[asset.sap_table_name] if asset.sap_table_name else []
                        ))
        
        return terms
    
    def _extract_term_from_table_name(self, table_name: str) -> Optional[str]:
        """从表名提取业务术语"""
        # 使用预定义模式匹配
        for pattern_key, pattern in self.term_patterns.items():
            for asset in pattern.get("technical_assets", []):
                if asset == table_name:
                    return pattern["terms"][0]  # 返回第一个术语
        return None
    
    def _extract_terms_from_description(self, description: str) -> List[str]:
        """从描述中提取业务术语"""
        terms = []
        desc_lower = description.lower()
        
        for pattern_key, pattern in self.term_patterns.items():
            for term in pattern["terms"]:
                if term.lower() in desc_lower:
                    terms.append(term)
        
        return terms
    
    def _extract_term_from_field_description(self, field_description: str) -> Optional[str]:
        """从字段描述中提取业务术语"""
        # 简单的关键词匹配
        field_lower = field_description.lower()
        
        for pattern_key, pattern in self.term_patterns.items():
            for keyword in pattern.get("search_keywords", []):
                if keyword.lower() in field_lower:
                    return pattern["terms"][0]
        
        return None
    
    def build_semantic_relationships(
        self,
        assets: List[SAPDataAsset],
        entities: List[SAPBusinessEntity]
    ) -> List[Dict[str, Any]]:
        """
        构建语义关系
        
        Args:
            assets: 数据资产列表
            entities: 业务实体列表
            
        Returns:
            语义关系列表
        """
        relationships = []
        
        # 资产到实体的关系
        for asset in assets:
            asset_terms = self.extract_business_terms_from_asset(asset)
            for term_mapping in asset_terms:
                # 查找匹配的业务实体
                for entity in entities:
                    if entity.entity_type in term_mapping.get("entity_types", []):
                        relationships.append({
                            "source": f"asset:{asset.name}",
                            "target": f"entity:{entity.name}",
                            "relationship_type": "represents",
                            "confidence": 0.8
                        })
        
        # 实体之间的关系
        entity_dict = {e.name: e for e in entities}
        for entity in entities:
            if entity.related_entities:
                for related_name in entity.related_entities:
                    if related_name in entity_dict:
                        relationships.append({
                            "source": f"entity:{entity.name}",
                            "target": f"entity:{related_name}",
                            "relationship_type": "related_to",
                            "confidence": 0.7
                        })
        
        return relationships



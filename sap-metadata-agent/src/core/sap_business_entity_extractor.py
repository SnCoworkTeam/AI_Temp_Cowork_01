"""
SAP业务实体提取器
从SAP数据资产中提取业务实体（客户、供应商、物料等）
"""
import logging
from typing import List, Dict, Any, Optional
import re

from ..models.sap_metadata_models import (
    SAPBusinessEntity,
    SAPBusinessDomain
)
from .sap_data_asset_discoverer import SAPDataAssetDiscoverer

logger = logging.getLogger(__name__)


class SAPBusinessEntityExtractor:
    """SAP业务实体提取器"""
    
    def __init__(self, asset_discoverer: SAPDataAssetDiscoverer):
        """
        初始化业务实体提取器
        
        Args:
            asset_discoverer: 数据资产发现器
        """
        self.asset_discoverer = asset_discoverer
        self.entity_patterns = self._init_entity_patterns()
    
    def _init_entity_patterns(self) -> Dict[str, Dict[str, Any]]:
        """初始化实体识别模式"""
        return {
            "customer": {
                "tables": ["KNA1", "KNB1", "KNVV", "KNVP"],
                "key_fields": ["KUNNR"],
                "description": "客户",
                "domain": SAPBusinessDomain.SALES
            },
            "vendor": {
                "tables": ["LFA1", "LFB1", "LFM1", "LFM2"],
                "key_fields": ["LIFNR"],
                "description": "供应商",
                "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT
            },
            "material": {
                "tables": ["MARA", "MARC", "MARD", "MVKE"],
                "key_fields": ["MATNR"],
                "description": "物料",
                "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT
            },
            "product": {
                "tables": ["MVKE", "MARA"],
                "key_fields": ["MATNR"],
                "description": "产品",
                "domain": SAPBusinessDomain.SALES
            },
            "employee": {
                "tables": ["PA0001", "PA0002", "PA0003"],
                "key_fields": ["PERNR"],
                "description": "员工",
                "domain": SAPBusinessDomain.HUMAN_RESOURCES
            },
            "company_code": {
                "tables": ["T001"],
                "key_fields": ["BUKRS"],
                "description": "公司代码",
                "domain": SAPBusinessDomain.FINANCE
            },
            "plant": {
                "tables": ["T001W"],
                "key_fields": ["WERKS"],
                "description": "工厂",
                "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT
            },
            "sales_organization": {
                "tables": ["TVKO"],
                "key_fields": ["VKORG"],
                "description": "销售组织",
                "domain": SAPBusinessDomain.SALES
            },
        }
    
    async def extract_entities(
        self,
        assets: List[Dict[str, Any]]
    ) -> List[SAPBusinessEntity]:
        """
        从数据资产中提取业务实体
        
        Args:
            assets: 数据资产列表
            
        Returns:
            业务实体列表
        """
        entities = []
        processed_tables = set()
        
        for asset in assets:
            table_name = asset.get('sap_table_name')
            if not table_name or table_name in processed_tables:
                continue
            
            # 识别实体类型
            entity_type = self._identify_entity_type(table_name, asset)
            if not entity_type:
                continue
            
            # 提取实体信息
            entity = await self._extract_entity_info(asset, entity_type)
            if entity:
                entities.append(entity)
                processed_tables.add(table_name)
        
        logger.info(f"Extracted {len(entities)} business entities")
        return entities
    
    def _identify_entity_type(
        self,
        table_name: str,
        asset: Dict[str, Any]
    ) -> Optional[str]:
        """
        识别实体类型
        
        Args:
            table_name: 表名
            asset: 资产信息
            
        Returns:
            实体类型，如果无法识别返回None
        """
        table_upper = table_name.upper()
        
        # 使用模式匹配
        for entity_type, pattern in self.entity_patterns.items():
            if table_upper in pattern['tables']:
                return entity_type
        
        # 基于表名推断
        if table_upper.startswith('KNA') or table_upper.startswith('KN'):
            return "customer"
        elif table_upper.startswith('LFA') or table_upper.startswith('LF'):
            return "vendor"
        elif table_upper.startswith('MAR') or table_upper.startswith('M'):
            if 'sales' in asset.get('description', '').lower():
                return "product"
            return "material"
        elif table_upper.startswith('PA'):
            return "employee"
        elif table_upper.startswith('T001'):
            return "company_code"
        elif table_upper.startswith('T001W'):
            return "plant"
        
        return None
    
    async def _extract_entity_info(
        self,
        asset: Dict[str, Any],
        entity_type: str
    ) -> Optional[SAPBusinessEntity]:
        """
        提取实体详细信息
        
        Args:
            asset: 资产信息
            entity_type: 实体类型
            
        Returns:
            业务实体，如果提取失败返回None
        """
        pattern = self.entity_patterns.get(entity_type)
        if not pattern:
            return None
        
        table_name = asset.get('sap_table_name')
        schema_info = asset.get('schema_info', {})
        fields = schema_info.get('fields', [])
        primary_key = schema_info.get('primary_key', [])
        
        # 确定关键字段
        key_fields = pattern.get('key_fields', [])
        if not key_fields and primary_key:
            key_fields = primary_key
        
        # 查找相关表
        related_tables = []
        for related_type, related_pattern in self.entity_patterns.items():
            if related_type != entity_type:
                # 检查是否有外键关系
                foreign_keys = schema_info.get('foreign_keys', [])
                for fk in foreign_keys:
                    if any(key in fk.get('referred_table', '') for key in related_pattern['tables']):
                        related_tables.append(fk.get('referred_table'))
        
        return SAPBusinessEntity(
            name=f"sap_entity_{entity_type}_{table_name.lower()}",
            display_name=f"{pattern['description']} - {table_name}",
            description=f"SAP业务实体: {pattern['description']} ({table_name})",
            entity_type=entity_type,
            sap_table_name=table_name,
            key_fields=key_fields,
            related_tables=list(set(related_tables)),
            business_domain=pattern.get('domain'),
            metadata={
                "source_asset": asset.get('name'),
                "table_fields": [f.get('name') for f in fields],
                "extraction_method": "pattern_matching"
            }
        )


"""
SAP数据资产发现器
通过OData服务和直接数据库查询发现SAP数据资产
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.sap_metadata_models import (
    SAPDataAsset,
    SAPAssetType,
    SAPBusinessDomain
)
from ..services.sap_database_client import SAPDatabaseClient
from ..services.sap_mcp_client import SAPMCPClient
from ..services.sap_abap_dictionary_client import SAPABAPDictionaryClient

logger = logging.getLogger(__name__)


class SAPDataAssetDiscoverer:
    """SAP数据资产发现器"""
    
    def __init__(
        self,
        db_client: Optional[SAPDatabaseClient] = None,
        mcp_client: Optional[SAPMCPClient] = None
    ):
        """
        初始化SAP数据资产发现器
        
        Args:
            db_client: SAP数据库客户端（可选）
            mcp_client: SAP MCP客户端（可选）
        """
        self.db_client = db_client
        self.mcp_client = mcp_client
        self.abap_dict_client = SAPABAPDictionaryClient(db_client) if db_client else None
        self.bapi_discoverer = SAPBAPIDiscoverer(db_client) if db_client else None
        self.sap_table_mapping = self._init_sap_table_mapping()
    
    def _init_sap_table_mapping(self) -> Dict[str, Dict[str, Any]]:
        """初始化SAP表映射（常用SAP表）"""
        return {
            # 主数据表
            "KNA1": {"type": SAPAssetType.MASTER_DATA, "domain": SAPBusinessDomain.SALES, "description": "客户主数据"},
            "LFA1": {"type": SAPAssetType.MASTER_DATA, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "供应商主数据"},
            "MARA": {"type": SAPAssetType.MASTER_DATA, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "物料主数据"},
            "MARC": {"type": SAPAssetType.MASTER_DATA, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "物料工厂数据"},
            "MVKE": {"type": SAPAssetType.MASTER_DATA, "domain": SAPBusinessDomain.SALES, "description": "物料销售数据"},
            # 事务数据表
            "VBAK": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "销售订单抬头"},
            "VBAP": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "销售订单项目"},
            "LIKP": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "交货单抬头"},
            "LIPS": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "交货单项目"},
            "VBRK": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "发票抬头"},
            "VBRP": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.SALES, "description": "发票项目"},
            "EKKO": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "采购订单抬头"},
            "EKPO": {"type": SAPAssetType.TRANSACTION_DATA, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "采购订单项目"},
            # 配置表
            "T001": {"type": SAPAssetType.CONFIGURATION, "domain": SAPBusinessDomain.FINANCE, "description": "公司代码"},
            "T001W": {"type": SAPAssetType.CONFIGURATION, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "工厂"},
            "T024": {"type": SAPAssetType.CONFIGURATION, "domain": SAPBusinessDomain.MATERIAL_MANAGEMENT, "description": "采购组织"},
        }
    
    async def discover_all_assets(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0,
        include_database: bool = True,
        include_odata: bool = True,
        include_bapi: bool = False
    ) -> List[SAPDataAsset]:
        """
        发现SAP数据资产（支持分批处理）
        
        Args:
            limit: 限制处理的服务数量（None表示处理所有）
            offset: 起始偏移量
            include_database: 是否从数据库发现
            include_odata: 是否从OData服务发现
            include_bapi: 是否包含BAPI/RFC函数发现
        
        Returns:
            SAP数据资产列表
        """
        assets = []
        
        # 1. 从数据库发现表
        if include_database and self.db_client:
            db_assets = await self._discover_from_database()
            assets.extend(db_assets)
        
        # 2. 从OData服务发现实体（支持分批）
        if include_odata and self.mcp_client:
            odata_assets = await self._discover_from_odata(limit=limit, offset=offset)
            assets.extend(odata_assets)
        
        # 3. 从TFDIR表发现BAPI/RFC函数（如果启用）
        if include_bapi and self.bapi_discoverer:
            try:
                # 发现BAPI函数
                bapi_assets = await self.bapi_discoverer.discover_bapi_functions(limit=limit, offset=offset)
                assets.extend(bapi_assets)
                logger.info(f"Discovered {len(bapi_assets)} BAPI functions")
                
                # 发现RFC函数（非BAPI）
                rfc_assets = await self.bapi_discoverer.discover_rfc_functions(limit=limit, offset=offset)
                assets.extend(rfc_assets)
                logger.info(f"Discovered {len(rfc_assets)} RFC functions")
            except Exception as e:
                logger.warning(f"Failed to discover BAPI/RFC functions: {e}")
        
        logger.info(f"Discovered {len(assets)} SAP data assets")
        return assets
    
    async def _discover_from_database(self) -> List[SAPDataAsset]:
        """从数据库发现数据资产"""
        assets = []
        
        try:
            # 获取所有表
            tables = await self.db_client.get_all_tables()
            logger.info(f"Found {len(tables)} tables in SAP database")
            
            for table_info in tables:
                try:
                    table_name = table_info.get('table_name')
                    schema = table_info.get('schema')
                    
                    # 获取表结构
                    table_structure = await self.db_client.get_sap_table_info(table_name, schema)
                    
                    # 获取ABAP数据字典信息（如果可用）
                    abap_dict_metadata = None
                    if self.abap_dict_client:
                        try:
                            abap_dict_metadata = await self.abap_dict_client.get_complete_table_metadata(
                                table_name, 
                                language='E'  # 默认英文，可配置
                            )
                        except Exception as e:
                            logger.warning(f"Failed to get ABAP dictionary metadata for {table_name}: {e}")
                    
                    # 确定资产类型和业务域
                    table_mapping = self.sap_table_mapping.get(table_name, {})
                    asset_type = table_mapping.get('type', SAPAssetType.TABLE)
                    domain = table_mapping.get('domain')
                    
                    # 优先使用ABAP字典中的表描述
                    if abap_dict_metadata and abap_dict_metadata.get('table_description'):
                        description = abap_dict_metadata['table_description']
                    else:
                        description = table_mapping.get('description', f"SAP表: {table_name}")
                    
                    # 增强schema信息，包含ABAP字典字段信息
                    enhanced_fields = []
                    db_fields = table_structure.get('columns', [])
                    abap_fields = abap_dict_metadata.get('fields', []) if abap_dict_metadata else []
                    
                    # 合并数据库字段和ABAP字典字段信息
                    abap_fields_dict = {f['field_name']: f for f in abap_fields}
                    for db_field in db_fields:
                        field_name = db_field.get('name') or db_field.get('column_name')
                        abap_field = abap_fields_dict.get(field_name)
                        
                        enhanced_field = {
                            **db_field,
                            "field_name": field_name
                        }
                        
                        if abap_field:
                            # 添加ABAP字典信息
                            enhanced_field.update({
                                "field_description": abap_field.get('field_description'),
                                "data_element": abap_field.get('data_element'),
                                "data_element_info": abap_field.get('data_element_info'),
                                "domain_name": abap_field.get('domain_name'),
                                "domain_values": abap_field.get('domain_values', []),
                                "check_table": abap_field.get('check_table'),
                                "reference_field": abap_field.get('reference_field')
                            })
                        
                        enhanced_fields.append(enhanced_field)
                    
                    # 创建数据资产
                    asset = SAPDataAsset(
                        name=f"sap_table_{table_name.lower()}",
                        display_name=description,
                        description=f"SAP数据库表: {table_name}",
                        asset_type=asset_type,
                        sap_table_name=table_name,
                        sap_module=domain,
                        schema_info={
                            "fields": enhanced_fields,
                            "primary_key": table_structure.get('primary_key', []),
                            "foreign_keys": table_structure.get('foreign_keys', []),
                            "indexes": table_structure.get('indexes', []),
                            "abap_dictionary": abap_dict_metadata.get('abap_dictionary') if abap_dict_metadata else None
                        },
                        tags=["SAP", "database", "table", table_name],
                        classification=self._classify_table_asset(table_name, asset_type, domain),
                        metadata={
                            "schema": schema,
                            "table_type": table_structure.get('sap_info', {}).get('table_type'),
                            "table_class": abap_dict_metadata.get('table_class') if abap_dict_metadata else None,
                            "row_count": table_structure.get('row_count'),
                            "discovery_method": "database",
                            "abap_dictionary_available": abap_dict_metadata is not None
                        }
                    )
                    assets.append(asset)
                    
                except Exception as e:
                    logger.warning(f"Failed to process table {table_info.get('table_name')}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error discovering assets from database: {e}", exc_info=True)
        
        return assets
    
    async def _discover_from_odata(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[SAPDataAsset]:
        """
        从OData服务发现数据资产（支持分批处理）
        
        Args:
            limit: 限制处理的服务数量
            offset: 起始偏移量
        """
        assets = []
        
        try:
            # 发现所有OData服务
            all_services = await self.mcp_client.discover_services()
            logger.info(f"Found {len(all_services)} total OData services")
            
            # 应用分批处理
            if limit is not None:
                services = all_services[offset:offset + limit]
                logger.info(f"Processing services {offset} to {offset + limit} (batch size: {len(services)})")
            else:
                services = all_services[offset:]
                logger.info(f"Processing services from {offset} to end (total: {len(services)})")
            
            for service in services:
                service_id = service.get('id') or service.get('name')
                service_name = service.get('name', '')
                service_description = service.get('description', '')
                
                # 获取服务中的实体
                entities = service.get('entities', [])
                
                for entity in entities:
                    entity_name = entity.get('name', '')
                    
                    # 获取实体结构（如果实体信息中没有，则调用API获取）
                    entity_structure = None
                    if isinstance(entity, dict) and 'properties' in entity:
                        # 实体信息中已包含结构
                        entity_structure = {
                            'properties': entity.get('properties', []),
                            'key': entity.get('key', [])
                        }
                    else:
                        # 调用API获取实体结构
                        try:
                            entity_structure = await self.mcp_client.get_entity_structure(
                                service_id,
                                entity_name
                            )
                        except Exception as e:
                            logger.warning(f"Failed to get structure for {entity_name}: {e}")
                            # 使用基本信息创建资产
                            entity_structure = {
                                'properties': [],
                                'key': []
                            }
                    
                    if entity_structure or True:  # 即使没有结构也创建资产
                        # 创建数据资产
                        # 提取业务术语（从实体名称中）
                        business_terms = []
                        entity_lower = entity_name.lower()
                        if 'customer' in entity_lower or 'kunnr' in entity_lower:
                            business_terms.append("客户")
                        if 'vendor' in entity_lower or 'supplier' in entity_lower or 'lifnr' in entity_lower:
                            business_terms.append("供应商")
                        if 'material' in entity_lower or 'mara' in entity_lower:
                            business_terms.append("物料")
                        if 'order' in entity_lower:
                            business_terms.append("订单")
                        
                        asset = SAPDataAsset(
                            name=f"sap_odata_{service_name.lower()}_{entity_name.lower()}",
                            display_name=f"{service_name} - {entity_name}",
                            description=f"SAP OData实体: {service_name}/{entity_name}",
                            asset_type=SAPAssetType.BUSINESS_OBJECT,
                            odata_service=service_name,
                            odata_entity=entity_name,
                            schema_info={
                                "properties": entity_structure.get('properties', []),
                                "key": entity_structure.get('key', [])
                            },
                            tags=["SAP", "OData", "API", service_name, entity_name],
                            classification=self._classify_odata_entity(entity_name, service_name),
                            business_terms=business_terms,
                            metadata={
                                "service_id": service_id,
                                "service_url": service.get('url'),
                                "discovery_method": "odata"
                            }
                        )
                        assets.append(asset)
                        
        except Exception as e:
            logger.error(f"Error discovering assets from OData: {e}", exc_info=True)
        
        return assets
    
    def _classify_asset_type(self, table_name: str, description: str) -> SAPAssetType:
        """
        根据表名和描述分类资产类型
        
        Args:
            table_name: 表名
            description: 描述
            
        Returns:
            资产类型
        """
        # 使用映射表
        if table_name in self.sap_table_mapping:
            return self.sap_table_mapping[table_name]['type']
        
        # 基于命名规则推断
        table_upper = table_name.upper()
        if table_upper.startswith('K') or table_upper.startswith('LFA'):
            return SAPAssetType.MASTER_DATA  # 客户/供应商主数据
        elif table_upper.startswith('M'):
            return SAPAssetType.MASTER_DATA  # 物料主数据
        elif table_upper.startswith('V') or table_upper.startswith('E'):
            return SAPAssetType.TRANSACTION_DATA  # 事务数据
        elif table_upper.startswith('T'):
            return SAPAssetType.CONFIGURATION  # 配置表
        else:
            return SAPAssetType.TABLE
    
    def _infer_business_domain(self, table_name: str, description: str) -> Optional[SAPBusinessDomain]:
        """
        推断业务域
        
        Args:
            table_name: 表名
            description: 描述
            
        Returns:
            业务域
        """
        # 使用映射表
        if table_name in self.sap_table_mapping:
            return self.sap_table_mapping[table_name].get('domain')
        
        # 基于表名和描述推断
        table_upper = table_name.upper()
        desc_lower = description.lower()
        
        if 'sales' in desc_lower or 'order' in desc_lower or table_upper.startswith('V'):
            return SAPBusinessDomain.SALES
        elif 'purchase' in desc_lower or 'procure' in desc_lower or table_upper.startswith('E'):
            return SAPBusinessDomain.MATERIAL_MANAGEMENT
        elif 'finance' in desc_lower or 'account' in desc_lower or table_upper.startswith('BKPF'):
            return SAPBusinessDomain.FINANCE
        elif 'material' in desc_lower or table_upper.startswith('M'):
            return SAPBusinessDomain.MATERIAL_MANAGEMENT
        
        return None
    
    def _classify_table_asset(self, table_name: str, asset_type: SAPAssetType, domain: Optional[SAPBusinessDomain]) -> str:
        """
        为数据库表生成细粒度的分类
        
        Args:
            table_name: 表名
            asset_type: 资产类型
            domain: 业务域
            
        Returns:
            分类字符串
        """
        # 基础分类
        base_classification = "sap_table"
        
        # 根据资产类型和业务域生成更细的分类
        if asset_type == SAPAssetType.MASTER_DATA:
            # 主数据表
            table_upper = table_name.upper()
            if table_upper.startswith('KNA') or 'CUSTOMER' in table_upper:
                return "sap_master_data_customer"
            elif table_upper.startswith('LFA') or 'VENDOR' in table_upper or 'SUPPLIER' in table_upper:
                return "sap_master_data_vendor"
            elif table_upper.startswith('MARA') or table_upper.startswith('MARC') or 'MATERIAL' in table_upper:
                return "sap_master_data_material"
            elif domain == SAPBusinessDomain.SALES:
                return "sap_master_data_sales"
            elif domain == SAPBusinessDomain.MATERIAL_MANAGEMENT:
                return "sap_master_data_mm"
            else:
                return "sap_master_data"
        elif asset_type == SAPAssetType.TRANSACTION_DATA:
            # 事务数据表
            table_upper = table_name.upper()
            if table_upper.startswith('VBAK') or table_upper.startswith('VBAP') or 'SALES_ORDER' in table_upper:
                return "sap_transaction_sales_order"
            elif table_upper.startswith('EKKO') or table_upper.startswith('EKPO') or 'PURCHASE_ORDER' in table_upper:
                return "sap_transaction_purchase_order"
            elif table_upper.startswith('LIKP') or table_upper.startswith('LIPS') or 'DELIVERY' in table_upper:
                return "sap_transaction_delivery"
            elif table_upper.startswith('VBRK') or table_upper.startswith('VBRP') or 'INVOICE' in table_upper:
                return "sap_transaction_invoice"
            elif domain == SAPBusinessDomain.SALES:
                return "sap_transaction_sales"
            elif domain == SAPBusinessDomain.MATERIAL_MANAGEMENT:
                return "sap_transaction_mm"
            else:
                return "sap_transaction_data"
        elif asset_type == SAPAssetType.CONFIGURATION:
            # 配置表
            if domain == SAPBusinessDomain.FINANCE:
                return "sap_configuration_finance"
            elif domain == SAPBusinessDomain.MATERIAL_MANAGEMENT:
                return "sap_configuration_mm"
            elif domain == SAPBusinessDomain.SALES:
                return "sap_configuration_sales"
            else:
                return "sap_configuration"
        else:
            return base_classification
    
    def _classify_odata_entity(self, entity_name: str, service_name: str) -> str:
        """
        为OData实体生成细粒度的分类
        
        Args:
            entity_name: 实体名称
            service_name: 服务名称
            
        Returns:
            分类字符串
        """
        # 基础分类
        base_classification = "sap_odata_entity"
        
        # 转换为小写以便匹配
        entity_lower = entity_name.lower()
        service_lower = service_name.lower()
        
        # 根据实体名称模式分类
        if 'customer' in entity_lower or 'kunnr' in entity_lower or 'kna1' in entity_lower:
            return "sap_odata_master_data_customer"
        elif 'vendor' in entity_lower or 'supplier' in entity_lower or 'lifnr' in entity_lower or 'lfa1' in entity_lower:
            return "sap_odata_master_data_vendor"
        elif 'material' in entity_lower or 'mara' in entity_lower or 'marc' in entity_lower:
            return "sap_odata_master_data_material"
        elif 'sales' in entity_lower and 'order' in entity_lower:
            return "sap_odata_transaction_sales_order"
        elif 'purchase' in entity_lower and 'order' in entity_lower:
            return "sap_odata_transaction_purchase_order"
        elif 'delivery' in entity_lower:
            return "sap_odata_transaction_delivery"
        elif 'invoice' in entity_lower:
            return "sap_odata_transaction_invoice"
        elif 'order' in entity_lower:
            if 'sales' in service_lower:
                return "sap_odata_transaction_sales_order"
            elif 'purchase' in service_lower or 'procure' in service_lower:
                return "sap_odata_transaction_purchase_order"
            else:
                return "sap_odata_transaction_order"
        elif 'master' in entity_lower or 'masterdata' in entity_lower:
            return "sap_odata_master_data"
        elif 'transaction' in entity_lower:
            return "sap_odata_transaction_data"
        elif 'configuration' in entity_lower or 'config' in entity_lower:
            return "sap_odata_configuration"
        elif 'currency' in entity_lower or 'unit' in entity_lower or 'format' in entity_lower:
            return "sap_odata_reference_data"
        else:
            # 根据服务名称推断
            if 'sales' in service_lower:
                return "sap_odata_sales"
            elif 'purchase' in service_lower or 'procure' in service_lower:
                return "sap_odata_procurement"
            elif 'material' in service_lower:
                return "sap_odata_material"
            elif 'finance' in service_lower or 'financial' in service_lower:
                return "sap_odata_finance"
            else:
                return base_classification


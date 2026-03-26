"""
SAP BAPI/RFC函数发现器
从SAP数据库的TFDIR表发现BAPI和RFC函数模块
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text

from ..models.sap_metadata_models import SAPDataAsset, SAPAssetType, SAPBusinessDomain
from .sap_database_client import SAPDatabaseClient

logger = logging.getLogger(__name__)


class SAPBAPIDiscoverer:
    """SAP BAPI/RFC函数发现器"""
    
    def __init__(self, db_client: SAPDatabaseClient):
        """
        初始化BAPI发现器
        
        Args:
            db_client: SAP数据库客户端
        """
        self.db_client = db_client
    
    async def discover_bapi_functions(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SAPDataAsset]:
        """
        从TFDIR表发现BAPI函数
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            BAPI函数资产列表
        """
        assets = []
        
        if not self.db_client or not self.db_client.engine:
            logger.warning("Database client not available, skipping BAPI discovery")
            return assets
        
        try:
            # 查询TFDIR表，获取BAPI函数
            # TFDIR: RFC函数目录表
            # FUNCNAME: 函数名
            # PNAME: 程序名
            # INCLUDE: 包含文件
            query = text("""
                SELECT 
                    FUNCNAME as function_name,
                    PNAME as program_name,
                    INCLUDE as include_name
                FROM TFDIR
                WHERE FUNCNAME LIKE 'BAPI%'
                ORDER BY FUNCNAME
            """)
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query)
                
                for row in result:
                    function_name = row.function_name
                    
                    # 获取函数参数（从TFBIR表）
                    parameters = await self._get_function_parameters(function_name)
                    
                    # 提取业务术语
                    business_terms = self._extract_business_terms_from_bapi(function_name)
                    
                    # 确定业务域
                    domain = self._infer_business_domain(function_name)
                    
                    # 创建BAPI资产
                    asset = SAPDataAsset(
                        name=f"sap_bapi_{function_name.lower()}",
                        display_name=f"BAPI: {function_name}",
                        description=f"SAP BAPI函数: {function_name}",
                        asset_type=SAPAssetType.BUSINESS_OBJECT,
                        sap_object_type="BAPI",
                        sap_module=domain,
                        schema_info={
                            "function_name": function_name,
                            "program_name": row.program_name,
                            "include_name": row.include_name,
                            "parameters": parameters,
                            "function_type": "BAPI"
                        },
                        tags=["SAP", "BAPI", "RFC", "Function", function_name],
                        classification="sap_bapi_function",
                        business_terms=business_terms,
                        metadata={
                            "discovery_method": "database",
                            "source_table": "TFDIR"
                        }
                    )
                    assets.append(asset)
            
            logger.info(f"Discovered {len(assets)} BAPI functions")
            
        except Exception as e:
            logger.error(f"Error discovering BAPI functions: {e}", exc_info=True)
        
        return assets
    
    async def discover_rfc_functions(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SAPDataAsset]:
        """
        从TFDIR表发现RFC函数（非BAPI）
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            RFC函数资产列表
        """
        assets = []
        
        if not self.db_client or not self.db_client.engine:
            return assets
        
        try:
            # 查询TFDIR表，获取RFC函数（排除BAPI）
            query = text("""
                SELECT 
                    FUNCNAME as function_name,
                    PNAME as program_name,
                    INCLUDE as include_name
                FROM TFDIR
                WHERE FUNCNAME NOT LIKE 'BAPI%'
                AND FUNCNAME LIKE 'RFC%' OR FUNCNAME LIKE 'Z%' OR FUNCNAME LIKE 'Y%'
                ORDER BY FUNCNAME
            """)
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query)
                
                for row in result:
                    function_name = row.function_name
                    
                    # 获取函数参数
                    parameters = await self._get_function_parameters(function_name)
                    
                    # 创建RFC资产
                    asset = SAPDataAsset(
                        name=f"sap_rfc_{function_name.lower()}",
                        display_name=f"RFC: {function_name}",
                        description=f"SAP RFC函数: {function_name}",
                        asset_type=SAPAssetType.BUSINESS_OBJECT,
                        sap_object_type="RFC",
                        schema_info={
                            "function_name": function_name,
                            "program_name": row.program_name,
                            "include_name": row.include_name,
                            "parameters": parameters,
                            "function_type": "RFC"
                        },
                        tags=["SAP", "RFC", "Function", function_name],
                        classification="sap_rfc_function",
                        metadata={
                            "discovery_method": "database",
                            "source_table": "TFDIR"
                        }
                    )
                    assets.append(asset)
            
            logger.info(f"Discovered {len(assets)} RFC functions")
            
        except Exception as e:
            logger.error(f"Error discovering RFC functions: {e}", exc_info=True)
        
        return assets
    
    async def _get_function_parameters(self, function_name: str) -> List[Dict[str, Any]]:
        """
        获取函数参数（从TFBIR表）
        
        Args:
            function_name: 函数名
            
        Returns:
            参数列表
        """
        parameters = []
        
        try:
            # TFBIR: RFC函数接口（参数）
            # FUNCNAME: 函数名
            # PARAMETER: 参数名
            # PARAMTYPE: 参数类型（I=输入, E=输出, C=输入输出, T=表）
            # PARAMTEXT: 参数描述
            query = text("""
                SELECT 
                    PARAMETER as parameter_name,
                    PARAMTYPE as parameter_type,
                    PARAMTEXT as parameter_text
                FROM TFBIR
                WHERE FUNCNAME = :function_name
                ORDER BY PARAMETER
            """)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query, {"function_name": function_name})
                
                for row in result:
                    param_type_map = {
                        'I': 'input',
                        'E': 'output',
                        'C': 'changing',
                        'T': 'table'
                    }
                    
                    parameters.append({
                        "parameter_name": row.parameter_name,
                        "parameter_type": param_type_map.get(row.parameter_type, row.parameter_type),
                        "parameter_text": row.parameter_text
                    })
        
        except Exception as e:
            logger.warning(f"Failed to get parameters for {function_name}: {e}")
        
        return parameters
    
    def _extract_business_terms_from_bapi(self, function_name: str) -> List[str]:
        """
        从BAPI函数名提取业务术语
        
        Args:
            function_name: BAPI函数名（如BAPI_CUSTOMER_GETDETAIL）
            
        Returns:
            业务术语列表
        """
        terms = []
        func_upper = function_name.upper()
        
        # BAPI函数名通常格式：BAPI_<ENTITY>_<ACTION>
        # 例如：BAPI_CUSTOMER_GETDETAIL -> 客户
        #      BAPI_MATERIAL_GETDETAIL -> 物料
        
        if "CUSTOMER" in func_upper or "KUNNR" in func_upper:
            terms.append("客户")
        if "VENDOR" in func_upper or "SUPPLIER" in func_upper or "LIFNR" in func_upper:
            terms.append("供应商")
        if "MATERIAL" in func_upper or "MATNR" in func_upper:
            terms.append("物料")
        if "ORDER" in func_upper or "AUFTRAG" in func_upper:
            terms.append("订单")
        if "SALES" in func_upper:
            terms.append("销售")
        if "PURCHASE" in func_upper or "PURCH" in func_upper:
            terms.append("采购")
        if "INVOICE" in func_upper:
            terms.append("发票")
        if "DELIVERY" in func_upper:
            terms.append("交货")
        
        return terms
    
    def _infer_business_domain(self, function_name: str) -> Optional[SAPBusinessDomain]:
        """
        从函数名推断业务域
        
        Args:
            function_name: 函数名
            
        Returns:
            业务域
        """
        func_upper = function_name.upper()
        
        if "CUSTOMER" in func_upper or "SALES" in func_upper:
            return SAPBusinessDomain.SALES
        elif "VENDOR" in func_upper or "PURCHASE" in func_upper or "PURCH" in func_upper:
            return SAPBusinessDomain.PROCUREMENT
        elif "MATERIAL" in func_upper:
            return SAPBusinessDomain.MATERIAL_MANAGEMENT
        elif "FINANCE" in func_upper or "FI" in func_upper:
            return SAPBusinessDomain.FINANCE
        elif "HR" in func_upper or "HUMAN" in func_upper:
            return SAPBusinessDomain.HUMAN_RESOURCES
        
        return None



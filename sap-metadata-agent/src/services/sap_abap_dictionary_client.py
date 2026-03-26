"""
SAP ABAP数据字典客户端
从SAP ABAP数据字典表（DD02L, DD03L, DD04T, DD07T）获取业务元数据
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from .sap_database_client import SAPDatabaseClient

logger = logging.getLogger(__name__)


class SAPABAPDictionaryClient:
    """SAP ABAP数据字典客户端"""
    
    def __init__(self, db_client: SAPDatabaseClient):
        """
        初始化ABAP数据字典客户端
        
        Args:
            db_client: SAP数据库客户端
        """
        self.db_client = db_client
    
    async def get_table_info(self, table_name: str, language: str = 'E') -> Optional[Dict[str, Any]]:
        """
        从DD02L获取表信息
        
        Args:
            table_name: 表名（如KNA1）
            language: 语言代码（E=英文, Z=中文等）
            
        Returns:
            表信息字典，包含表描述、表类型等
        """
        if not self.db_client or not self.db_client.engine:
            return None
        
        try:
            # DD02L: SAP表信息
            # TABNAME: 表名
            # DDCLASS: 表类型（TRANSP=透明表, CLUSTER=簇表, POOL=池表）
            # DDMTEXT: 表描述
            query = text("""
                SELECT 
                    TABNAME as table_name,
                    DDCLASS as table_class,
                    DDMTEXT as table_description,
                    DDMTEXT as short_text
                FROM DD02L
                WHERE TABNAME = :table_name
                AND DDLANGUAGE = :language
                AND AS4LOCAL = 'A'
            """)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query, {"table_name": table_name, "language": language})
                row = result.fetchone()
                
                if row:
                    return {
                        "table_name": row.table_name,
                        "table_class": row.table_class,
                        "table_description": row.table_description,
                        "short_text": row.short_text
                    }
        except Exception as e:
            logger.warning(f"Failed to get table info for {table_name} from DD02L: {e}")
        
        return None
    
    async def get_field_info(self, table_name: str, language: str = 'E') -> List[Dict[str, Any]]:
        """
        从DD03L获取表字段信息
        
        Args:
            table_name: 表名
            language: 语言代码
            
        Returns:
            字段信息列表
        """
        if not self.db_client or not self.db_client.engine:
            return []
        
        fields = []
        try:
            # DD03L: 表字段信息
            # TABNAME: 表名
            # FIELDNAME: 字段名
            # POSITION: 位置
            # KEYFLAG: 是否主键
            # ROLLNAME: 数据元素名
            # DOMNAME: 域名
            # DATATYPE: 数据类型
            # LENG: 长度
            # DECIMALS: 小数位数
            # CHECKTABLE: 检查表
            query = text("""
                SELECT 
                    FIELDNAME as field_name,
                    POSITION as position,
                    KEYFLAG as is_key,
                    ROLLNAME as data_element,
                    DOMNAME as domain_name,
                    DATATYPE as data_type,
                    LENG as length,
                    DECIMALS as decimals,
                    CHECKTABLE as check_table,
                    NOTNULL as is_not_null,
                    REFFIELD as reference_field
                FROM DD03L
                WHERE TABNAME = :table_name
                AND DDLANGUAGE = :language
                AND AS4LOCAL = 'A'
                ORDER BY POSITION
            """)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query, {"table_name": table_name, "language": language})
                
                for row in result:
                    fields.append({
                        "field_name": row.field_name,
                        "position": row.position,
                        "is_key": row.is_key == 'X',
                        "data_element": row.data_element,
                        "domain_name": row.domain_name,
                        "data_type": row.data_type,
                        "length": row.length,
                        "decimals": row.decimals,
                        "check_table": row.check_table,
                        "is_not_null": row.is_not_null == 'X',
                        "reference_field": row.reference_field
                    })
        except Exception as e:
            logger.warning(f"Failed to get field info for {table_name} from DD03L: {e}")
        
        return fields
    
    async def get_data_element_text(self, rollname: str, language: str = 'E') -> Optional[Dict[str, Any]]:
        """
        从DD04T获取数据元素文本
        
        Args:
            rollname: 数据元素名
            language: 语言代码
            
        Returns:
            数据元素文本信息
        """
        if not self.db_client or not self.db_client.engine:
            return None
        
        try:
            # DD04T: 数据元素文本
            # ROLLNAME: 数据元素名
            # DDTEXT: 短文本
            # REPTEXT: 标题
            # SCRTEXT_S: 短描述
            # SCRTEXT_M: 中描述
            # SCRTEXT_L: 长描述
            query = text("""
                SELECT 
                    ROLLNAME as data_element,
                    DDTEXT as short_text,
                    REPTEXT as header_text,
                    SCRTEXT_S as short_description,
                    SCRTEXT_M as medium_description,
                    SCRTEXT_L as long_description
                FROM DD04T
                WHERE ROLLNAME = :rollname
                AND DDLANGUAGE = :language
                AND AS4LOCAL = 'A'
            """)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query, {"rollname": rollname, "language": language})
                row = result.fetchone()
                
                if row:
                    return {
                        "data_element": row.data_element,
                        "short_text": row.short_text,
                        "header_text": row.header_text,
                        "short_description": row.short_description,
                        "medium_description": row.medium_description,
                        "long_description": row.long_description
                    }
        except Exception as e:
            logger.warning(f"Failed to get data element text for {rollname} from DD04T: {e}")
        
        return None
    
    async def get_domain_values(self, domname: str, language: str = 'E') -> List[Dict[str, Any]]:
        """
        从DD07T获取域值
        
        Args:
            domname: 域名
            language: 语言代码
            
        Returns:
            域值列表
        """
        if not self.db_client or not self.db_client.engine:
            return []
        
        values = []
        try:
            # DD07T: 域值文本
            # DOMNAME: 域名
            # DDLANGUAGE: 语言
            # DOMVALUE_L: 域值（低值）
            # DOMVALUE_H: 域值（高值，用于范围）
            # DDTEXT: 域值文本
            query = text("""
                SELECT 
                    DOMVALUE_L as domain_value_low,
                    DOMVALUE_H as domain_value_high,
                    DDTEXT as domain_value_text
                FROM DD07T
                WHERE DOMNAME = :domname
                AND DDLANGUAGE = :language
                AND AS4LOCAL = 'A'
                ORDER BY DOMVALUE_L
            """)
            
            with self.db_client.engine.connect() as conn:
                result = conn.execute(query, {"domname": domname, "language": language})
                
                for row in result:
                    values.append({
                        "domain_value_low": row.domain_value_low,
                        "domain_value_high": row.domain_value_high,
                        "domain_value_text": row.domain_value_text
                    })
        except Exception as e:
            logger.warning(f"Failed to get domain values for {domname} from DD07T: {e}")
        
        return values
    
    async def get_complete_table_metadata(
        self, 
        table_name: str, 
        language: str = 'E'
    ) -> Dict[str, Any]:
        """
        获取完整的表元数据（包括ABAP字典信息）
        
        Args:
            table_name: 表名
            language: 语言代码
            
        Returns:
            完整的表元数据
        """
        metadata = {
            "table_name": table_name,
            "abap_dictionary": {}
        }
        
        # 1. 获取表信息
        table_info = await self.get_table_info(table_name, language)
        if table_info:
            metadata["abap_dictionary"]["table_info"] = table_info
            metadata["table_description"] = table_info.get("table_description")
            metadata["table_class"] = table_info.get("table_class")
        
        # 2. 获取字段信息
        fields = await self.get_field_info(table_name, language)
        metadata["fields"] = []
        
        for field in fields:
            field_metadata = {
                **field,
                "data_element_info": None,
                "domain_values": []
            }
            
            # 3. 获取数据元素文本
            if field.get("data_element"):
                data_element_info = await self.get_data_element_text(
                    field["data_element"], 
                    language
                )
                if data_element_info:
                    field_metadata["data_element_info"] = data_element_info
                    # 使用数据元素的描述作为字段描述
                    field_metadata["field_description"] = (
                        data_element_info.get("long_description") or
                        data_element_info.get("medium_description") or
                        data_element_info.get("short_description") or
                        data_element_info.get("short_text")
                    )
            
            # 4. 获取域值
            if field.get("domain_name"):
                domain_values = await self.get_domain_values(
                    field["domain_name"], 
                    language
                )
                if domain_values:
                    field_metadata["domain_values"] = domain_values
            
            metadata["fields"].append(field_metadata)
        
        return metadata



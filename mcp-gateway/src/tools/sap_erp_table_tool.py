"""
SAP ERP表查询工具
通过RFC直接连接SAP ERP（S4 HANA）并查询表数据
"""
from typing import Dict, Any, List, Optional
import logging
import os
from datetime import datetime

from ..models.tool_models import ToolDefinition, ToolType, ToolStatus

logger = logging.getLogger(__name__)

# pyRFC连接对象（延迟初始化）
_rfc_connection = None


def _get_rfc_connection():
    """获取RFC连接（延迟初始化）"""
    global _rfc_connection
    
    if _rfc_connection is None:
        try:
            import pyrfc
        except ImportError:
            raise ImportError(
                "pyRFC library not installed. "
                "Please install it: pip install pyrfc"
            )
        
        # 从环境变量或配置获取连接参数
        conn_params = {
            'user': os.getenv('SAP_USER', 'admin'),
            'passwd': os.getenv('SAP_PASSWORD', 'ad@kf29!()G'),
            'ashost': os.getenv('SAP_HOST', '10.24.49.128'),
            'sysnr': os.getenv('SAP_SYSNR', '00'),
            'client': os.getenv('SAP_CLIENT', '100'),
        }
        
        try:
            _rfc_connection = pyrfc.Connection(**conn_params)
            logger.info(f"Connected to SAP ERP: {conn_params['ashost']} (Client: {conn_params['client']})")
        except Exception as e:
            logger.error(f"Failed to connect to SAP ERP: {e}")
            raise
    
    # 检查连接是否仍然有效
    try:
        _rfc_connection.ping()
    except:
        # 连接失效，重新连接
        logger.warning("RFC connection lost, reconnecting...")
        _rfc_connection = None
        return _get_rfc_connection()
    
    return _rfc_connection


async def query_sap_table(
    table_name: str,
    fields: Optional[List[str]] = None,
    where_clause: Optional[str] = None,
    max_rows: int = 100,
    order_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询SAP ERP表数据
    
    Args:
        table_name: 表名（如：BKPF）
        fields: 要查询的字段列表（可选，默认查询所有字段）
        where_clause: WHERE条件（可选，ABAP语法）
        max_rows: 最大返回行数（默认100）
        order_by: 排序字段（可选）
    
    Returns:
        查询结果字典
    """
    try:
        conn = _get_rfc_connection()
        
        # 构建RFC函数调用参数
        # 使用RFC_READ_TABLE函数模块来查询表
        rfc_params = {
            'QUERY_TABLE': table_name.upper(),
            'DELIMITER': '|',  # 字段分隔符
            'NO_DATA': '',  # 不返回数据，只返回结构（用于获取字段列表）
        }
        
        # 如果指定了字段，设置字段列表
        if fields:
            rfc_params['FIELDS'] = [
                {'FIELDNAME': field.upper()} for field in fields
            ]
        else:
            # 先获取表结构，确定所有字段
            structure_params = {
                'QUERY_TABLE': table_name.upper(),
                'DELIMITER': '|',
                'NO_DATA': 'X',  # 只返回结构，不返回数据
            }
            structure_result = conn.call('RFC_READ_TABLE', **structure_params)
            
            # 获取字段列表
            available_fields = [field['FIELDNAME'] for field in structure_result.get('FIELDS', [])]
            if available_fields:
                rfc_params['FIELDS'] = [
                    {'FIELDNAME': field} for field in available_fields
                ]
            # NO_DATA已经默认为空字符串，会返回数据
        
        # 设置WHERE条件
        if where_clause:
            # WHERE条件需要转换为RFC_READ_TABLE的OPTIONS格式
            # OPTIONS是一个表，每行是一个条件
            rfc_params['OPTIONS'] = [
                {'TEXT': where_clause}
            ]
        
        # 设置最大行数
        rfc_params['ROWCOUNT'] = max_rows
        
        # 设置行跳过（用于分页，这里从0开始）
        rfc_params['ROWSKIPS'] = 0
        
        # 调用RFC函数
        logger.info(f"Querying SAP table {table_name} with params: {rfc_params}")
        result = conn.call('RFC_READ_TABLE', **rfc_params)
        
        # 解析结果
        data_rows = result.get('DATA', [])
        fields_info = result.get('FIELDS', [])
        
        # 解析数据行
        parsed_data = []
        for row in data_rows:
            # 每行数据是一个字符串，用分隔符分隔
            row_data = {}
            row_string = row.get('WA', '')
            if row_string:
                values = row_string.split('|')
                for i, field_info in enumerate(fields_info):
                    field_name = field_info.get('FIELDNAME', '')
                    if i < len(values):
                        row_data[field_name] = values[i].strip()
                parsed_data.append(row_data)
        
        return {
            "success": True,
            "table_name": table_name.upper(),
            "row_count": len(parsed_data),
            "fields": [f.get('FIELDNAME') for f in fields_info],
            "data": parsed_data,
            "query_info": {
                "where_clause": where_clause,
                "max_rows": max_rows,
                "order_by": order_by
            }
        }
        
    except ImportError as e:
        logger.error(f"pyRFC not installed: {e}")
        return {
            "success": False,
            "error": f"pyRFC library not installed: {str(e)}",
            "error_code": "LIBRARY_NOT_INSTALLED"
        }
    except Exception as e:
        logger.error(f"Failed to query SAP table {table_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_code": "QUERY_FAILED",
            "table_name": table_name.upper()
        }


async def execute_query_sap_table(parameters: Dict[str, Any]) -> Any:
    """
    执行SAP表查询工具
    
    Args:
        parameters: 工具参数
            - table_name: 表名（必需）
            - fields: 字段列表（可选）
            - where_clause: WHERE条件（可选）
            - max_rows: 最大行数（默认100）
            - order_by: 排序字段（可选）
    
    Returns:
        查询结果
    """
    table_name = parameters.get("table_name")
    if not table_name:
        raise ValueError("table_name参数是必需的")
    
    fields = parameters.get("fields")
    where_clause = parameters.get("where_clause")
    max_rows = parameters.get("max_rows", 100)
    order_by = parameters.get("order_by")
    
    return await query_sap_table(
        table_name=table_name,
        fields=fields,
        where_clause=where_clause,
        max_rows=max_rows,
        order_by=order_by
    )


# 工具定义
SAP_ERP_TABLE_TOOL = ToolDefinition(
    name="sap_erp_table_query",
    description="查询SAP ERP（S4 HANA）表数据。通过RFC直接连接SAP系统并执行表查询。支持字段选择、WHERE条件和分页。",
    version="1.0.0",
    tool_type=ToolType.FUNCTION,
    status=ToolStatus.ACTIVE,
    parameters={
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "SAP表名（必需），如：BKPF（会计凭证表）、VBAK（销售订单表）",
                "minLength": 1,
                "maxLength": 30,
                "examples": ["BKPF", "VBAK", "MARA", "KNA1"]
            },
            "fields": {
                "type": "array",
                "description": "要查询的字段列表（可选）。如果不指定，查询所有字段",
                "items": {
                    "type": "string"
                },
                "examples": [
                    ["BELNR", "GJAHR", "BUKRS"],
                    ["VBELN", "ERDAT", "VKORG"]
                ]
            },
            "where_clause": {
                "type": "string",
                "description": "WHERE条件（可选），使用ABAP语法。例如：BUKRS = '1000' AND GJAHR = '2024'",
                "examples": [
                    "BUKRS = '1000'",
                    "GJAHR = '2024' AND MONAT = '01'",
                    "BELNR LIKE '1%'"
                ]
            },
            "max_rows": {
                "type": "integer",
                "description": "最大返回行数（默认100，最大10000）",
                "minimum": 1,
                "maximum": 10000,
                "default": 100
            },
            "order_by": {
                "type": "string",
                "description": "排序字段（可选），例如：BELNR DESC",
                "examples": ["BELNR", "GJAHR DESC", "ERDAT ASC"]
            }
        },
        "required": ["table_name"]
    },
    required_parameters=["table_name"],
    returns={
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "是否成功"
            },
            "table_name": {
                "type": "string",
                "description": "查询的表名"
            },
            "row_count": {
                "type": "integer",
                "description": "返回的行数"
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "字段列表"
            },
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "查询结果数据"
            },
            "query_info": {
                "type": "object",
                "description": "查询信息"
            },
            "error": {
                "type": "string",
                "description": "错误信息（如果失败）"
            },
            "error_code": {
                "type": "string",
                "description": "错误代码（如果失败）"
            }
        }
    },
    metadata={
        "category": "sap",
        "author": "system",
        "service": "mcp-gateway",
        "requires_config": {
            "SAP_USER": "SAP用户名",
            "SAP_PASSWORD": "SAP密码",
            "SAP_HOST": "SAP应用服务器地址",
            "SAP_SYSNR": "SAP系统编号（默认00）",
            "SAP_CLIENT": "SAP客户端（默认100）"
        },
        "sap_system": "S4 HANA",
        "connection_type": "RFC"
    }
)


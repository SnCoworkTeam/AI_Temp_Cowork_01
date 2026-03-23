"""
同步SAP ERP表查询工具到数据库和元数据服务
"""
import asyncio
import httpx
import json
import logging
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_gateway.src.tools.sap_erp_table_tool import SAP_ERP_TABLE_TOOL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os

MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL", "http://localhost:8001")


async def sync_sap_erp_table_tool():
    """通过API同步SAP ERP表查询工具"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("Syncing sap_erp_table_query tool via API...")
            
            # 准备工具定义
            tool_def = {
                "name": SAP_ERP_TABLE_TOOL.name,
                "description": SAP_ERP_TABLE_TOOL.description,
                "version": SAP_ERP_TABLE_TOOL.version,
                "tool_type": SAP_ERP_TABLE_TOOL.tool_type.value if hasattr(SAP_ERP_TABLE_TOOL.tool_type, 'value') else str(SAP_ERP_TABLE_TOOL.tool_type),
                "status": SAP_ERP_TABLE_TOOL.status.value if hasattr(SAP_ERP_TABLE_TOOL.status, 'value') else str(SAP_ERP_TABLE_TOOL.status),
                "parameters": SAP_ERP_TABLE_TOOL.parameters,
                "required_parameters": SAP_ERP_TABLE_TOOL.required_parameters,
                "returns": SAP_ERP_TABLE_TOOL.returns,
                "metadata": SAP_ERP_TABLE_TOOL.metadata or {}
            }
            
            # 调用注册API
            response = await client.post(
                f"{MCP_GATEWAY_URL}/api/tools/register",
                json={
                    "tool": tool_def,
                    "overwrite": True
                }
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ Successfully synced sap_erp_table_query tool via API")
                logger.info(f"   Tool ID: {result.get('tool_id', 'N/A')}")
                logger.info(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ Failed to sync sap_erp_table_query tool: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                
        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to MCP Gateway at {MCP_GATEWAY_URL}")
            logger.error("   Please make sure the MCP Gateway service is running")
        except Exception as e:
            logger.error(f"❌ Error syncing sap_erp_table_query tool: {str(e)}", exc_info=True)


if __name__ == "__main__":
    import os
    asyncio.run(sync_sap_erp_table_tool())


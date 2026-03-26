"""
同步send_email工具到数据库和元数据服务
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from database.src.core.session import SessionLocal
from mcp_gateway.src.services.tool_service import ToolService
from mcp_gateway.src.tools.tool_registry import tool_registry
from mcp_gateway.src.tools.email_tool import SEND_EMAIL_TOOL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_send_email_tool():
    """同步send_email工具到数据库和元数据服务"""
    
    # 获取数据库会话
    db: Session = SessionLocal()
    tool_service = ToolService(db, tool_registry)
    
    try:
        logger.info("Syncing send_email tool...")
        
        # 转换为字典格式
        tool_def = {
            "name": SEND_EMAIL_TOOL.name,
            "description": SEND_EMAIL_TOOL.description,
            "version": SEND_EMAIL_TOOL.version,
            "tool_type": SEND_EMAIL_TOOL.tool_type.value if hasattr(SEND_EMAIL_TOOL.tool_type, 'value') else str(SEND_EMAIL_TOOL.tool_type),
            "parameters": SEND_EMAIL_TOOL.parameters,
            "required_parameters": SEND_EMAIL_TOOL.required_parameters,
            "returns": SEND_EMAIL_TOOL.returns,
            "metadata": SEND_EMAIL_TOOL.metadata or {}
        }
        
        # 注册工具（会保存到数据库并同步到元数据服务）
        result = await tool_service.register_tool(
            tool_def,
            overwrite=True  # 如果已存在则更新
        )
        
        if result.get("success"):
            logger.info(f"✅ Successfully synced send_email tool")
            logger.info(f"   Tool ID: {result.get('tool_id')}")
            logger.info(f"   Tool Name: {result.get('tool_name')}")
        else:
            logger.error(f"❌ Failed to sync send_email tool: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Error syncing send_email tool: {str(e)}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(sync_send_email_tool())



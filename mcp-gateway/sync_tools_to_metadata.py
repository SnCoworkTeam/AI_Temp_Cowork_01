"""
同步工具到数据库和元数据服务
将内存中注册的工具持久化到数据库，并同步到元数据服务
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
from mcp_gateway.src.models.tool_models import ToolDefinition
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sync_tools_to_database_and_metadata():
    """同步工具到数据库和元数据服务"""
    
    # 获取数据库会话
    db: Session = SessionLocal()
    tool_service = ToolService(db, tool_registry)
    
    try:
        # 获取所有已注册的工具
        all_tools = tool_registry.list_tools()
        
        logger.info(f"Found {len(all_tools)} tools in registry")
        
        synced_count = 0
        failed_count = 0
        
        for tool_dict in all_tools:
            tool_name = tool_dict.get("name")
            if not tool_name:
                continue
            
            try:
                logger.info(f"Syncing tool: {tool_name}")
                
                # 转换为ToolDefinition格式
                tool_def = {
                    "name": tool_name,
                    "description": tool_dict.get("description", ""),
                    "version": tool_dict.get("version", "1.0.0"),
                    "tool_type": tool_dict.get("tool_type", "function"),
                    "parameters": tool_dict.get("parameters", {}),
                    "required_parameters": tool_dict.get("required_parameters", []),
                    "returns": tool_dict.get("returns", {}),
                    "metadata": tool_dict.get("metadata", {})
                }
                
                # 注册工具（会保存到数据库并同步到元数据服务）
                result = await tool_service.register_tool(
                    tool_def,
                    overwrite=True  # 如果已存在则更新
                )
                
                if result.get("success"):
                    logger.info(f"✅ Successfully synced tool: {tool_name}")
                    synced_count += 1
                else:
                    logger.warning(f"⚠️ Failed to sync tool: {tool_name} - {result.get('message', 'Unknown error')}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Error syncing tool {tool_name}: {str(e)}", exc_info=True)
                failed_count += 1
        
        logger.info(f"\n=== Sync Summary ===")
        logger.info(f"Total tools: {len(all_tools)}")
        logger.info(f"Successfully synced: {synced_count}")
        logger.info(f"Failed: {failed_count}")
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(sync_tools_to_database_and_metadata())


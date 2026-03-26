"""
通过API同步send_email工具到数据库和元数据服务
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

# 直接定义工具信息，避免导入问题
SEND_EMAIL_TOOL_INFO = {
    "name": "send_email",
    "description": "发送电子邮件。支持文本和HTML格式，可以添加附件、抄送和密送。需要配置SMTP服务器信息。",
    "version": "1.0.0",
    "tool_type": "function",
    "status": "active",
    "parameters": {
        "type": "object",
        "properties": {
            "to_emails": {
                "type": ["string", "array"],
                "description": "收件人邮箱地址（必需）。可以是字符串（多个邮箱用逗号或分号分隔）或数组"
            },
            "subject": {
                "type": "string",
                "description": "邮件主题（必需）"
            },
            "body": {
                "type": "string",
                "description": "邮件正文内容（必需）"
            },
            "body_type": {
                "type": "string",
                "description": "正文类型：text（纯文本）或html（HTML格式）",
                "enum": ["text", "html"],
                "default": "text"
            }
        },
        "required": ["to_emails", "subject", "body"]
    },
    "required_parameters": ["to_emails", "subject", "body"],
    "metadata": {
        "category": "communication",
        "author": "system",
        "tags": ["邮件", "发送", "通知", "通信"]
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_GATEWAY_URL = "http://localhost:8001"


async def sync_send_email_tool():
    """通过API同步send_email工具"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("Syncing send_email tool via API...")
            
            # 准备工具定义
            tool_def = SEND_EMAIL_TOOL_INFO
            
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
                logger.info(f"✅ Successfully synced send_email tool via API")
                logger.info(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                logger.error(f"❌ Failed to sync send_email tool: HTTP {response.status_code}")
                logger.error(f"   Response: {response.text}")
                
        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to MCP Gateway at {MCP_GATEWAY_URL}")
            logger.error("   Please make sure the MCP Gateway service is running")
        except Exception as e:
            logger.error(f"❌ Error syncing send_email tool: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(sync_send_email_tool())


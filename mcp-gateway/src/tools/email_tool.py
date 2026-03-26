"""
邮件发送工具
提供发送电子邮件的功能，支持文本和HTML格式
"""
from typing import Dict, Any, List, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os

from ..models.tool_models import ToolDefinition, ToolType, ToolStatus
from ..config import settings

logger = logging.getLogger(__name__)

# 配置中心客户端（可选）
_config_client = None

def _get_config_client():
    """获取配置中心客户端（延迟初始化）"""
    global _config_client
    if _config_client is None:
        try:
            from luminaos_common.clients.config_client import get_config_client
            _config_client = get_config_client()
        except ImportError:
            logger.warning("Config client not available, using environment variables")
    return _config_client

async def _get_smtp_config():
    """从配置中心或环境变量获取SMTP配置"""
    config_client = _get_config_client()
    
    # 优先从配置中心读取
    if config_client:
        try:
            smtp_config = {
                "server": await config_client.get_config("smtp.server", "default"),
                "port": await config_client.get_config("smtp.port", "default"),
                "username": await config_client.get_config("smtp.username", "default"),
                "password": await config_client.get_config("smtp.password", "default"),
                "from_email": await config_client.get_config("smtp.from_email", "default"),
                "use_tls": await config_client.get_config("smtp.use_tls", "default"),
                "use_ssl": await config_client.get_config("smtp.use_ssl", "default"),
            }
            
            # 如果配置中心有值，使用配置中心的值
            if smtp_config["server"]:
                logger.info("Using SMTP config from config center")
                return smtp_config
        except Exception as e:
            logger.warning(f"Failed to get SMTP config from config center: {e}, falling back to environment variables")
    
    # 降级到环境变量或配置文件
    logger.info("Using SMTP config from environment variables or settings")
    return {
        "server": os.getenv("SMTP_SERVER", getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')),
        "port": int(os.getenv("SMTP_PORT", str(getattr(settings, 'SMTP_PORT', 587)))),
        "username": os.getenv("SMTP_USERNAME", getattr(settings, 'SMTP_USERNAME', '')),
        "password": os.getenv("SMTP_PASSWORD", getattr(settings, 'SMTP_PASSWORD', '')),
        "from_email": os.getenv("SMTP_FROM_EMAIL", getattr(settings, 'SMTP_FROM_EMAIL', '')),
        "use_tls": os.getenv("SMTP_USE_TLS", getattr(settings, 'SMTP_USE_TLS', 'true')).lower() == 'true',
        "use_ssl": os.getenv("SMTP_USE_SSL", getattr(settings, 'SMTP_USE_SSL', 'false')).lower() == 'true',
    }


async def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    body_type: str = "text",
    from_email: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    bcc_emails: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    reply_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送电子邮件
    
    Args:
        to_emails: 收件人邮箱列表（必需）
        subject: 邮件主题（必需）
        body: 邮件正文（必需）
        body_type: 正文类型（text/html，默认text）
        from_email: 发件人邮箱（可选，默认使用配置的发件人）
        cc_emails: 抄送邮箱列表（可选）
        bcc_emails: 密送邮箱列表（可选）
        attachments: 附件列表（可选），格式：[{"filename": "file.txt", "content": b"...", "content_type": "text/plain"}]
        reply_to: 回复邮箱（可选）
    
    Returns:
        发送结果
    """
    try:
        # 验证必需参数
        if not to_emails:
            raise ValueError("收件人邮箱列表不能为空")
        if not subject:
            raise ValueError("邮件主题不能为空")
        if not body:
            raise ValueError("邮件正文不能为空")
        
        # 从配置中心或环境变量获取SMTP配置
        smtp_config = await _get_smtp_config()
        
        # 验证SMTP配置
        if not smtp_config.get("server"):
            raise ValueError("SMTP服务器未配置")
        if not smtp_config.get("username"):
            raise ValueError("SMTP用户名未配置")
        if not smtp_config.get("password"):
            raise ValueError("SMTP密码未配置")
        
        # 使用配置的发件人邮箱
        sender_email = from_email or smtp_config.get("from_email") or smtp_config.get("username")
        
        # 创建邮件消息
        if body_type == "html" or attachments:
            msg = MIMEMultipart('alternative')
        else:
            msg = MIMEText(body, body_type, 'utf-8')
            msg = MIMEMultipart()
            msg.attach(MIMEText(body, body_type, 'utf-8'))
        
        # 设置邮件头
        msg['From'] = sender_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        if reply_to:
            msg['Reply-To'] = reply_to
        
        # 添加附件
        if attachments:
            for attachment in attachments:
                filename = attachment.get('filename', 'attachment')
                content = attachment.get('content')
                content_type = attachment.get('content_type', 'application/octet-stream')
                
                if content:
                    part = MIMEBase('application', 'octet-stream')
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
        
        # 构建收件人列表（包括抄送和密送）
        recipients = to_emails.copy()
        if cc_emails:
            recipients.extend(cc_emails)
        if bcc_emails:
            recipients.extend(bcc_emails)
        
        # 发送邮件
        smtp_server = smtp_config.get("server")
        smtp_port = smtp_config.get("port")
        smtp_username = smtp_config.get("username")
        smtp_password = smtp_config.get("password")
        smtp_use_ssl = smtp_config.get("use_ssl", False)
        smtp_use_tls = smtp_config.get("use_tls", False)
        
        logger.info(f"Sending email to {len(recipients)} recipients via {smtp_server}:{smtp_port}")
        
        if smtp_use_ssl:
            # 使用SSL连接
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # 使用TLS连接
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_use_tls:
                server.starttls()
        
        # 登录
        server.login(smtp_username, smtp_password)
        
        # 发送
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {', '.join(to_emails)}")
        
        return {
            "success": True,
            "message": "邮件发送成功",
            "to": to_emails,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "recipient_count": len(recipients)
        }
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"SMTP认证失败: {str(e)}",
            "error_code": "SMTP_AUTH_ERROR"
        }
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"SMTP错误: {str(e)}",
            "error_code": "SMTP_ERROR"
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"发送邮件时发生错误: {str(e)}",
            "error_code": "EMAIL_SEND_ERROR"
        }


async def execute_send_email(parameters: Dict[str, Any]) -> Any:
    """
    执行邮件发送工具
    
    Args:
        parameters: 工具参数
            - to_emails: 收件人邮箱列表（必需，字符串或列表）
            - subject: 邮件主题（必需）
            - body: 邮件正文（必需）
            - body_type: 正文类型（text/html，默认text）
            - from_email: 发件人邮箱（可选）
            - cc_emails: 抄送邮箱列表（可选，字符串或列表）
            - bcc_emails: 密送邮箱列表（可选，字符串或列表）
            - attachments: 附件列表（可选）
            - reply_to: 回复邮箱（可选）
    
    Returns:
        发送结果
    """
    # 解析收件人邮箱
    to_emails_param = parameters.get("to_emails")
    if isinstance(to_emails_param, str):
        # 如果是字符串，按逗号或分号分割
        to_emails = [email.strip() for email in to_emails_param.replace(';', ',').split(',') if email.strip()]
    elif isinstance(to_emails_param, list):
        to_emails = [str(email).strip() for email in to_emails_param if email]
    else:
        raise ValueError("to_emails参数必须是字符串或列表")
    
    # 解析抄送邮箱
    cc_emails = None
    cc_emails_param = parameters.get("cc_emails")
    if cc_emails_param:
        if isinstance(cc_emails_param, str):
            cc_emails = [email.strip() for email in cc_emails_param.replace(';', ',').split(',') if email.strip()]
        elif isinstance(cc_emails_param, list):
            cc_emails = [str(email).strip() for email in cc_emails_param if email]
    
    # 解析密送邮箱
    bcc_emails = None
    bcc_emails_param = parameters.get("bcc_emails")
    if bcc_emails_param:
        if isinstance(bcc_emails_param, str):
            bcc_emails = [email.strip() for email in bcc_emails_param.replace(';', ',').split(',') if email.strip()]
        elif isinstance(bcc_emails_param, list):
            bcc_emails = [str(email).strip() for email in bcc_emails_param if email]
    
    # 获取其他参数
    subject = parameters.get("subject", "")
    body = parameters.get("body", "")
    body_type = parameters.get("body_type", "text")
    from_email = parameters.get("from_email")
    attachments = parameters.get("attachments")
    reply_to = parameters.get("reply_to")
    
    # 验证必需参数
    if not to_emails:
        raise ValueError("收件人邮箱列表不能为空")
    if not subject:
        raise ValueError("邮件主题不能为空")
    if not body:
        raise ValueError("邮件正文不能为空")
    
    # 发送邮件
    return await send_email(
        to_emails=to_emails,
        subject=subject,
        body=body,
        body_type=body_type,
        from_email=from_email,
        cc_emails=cc_emails,
        bcc_emails=bcc_emails,
        attachments=attachments,
        reply_to=reply_to
    )


# 工具定义
SEND_EMAIL_TOOL = ToolDefinition(
    name="send_email",
    description="发送电子邮件。支持文本和HTML格式，可以添加附件、抄送和密送。需要配置SMTP服务器信息。",
    version="1.0.0",
    tool_type=ToolType.FUNCTION,
    status=ToolStatus.ACTIVE,
    parameters={
        "type": "object",
        "properties": {
            "to_emails": {
                "type": ["string", "array"],
                "description": "收件人邮箱地址（必需）。可以是字符串（多个邮箱用逗号或分号分隔）或数组",
                "items": {
                    "type": "string",
                    "format": "email"
                },
                "examples": [
                    "user@example.com",
                    "user1@example.com,user2@example.com",
                    ["user1@example.com", "user2@example.com"]
                ]
            },
            "subject": {
                "type": "string",
                "description": "邮件主题（必需）",
                "minLength": 1,
                "maxLength": 200
            },
            "body": {
                "type": "string",
                "description": "邮件正文内容（必需）",
                "minLength": 1
            },
            "body_type": {
                "type": "string",
                "description": "正文类型：text（纯文本）或html（HTML格式）",
                "enum": ["text", "html"],
                "default": "text"
            },
            "from_email": {
                "type": "string",
                "description": "发件人邮箱地址（可选，默认使用配置的发件人）",
                "format": "email"
            },
            "cc_emails": {
                "type": ["string", "array"],
                "description": "抄送邮箱地址（可选）。可以是字符串（多个邮箱用逗号或分号分隔）或数组",
                "items": {
                    "type": "string",
                    "format": "email"
                }
            },
            "bcc_emails": {
                "type": ["string", "array"],
                "description": "密送邮箱地址（可选）。可以是字符串（多个邮箱用逗号或分号分隔）或数组",
                "items": {
                    "type": "string",
                    "format": "email"
                }
            },
            "attachments": {
                "type": "array",
                "description": "附件列表（可选）。每个附件包含filename（文件名）、content（内容，base64编码或字节）和content_type（内容类型）",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "附件文件名"
                        },
                        "content": {
                            "type": ["string", "object"],
                            "description": "附件内容（字符串或base64编码）"
                        },
                        "content_type": {
                            "type": "string",
                            "description": "附件内容类型（如：text/plain, application/pdf等）",
                            "default": "application/octet-stream"
                        }
                    },
                    "required": ["filename", "content"]
                }
            },
            "reply_to": {
                "type": "string",
                "description": "回复邮箱地址（可选）",
                "format": "email"
            }
        },
        "required": ["to_emails", "subject", "body"]
    },
    required_parameters=["to_emails", "subject", "body"],
    returns={
        "type": "object",
        "properties": {
            "success": {
                "type": "boolean",
                "description": "是否发送成功"
            },
            "message": {
                "type": "string",
                "description": "结果消息"
            },
            "to": {
                "type": "array",
                "items": {"type": "string"},
                "description": "收件人列表"
            },
            "subject": {
                "type": "string",
                "description": "邮件主题"
            },
            "sent_at": {
                "type": "string",
                "format": "date-time",
                "description": "发送时间"
            },
            "recipient_count": {
                "type": "integer",
                "description": "收件人总数（包括抄送和密送）"
            },
            "error": {
                "type": "string",
                "description": "错误信息（如果发送失败）"
            },
            "error_code": {
                "type": "string",
                "description": "错误代码（如果发送失败）"
            }
        }
    },
    metadata={
        "category": "communication",
        "author": "system",
        "service": "mcp-gateway",
        "requires_config": {
            "SMTP_SERVER": "SMTP服务器地址",
            "SMTP_PORT": "SMTP端口（默认587）",
            "SMTP_USERNAME": "SMTP用户名",
            "SMTP_PASSWORD": "SMTP密码",
            "SMTP_FROM_EMAIL": "默认发件人邮箱（可选）",
            "SMTP_USE_TLS": "是否使用TLS（默认true）",
            "SMTP_USE_SSL": "是否使用SSL（默认false）"
        }
    }
)


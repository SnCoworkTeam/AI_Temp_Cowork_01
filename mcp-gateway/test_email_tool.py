"""
测试邮件发送工具
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

# 设置环境变量（163邮箱配置）
os.environ["SMTP_SERVER"] = "smtp.163.com"
os.environ["SMTP_PORT"] = "465"  # 163邮箱使用SSL端口
os.environ["SMTP_USERNAME"] = "lyb-005@163.com"
os.environ["SMTP_PASSWORD"] = "Liu@bner1983"
os.environ["SMTP_FROM_EMAIL"] = "lyb-005@163.com"
os.environ["SMTP_USE_TLS"] = "false"
os.environ["SMTP_USE_SSL"] = "true"  # 163邮箱使用SSL

async def test_send_email():
    """测试发送邮件"""
    try:
        from src.tools.email_tool import execute_send_email
        
        print("=" * 60)
        print("测试邮件发送工具")
        print("=" * 60)
        print(f"发件人: lyb-005@163.com")
        print(f"收件人: yubin.liu@pcitc.com")
        print(f"SMTP服务器: smtp.163.com:465 (SSL)")
        print()
        
        # 测试参数
        parameters = {
            "to_emails": "yubin.liu@pcitc.com",
            "subject": "测试邮件 - MCP工具测试",
            "body": f"""这是一封测试邮件，用于验证MCP邮件发送工具的功能。

邮件内容：
- 发件人：lyb-005@163.com
- 收件人：yubin.liu@pcitc.com
- 发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果您收到这封邮件，说明邮件发送工具配置成功！

此邮件由企业AI平台的MCP工具自动发送。
""",
            "body_type": "text"
        }
        
        print("正在发送邮件...")
        result = await execute_send_email(parameters)
        
        print()
        print("=" * 60)
        print("发送结果")
        print("=" * 60)
        
        if result.get("success"):
            print("✅ 邮件发送成功！")
            print(f"   收件人: {', '.join(result.get('to', []))}")
            print(f"   主题: {result.get('subject')}")
            print(f"   发送时间: {result.get('sent_at')}")
            print(f"   收件人总数: {result.get('recipient_count')}")
        else:
            print("❌ 邮件发送失败！")
            print(f"   错误: {result.get('error')}")
            print(f"   错误代码: {result.get('error_code')}")
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_send_email())
    sys.exit(0 if success else 1)


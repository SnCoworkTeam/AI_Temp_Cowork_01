"""
简单邮件发送测试脚本
直接测试163邮箱发送功能
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_send_email():
    """测试发送邮件"""
    print("=" * 60)
    print("测试163邮箱邮件发送")
    print("=" * 60)
    
    # 163邮箱SMTP配置
    smtp_server = "smtp.163.com"
    smtp_port = 465  # 163邮箱SSL端口
    username = "lyb-005@163.com"
    password = "Liu@bner1983"
    from_email = "lyb-005@163.com"
    to_email = "yubin.liu@pcitc.com"
    
    print(f"SMTP服务器: {smtp_server}:{smtp_port}")
    print(f"发件人: {from_email}")
    print(f"收件人: {to_email}")
    print()
    
    try:
        # 创建邮件消息
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "测试邮件 - MCP工具测试"
        
        # 邮件正文
        body = f"""这是一封测试邮件，用于验证MCP邮件发送工具的功能。

邮件信息：
- 发件人：{from_email}
- 收件人：{to_email}
- 发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果您收到这封邮件，说明邮件发送工具配置成功！

此邮件由企业AI平台的MCP工具自动发送。
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print("正在连接SMTP服务器...")
        # 使用SSL连接
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        
        print("正在登录...")
        server.login(username, password)
        
        print("正在发送邮件...")
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        
        print()
        print("=" * 60)
        print("✅ 邮件发送成功！")
        print("=" * 60)
        print(f"收件人: {to_email}")
        print(f"主题: 测试邮件 - MCP工具测试")
        print(f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print()
        print("=" * 60)
        print("❌ SMTP认证失败")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        print()
        print("可能的原因：")
        print("1. 用户名或密码错误")
        print("2. 163邮箱需要开启SMTP服务")
        print("3. 需要使用授权码而不是登录密码")
        print("   请登录163邮箱 -> 设置 -> POP3/SMTP/IMAP -> 开启SMTP服务并获取授权码")
        return False
        
    except smtplib.SMTPException as e:
        print()
        print("=" * 60)
        print("❌ SMTP错误")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        return False
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 发送邮件时发生错误")
        print("=" * 60)
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_send_email()
    exit(0 if success else 1)



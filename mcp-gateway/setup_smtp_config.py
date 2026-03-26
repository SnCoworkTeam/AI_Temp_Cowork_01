"""
将SMTP配置添加到配置中心
"""
import asyncio
import httpx
import os
import sys

CONFIG_CENTER_URL = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")

# 163邮箱SMTP配置
SMTP_CONFIGS = [
    {
        "key": "smtp.server",
        "value": "smtp.163.com",
        "description": "SMTP服务器地址（163邮箱）"
    },
    {
        "key": "smtp.port",
        "value": 465,
        "description": "SMTP端口（163邮箱使用SSL，端口465）"
    },
    {
        "key": "smtp.username",
        "value": "lyb-005@163.com",
        "description": "SMTP用户名（163邮箱地址）"
    },
    {
        "key": "smtp.password",
        "value": "Liu@bner1983",
        "description": "SMTP密码（163邮箱密码）"
    },
    {
        "key": "smtp.from_email",
        "value": "lyb-005@163.com",
        "description": "默认发件人邮箱地址"
    },
    {
        "key": "smtp.use_tls",
        "value": False,
        "description": "是否使用TLS（163邮箱使用SSL，不需要TLS）"
    },
    {
        "key": "smtp.use_ssl",
        "value": True,
        "description": "是否使用SSL（163邮箱使用SSL）"
    }
]


async def setup_smtp_config():
    """将SMTP配置添加到配置中心"""
    print("=" * 60)
    print("配置SMTP邮件设置到配置中心")
    print("=" * 60)
    print(f"配置中心URL: {CONFIG_CENTER_URL}")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 检查配置中心是否可用
        try:
            response = await client.get(f"{CONFIG_CENTER_URL}/health")
            if response.status_code != 200:
                print(f"❌ 配置中心不可用: {response.status_code}")
                return False
            print("✅ 配置中心连接正常")
            print()
        except Exception as e:
            print(f"❌ 无法连接到配置中心: {e}")
            print("   请确保配置中心服务正在运行")
            return False
        
        # 添加每个配置项
        success_count = 0
        for config in SMTP_CONFIGS:
            try:
                config_item = {
                    "key": config["key"],
                    "value": config["value"],
                    "description": config["description"],
                    "environment": "default"
                }
                
                response = await client.post(
                    f"{CONFIG_CENTER_URL}/api/config",
                    json=config_item
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 配置已添加: {config['key']} = {config['value']} (版本: {result.get('version', 1)})")
                    success_count += 1
                else:
                    print(f"⚠️  配置添加失败: {config['key']} - {response.status_code}: {response.text}")
            except Exception as e:
                print(f"❌ 配置添加错误: {config['key']} - {str(e)}")
        
        print()
        print("=" * 60)
        if success_count == len(SMTP_CONFIGS):
            print(f"✅ 所有SMTP配置已成功添加到配置中心 ({success_count}/{len(SMTP_CONFIGS)})")
            return True
        else:
            print(f"⚠️  部分配置添加成功 ({success_count}/{len(SMTP_CONFIGS)})")
            return False


if __name__ == "__main__":
    success = asyncio.run(setup_smtp_config())
    sys.exit(0 if success else 1)



#!/usr/bin/env python3
"""
添加SAP配置到配置中心
"""
import httpx
import json
import sys
import os

# 配置中心URL
CONFIG_CENTER_URL = os.getenv("CONFIG_CENTER_URL", "http://localhost:8090")
ENVIRONMENT = "default"

# SAP配置项（请根据实际情况修改）
SAP_CONFIGS = {
    "sap.base_url": {
        "value": "",  # 请填写SAP系统的基础URL，例如: https://your-sap-system.com
        "description": "SAP系统的基础URL"
    },
    "sap.username": {
        "value": "",  # 请填写SAP用户名
        "description": "SAP用户名"
    },
    "sap.password": {
        "value": "",  # 请填写SAP密码
        "description": "SAP密码"
    },
    "sap.client": {
        "value": "100",  # SAP客户端，默认100
        "description": "SAP客户端编号"
    },
    "sap.language": {
        "value": "EN",  # 语言，默认EN
        "description": "SAP系统语言"
    },
    "sap.timeout": {
        "value": 300000,  # 超时时间（毫秒），默认5分钟
        "description": "SAP请求超时时间（毫秒）"
    },
    "sap.max_retries": {
        "value": 3,  # 最大重试次数
        "description": "SAP请求最大重试次数"
    },
    "sap.page_size": {
        "value": 1000,  # 分页大小
        "description": "SAP查询分页大小"
    },
    "sap.max_records": {
        "value": 10000,  # 最大记录数
        "description": "SAP查询最大记录数"
    }
}


async def add_config(key: str, value: Any, description: str = None):
    """添加配置到配置中心"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        config_item = {
            "key": key,
            "value": value,
            "description": description,
            "environment": ENVIRONMENT
        }
        
        try:
            response = await client.post(
                f"{CONFIG_CENTER_URL}/api/config",
                json=config_item
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ 配置已添加: {key} (版本: {result.get('version', 1)})")
            return True
        except httpx.HTTPStatusError as e:
            print(f"❌ 添加配置失败 {key}: HTTP {e.response.status_code}")
            print(f"   响应: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ 添加配置失败 {key}: {str(e)}")
            return False


async def main():
    """主函数"""
    print(f"正在连接到配置中心: {CONFIG_CENTER_URL}")
    print(f"环境: {ENVIRONMENT}")
    print("-" * 60)
    
    # 检查必需配置是否已填写
    required_configs = ["sap.base_url", "sap.username", "sap.password"]
    missing_configs = []
    
    for key in required_configs:
        if not SAP_CONFIGS[key]["value"]:
            missing_configs.append(key)
    
    if missing_configs:
        print("⚠️  警告: 以下必需配置项未填写:")
        for key in missing_configs:
            print(f"   - {key}")
        print("\n请修改脚本中的配置值后再运行。")
        print("或者通过命令行参数传递配置值。")
        return
    
    # 添加所有配置
    success_count = 0
    fail_count = 0
    
    for key, config in SAP_CONFIGS.items():
        success = await add_config(
            key=key,
            value=config["value"],
            description=config["description"]
        )
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    print("-" * 60)
    print(f"完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    
    if success_count > 0:
        print("\n✅ SAP配置已添加到配置中心")
        print("   请重启 sap-mcp-server 服务以使配置生效")


if __name__ == "__main__":
    import asyncio
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 支持从命令行传递配置
        # 格式: python add_sap_config.py base_url=xxx username=xxx password=xxx
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                if key == "base_url":
                    SAP_CONFIGS["sap.base_url"]["value"] = value
                elif key == "username":
                    SAP_CONFIGS["sap.username"]["value"] = value
                elif key == "password":
                    SAP_CONFIGS["sap.password"]["value"] = value
                elif key == "client":
                    SAP_CONFIGS["sap.client"]["value"] = value
    
    asyncio.run(main())

































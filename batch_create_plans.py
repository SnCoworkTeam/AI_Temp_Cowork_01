#!/usr/bin/env python3
"""
批量创建项目计划脚本
"""
import urllib.request
import urllib.parse
import json
import sys

# API配置
BASE_URL = "http://localhost:8080"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
BATCH_CREATE_URL = f"{BASE_URL}/api/v1/projects/batch-create-plans"

# 登录凭据
LOGIN_DATA = {
    "username": "admin",
    "password": "admin123"
}

def make_request(url, method="GET", data=None, headers=None):
    """发送HTTP请求"""
    if headers is None:
        headers = {}

    if data:
        data = json.dumps(data).encode('utf-8')
        headers.setdefault('Content-Type', 'application/json')

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            response_data = response.read().decode('utf-8')
            return response.status, json.loads(response_data) if response_data else {}
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        try:
            return e.code, json.loads(error_data)
        except:
            return e.code, {"error": error_data}
    except Exception as e:
        return None, {"error": str(e)}

def main():
    print("=" * 60)
    print("批量创建项目计划")
    print("=" * 60)

    # 步骤1: 登录获取token
    print("\n[1/2] 正在登录...")
    status, login_data = make_request(LOGIN_URL, method="POST", data=LOGIN_DATA)

    if status != 200:
        print(f"❌ 登录失败 (HTTP {status}): {login_data}")
        return

    if not login_data.get("success"):
        print(f"❌ 登录失败: {login_data.get('error', {}).get('message', '未知错误')}")
        return

    access_token = login_data.get("access_token")
    if not access_token:
        print("❌ 登录成功但未获取到access_token")
        return

    print(f"✅ 登录成功")
    print(f"Token: {access_token[:50]}...")

    # 步骤2: 调用批量创建计划API
    print("\n[2/2] 正在调用批量创建计划API...")
    print("这可能需要几分钟时间，请耐心等待...")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    status, result = make_request(BATCH_CREATE_URL, method="POST", headers=headers)

    if status == 200:
        print("\n" + "=" * 60)
        print("✅ API调用成功！")
        print("=" * 60)
        print("\n结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n" + "=" * 60)

        # 显示摘要
        if isinstance(result, dict):
            print("\n摘要:")
            print(f"  - 处理项目数: {result.get('processed', 0)}")
            print(f"  - 创建计划数: {result.get('created_plans', 0)}")
            print(f"  - 创建阶段数: {result.get('created_phases', 0)}")
    else:
        print(f"\n❌ API调用失败 (HTTP {status})")
        print(f"错误详情: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    main()


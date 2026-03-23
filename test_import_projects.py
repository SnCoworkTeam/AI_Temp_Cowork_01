#!/usr/bin/env python3
"""测试项目导入功能"""
import requests
import json

# 配置
API_BASE = "http://43.143.139.197:8080"
EXCEL_FILE = "/tmp/projects.xlsx"

# 1. 先登录获取token
print("=== 步骤1: 登录获取token ===")
login_resp = requests.post(
    f"{API_BASE}/api/auth/login",
    json={"username": "admin", "password": "admin"}
)

if login_resp.status_code == 200:
    token = login_resp.json().get("access_token")
    print(f"✓ 登录成功，获取到token")
else:
    print(f"✗ 登录失败: {login_resp.status_code} - {login_resp.text}")
    token = None

# 2. 上传Excel文件导入项目
print("\n=== 步骤2: 上传Excel导入项目 ===")

if token:
    headers = {"Authorization": f"Bearer {token}"}

    with open(EXCEL_FILE, 'rb') as f:
        files = {'file': ('projects.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        import_resp = requests.post(
            f"{API_BASE}/api/v1/projects/import/excel",
            files=files,
            headers=headers
        )

        print(f"状态码: {import_resp.status_code}")
        print(f"响应: {json.dumps(import_resp.json(), indent=2, ensure_ascii=False)}")
else:
    print("✗ 跳过导入，因为没有token")

# 3. 查看导入的项目
print("\n=== 步骤3: 查看导入的项目 ===")
projects_resp = requests.get(f"{API_BASE}/api/v1/projects")
print(f"状态码: {projects_resp.status_code}")
if projects_resp.status_code == 200:
    data = projects_resp.json()
    print(f"总项目数: {data.get('total')}")
    print(f"前5个项目:")
    for proj in data.get('items', [])[:5]:
        print(f"  - {proj['name']} ({proj['project_code']})")
else:
    print(f"响应: {projects_resp.text}")

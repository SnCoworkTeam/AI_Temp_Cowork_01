#!/usr/bin/env python3
"""
将数据库中的权限同步到Redis
通过auth-service的API创建权限，这样会自动存储到Redis
"""
import requests
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API配置
API_BASE_URL = os.getenv('API_GATEWAY_URL', 'http://43.143.139.197:8080')
AUTH_URL = f"{API_BASE_URL}/api/auth/login"

# 默认管理员账号（需要根据实际情况修改）
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def get_auth_token():
    """获取认证token"""
    try:
        response = requests.post(AUTH_URL, json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"获取token失败: {str(e)}")
        return None

def get_permissions_from_db():
    """从数据库获取权限列表（通过API）"""
    # 这里我们需要通过SQL直接查询数据库
    # 但由于我们无法直接访问数据库，我们通过API创建权限
    # 实际上，我们应该创建一个脚本来读取数据库并创建权限
    pass

def create_permission_via_api(token, permission_data):
    """通过API创建权限"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}/api/auth/admin/permissions"
    
    try:
        response = requests.post(url, json=permission_data, headers=headers)
        if response.status_code == 201:
            print(f"  ✓ 创建权限: {permission_data['code']} - {permission_data['name']}")
            return True
        elif response.status_code == 400:
            # 可能是权限已存在
            error_msg = response.json().get('detail', '')
            if 'already exists' in error_msg.lower() or '已存在' in error_msg:
                print(f"  - 权限已存在: {permission_data['code']}")
                return True
            else:
                print(f"  ✗ 创建失败: {permission_data['code']} - {error_msg}")
                return False
        else:
            print(f"  ✗ 创建失败: {permission_data['code']} - {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ 创建失败: {permission_data['code']} - {str(e)}")
        return False

# 默认权限列表（与init_permissions_roles.py中的一致）
DEFAULT_PERMISSIONS = [
    # 用户管理权限
    {'code': 'user:read', 'name': '查看用户', 'resource_type': 'user', 'permission_type': 'read', 'description': '查看用户信息'},
    {'code': 'user:create', 'name': '创建用户', 'resource_type': 'user', 'permission_type': 'write', 'description': '创建新用户'},
    {'code': 'user:update', 'name': '更新用户', 'resource_type': 'user', 'permission_type': 'write', 'description': '更新用户信息'},
    {'code': 'user:delete', 'name': '删除用户', 'resource_type': 'user', 'permission_type': 'delete', 'description': '删除用户'},
    
    # 角色管理权限
    {'code': 'role:read', 'name': '查看角色', 'resource_type': 'admin', 'permission_type': 'read', 'description': '查看角色信息'},
    {'code': 'role:create', 'name': '创建角色', 'resource_type': 'admin', 'permission_type': 'write', 'description': '创建新角色'},
    {'code': 'role:update', 'name': '更新角色', 'resource_type': 'admin', 'permission_type': 'write', 'description': '更新角色信息'},
    {'code': 'role:delete', 'name': '删除角色', 'resource_type': 'admin', 'permission_type': 'delete', 'description': '删除角色'},
    
    # 权限管理权限
    {'code': 'permission:read', 'name': '查看权限', 'resource_type': 'admin', 'permission_type': 'read', 'description': '查看权限信息'},
    {'code': 'permission:create', 'name': '创建权限', 'resource_type': 'admin', 'permission_type': 'write', 'description': '创建新权限'},
    {'code': 'permission:update', 'name': '更新权限', 'resource_type': 'admin', 'permission_type': 'write', 'description': '更新权限信息'},
    {'code': 'permission:delete', 'name': '删除权限', 'resource_type': 'admin', 'permission_type': 'delete', 'description': '删除权限'},
    
    # 项目管理权限
    {'code': 'project:read', 'name': '查看项目', 'resource_type': 'user', 'permission_type': 'read', 'description': '查看项目信息'},
    {'code': 'project:create', 'name': '创建项目', 'resource_type': 'user', 'permission_type': 'write', 'description': '创建新项目'},
    {'code': 'project:update', 'name': '更新项目', 'resource_type': 'user', 'permission_type': 'write', 'description': '更新项目信息'},
    {'code': 'project:delete', 'name': '删除项目', 'resource_type': 'user', 'permission_type': 'delete', 'description': '删除项目'},
    
    # 工作流权限
    {'code': 'workflow:read', 'name': '查看工作流', 'resource_type': 'workflow', 'permission_type': 'read', 'description': '查看工作流信息'},
    {'code': 'workflow:create', 'name': '创建工作流', 'resource_type': 'workflow', 'permission_type': 'write', 'description': '创建新工作流'},
    {'code': 'workflow:update', 'name': '更新工作流', 'resource_type': 'workflow', 'permission_type': 'write', 'description': '更新工作流信息'},
    {'code': 'workflow:delete', 'name': '删除工作流', 'resource_type': 'workflow', 'permission_type': 'delete', 'description': '删除工作流'},
    {'code': 'workflow:execute', 'name': '执行工作流', 'resource_type': 'workflow', 'permission_type': 'execute', 'description': '执行工作流'},
    
    # 知识库权限
    {'code': 'knowledge:read', 'name': '查看知识库', 'resource_type': 'user', 'permission_type': 'read', 'description': '查看知识库信息'},
    {'code': 'knowledge:create', 'name': '创建知识库', 'resource_type': 'user', 'permission_type': 'write', 'description': '创建新知识库'},
    {'code': 'knowledge:update', 'name': '更新知识库', 'resource_type': 'user', 'permission_type': 'write', 'description': '更新知识库信息'},
    {'code': 'knowledge:delete', 'name': '删除知识库', 'resource_type': 'user', 'permission_type': 'delete', 'description': '删除知识库'},
    
    # 工具权限
    {'code': 'tool:read', 'name': '查看工具', 'resource_type': 'tool', 'permission_type': 'read', 'description': '查看工具信息'},
    {'code': 'tool:create', 'name': '创建工具', 'resource_type': 'tool', 'permission_type': 'write', 'description': '创建新工具'},
    {'code': 'tool:update', 'name': '更新工具', 'resource_type': 'tool', 'permission_type': 'write', 'description': '更新工具信息'},
    {'code': 'tool:delete', 'name': '删除工具', 'resource_type': 'tool', 'permission_type': 'delete', 'description': '删除工具'},
    {'code': 'tool:execute', 'name': '执行工具', 'resource_type': 'tool', 'permission_type': 'execute', 'description': '执行工具'},
    
    # 系统权限
    {'code': 'system:read', 'name': '查看系统', 'resource_type': 'system', 'permission_type': 'read', 'description': '查看系统信息'},
    {'code': 'system:update', 'name': '更新系统', 'resource_type': 'system', 'permission_type': 'write', 'description': '更新系统配置'},
    {'code': 'system:monitor', 'name': '监控系统', 'resource_type': 'system', 'permission_type': 'read', 'description': '监控系统状态'},
]

def main():
    print("=" * 60)
    print("权限同步到Redis脚本")
    print("=" * 60)
    
    # 获取认证token
    print("\n正在获取认证token...")
    token = get_auth_token()
    if not token:
        print("✗ 无法获取认证token，请检查管理员账号和密码")
        sys.exit(1)
    print("✓ 认证成功")
    
    # 创建权限
    print(f"\n开始创建权限（共 {len(DEFAULT_PERMISSIONS)} 个）...")
    success_count = 0
    for perm_data in DEFAULT_PERMISSIONS:
        if create_permission_via_api(token, perm_data):
            success_count += 1
    
    print(f"\n权限创建完成: {success_count}/{len(DEFAULT_PERMISSIONS)}")
    print("\n✓ 权限同步完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()


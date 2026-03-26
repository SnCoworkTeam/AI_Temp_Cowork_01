#!/usr/bin/env python3
"""
在auth-service容器内运行的权限同步脚本
从数据库读取权限并同步到Redis
"""
import asyncio
import sys
import os

# 添加auth-service的src目录到Python路径
sys.path.insert(0, '/app')

from src.services.permission_service import PermissionService
from src.models.permission_models import ResourceType, PermissionType
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# 数据库连接（使用环境变量）
DB_HOST = os.getenv('DB_HOST', 'enterprise-ai-postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'ai_platform')
DB_USER = os.getenv('DB_USER', 'ai_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ai_password')

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 资源类型映射
RESOURCE_TYPE_MAP = {
    'user': ResourceType.USER,
    'role': ResourceType.ADMIN,
    'permission': ResourceType.ADMIN,
    'project': ResourceType.USER,
    'workflow': ResourceType.WORKFLOW,
    'knowledge': ResourceType.USER,
    'tool': ResourceType.TOOL,
    'system': ResourceType.SYSTEM,
}

# 权限类型映射
PERMISSION_TYPE_MAP = {
    'read': PermissionType.READ,
    'create': PermissionType.WRITE,
    'write': PermissionType.WRITE,
    'update': PermissionType.WRITE,
    'delete': PermissionType.DELETE,
    'execute': PermissionType.EXECUTE,
    'monitor': PermissionType.READ,
    'admin': PermissionType.ADMIN,
}

async def sync_permissions():
    """同步权限从数据库到Redis"""
    print("=" * 60)
    print("权限同步脚本（数据库 -> Redis）")
    print("=" * 60)
    
    # 连接数据库
    print("\n连接数据库...")
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 从数据库读取权限
        print("从数据库读取权限...")
        result = db.execute(text("""
            SELECT code, name, resource, action, description 
            FROM permissions 
            WHERE code IS NOT NULL AND code != '' 
            ORDER BY code
        """))
        
        permissions = result.fetchall()
        print(f"找到 {len(permissions)} 个权限")
        
        if len(permissions) == 0:
            print("数据库中没有权限数据，请先运行 init_permissions_roles.py")
            return
        
        # 创建权限服务实例
        permission_service = PermissionService()
        
        # 同步每个权限
        print(f"\n开始同步权限到Redis...")
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for perm in permissions:
            code = perm.code
            name = perm.name
            resource = perm.resource or ''
            action = perm.action or ''
            description = perm.description or ''
            
            # 确定资源类型
            resource_type = ResourceType.USER  # 默认值
            if resource:
                # 从code中提取资源类型（如 user:read -> user）
                if ':' in code:
                    resource_from_code = code.split(':')[0]
                    resource_type = RESOURCE_TYPE_MAP.get(resource_from_code, ResourceType.USER)
                else:
                    resource_type = RESOURCE_TYPE_MAP.get(resource, ResourceType.USER)
            
            # 确定权限类型
            permission_type = PermissionType.READ  # 默认值
            if action:
                permission_type = PERMISSION_TYPE_MAP.get(action, PermissionType.READ)
            elif ':' in code:
                action_from_code = code.split(':')[1]
                permission_type = PERMISSION_TYPE_MAP.get(action_from_code, PermissionType.READ)
            
            try:
                # 检查权限是否已存在
                existing = await permission_service.get_permission_by_code(code)
                if existing:
                    print(f"  - 权限已存在: {code} - {name}")
                    skip_count += 1
                    continue
                
                # 创建权限
                permission_data = {
                    "name": name,
                    "code": code,
                    "resource_type": resource_type,
                    "permission_type": permission_type,
                    "description": description,
                }
                
                await permission_service.create_permission(permission_data)
                print(f"  ✓ 创建权限: {code} - {name}")
                success_count += 1
                
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"  - 权限已存在: {code}")
                    skip_count += 1
                else:
                    print(f"  ✗ 创建失败: {code} - {str(e)}")
                    error_count += 1
            except Exception as e:
                print(f"  ✗ 创建失败: {code} - {str(e)}")
                error_count += 1
        
        print(f"\n同步完成:")
        print(f"  ✓ 成功: {success_count}")
        print(f"  - 跳过: {skip_count}")
        print(f"  ✗ 失败: {error_count}")
        print(f"  总计: {len(permissions)}")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        engine.dispose()

if __name__ == '__main__':
    asyncio.run(sync_permissions())


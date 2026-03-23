#!/usr/bin/env python3
"""
创建测试用户账号脚本
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'auth-service', 'src'))
sys.path.insert(0, os.path.join(project_root, 'database', 'src'))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.src.core.database import get_db_session
from database.src.repositories.user_repository import UserRepository
from database.src.models.user_models import UserStatus, User
from uuid import uuid4
from datetime import datetime

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 定义要创建的用户列表
TEST_USERS = [
    {
        "username": "manager1",
        "email": "manager1@sinochem.com",
        "full_name": "项目经理1",
        "password": "Test@2025",
        "roles": ["user"]
    },
    {
        "username": "member1",
        "email": "member1@sinochem.com",
        "full_name": "项目成员1",
        "password": "Test@2025",
        "roles": ["user"]
    },
    {
        "username": "viewer1",
        "email": "viewer1@sinochem.com",
        "full_name": "查看者1",
        "password": "Test@2025",
        "roles": ["viewer"]
    },
    {
        "username": "developer1",
        "email": "developer1@sinochem.com",
        "full_name": "开发者1",
        "password": "Test@2025",
        "roles": ["developer"]
    },
    {
        "username": "testuser1",
        "email": "testuser1@sinochem.com",
        "full_name": "测试用户1",
        "password": "Test@2025",
        "roles": ["user"]
    },
    {
        "username": "testuser2",
        "email": "testuser2@sinochem.com",
        "full_name": "测试用户2",
        "password": "Test@2025",
        "roles": ["user"]
    },
]

def create_user(user_info: dict, db: Session) -> bool:
    """创建用户"""
    try:
        user_repo = UserRepository(db)
        
        # 检查用户是否已存在
        existing = user_repo.get_by_username(user_info["username"])
        if existing:
            print(f"⚠️  用户已存在: {user_info['username']}")
            return False
        
        # 检查邮箱是否已存在
        existing_email = user_repo.get_by_email(user_info["email"])
        if existing_email:
            print(f"⚠️  邮箱已存在: {user_info['email']}")
            return False
        
        # 加密密码
        password_hash = pwd_context.hash(user_info["password"])
        
        # 创建用户
        user = user_repo.create_user(
            username=user_info["username"],
            email=user_info["email"],
            password_hash=password_hash,
            full_name=user_info["full_name"],
            status=UserStatus.ACTIVE
        )
        
        db.commit()
        
        print(f"✅ 用户创建成功: {user_info['username']} (ID: {user.id})")
        
        # TODO: 分配角色（需要角色服务）
        # 这里暂时跳过角色分配，可以通过管理界面手动分配
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建用户失败: {user_info['username']} - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("创建测试用户账号")
    print("=" * 80)
    print("")
    
    try:
        db: Session = get_db_session()
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for user_info in TEST_USERS:
            result = create_user(user_info, db)
            if result:
                success_count += 1
            else:
                skip_count += 1
        
        db.close()
        
        print("")
        print("=" * 80)
        print("创建完成统计")
        print("=" * 80)
        print(f"✅ 成功: {success_count}")
        print(f"⚠️  跳过: {skip_count}")
        print(f"❌ 失败: {fail_count}")
        print("")
        
        print("测试账号信息:")
        print("=" * 80)
        for user_info in TEST_USERS:
            print(f"用户名: {user_info['username']} | 密码: {user_info['password']} | 角色: {', '.join(user_info['roles'])}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()



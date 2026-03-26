#!/usr/bin/env python3
"""
在容器内创建测试用户
"""
import sys
import os
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.core.database import SessionLocal, init_database
from src.repositories.user_repository import UserRepository
from database.src.models.user_models import UserStatus

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

test_users = [
    {'username': 'manager1', 'email': 'manager1@sinochem.com', 'full_name': '项目经理1', 'password': 'Test@2025'},
    {'username': 'member1', 'email': 'member1@sinochem.com', 'full_name': '项目成员1', 'password': 'Test@2025'},
    {'username': 'viewer1', 'email': 'viewer1@sinochem.com', 'full_name': '查看者1', 'password': 'Test@2025'},
    {'username': 'developer1', 'email': 'developer1@sinochem.com', 'full_name': '开发者1', 'password': 'Test@2025'},
    {'username': 'testuser1', 'email': 'testuser1@sinochem.com', 'full_name': '测试用户1', 'password': 'Test@2025'},
    {'username': 'testuser2', 'email': 'testuser2@sinochem.com', 'full_name': '测试用户2', 'password': 'Test@2025'},
]

print("=" * 80)
print("创建测试用户账号")
print("=" * 80)
print("")

# 初始化数据库
init_database()

db = SessionLocal()
user_repo = UserRepository(db)
success = 0
skip = 0
fail = 0

for user_info in test_users:
    try:
        existing = user_repo.get_by_username(user_info['username'])
        if existing:
            print(f"⚠️  用户已存在: {user_info['username']}")
            skip += 1
            continue
        
        existing_email = user_repo.get_by_email(user_info['email'])
        if existing_email:
            print(f"⚠️  邮箱已存在: {user_info['email']}")
            skip += 1
            continue
        
        password_hash = pwd_context.hash(user_info['password'])
        user = user_repo.create_user(
            username=user_info['username'],
            email=user_info['email'],
            password_hash=password_hash,
            full_name=user_info['full_name'],
            status='active'
        )
        db.commit()
        print(f"✅ 用户创建成功: {user_info['username']} (ID: {user.id})")
        success += 1
    except Exception as e:
        db.rollback()
        print(f"❌ 创建失败: {user_info['username']} - {str(e)}")
        fail += 1

db.close()

print("")
print("=" * 80)
print("创建完成统计")
print("=" * 80)
print(f"✅ 成功: {success}")
print(f"⚠️  跳过: {skip}")
print(f"❌ 失败: {fail}")
print("")
print("测试账号信息:")
print("=" * 80)
for user_info in test_users:
    print(f"用户名: {user_info['username']} | 密码: {user_info['password']}")
print("=" * 80)


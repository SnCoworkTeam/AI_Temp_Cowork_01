#!/usr/bin/env python3
"""
创建admin管理员账号
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'auth-service', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database', 'src'))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.src.core.database import get_db_session
from database.src.repositories.user_repository import UserRepository
from database.src.models.user_models import UserStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    """创建admin用户"""
    try:
        db: Session = get_db_session()
        try:
            user_repo = UserRepository(db)
            user = user_repo.get_by_username("admin")
            
            password_hash = pwd_context.hash("admin123456")
            
            if user:
                print(f"✅ admin用户已存在，更新密码...")
                user.password_hash = password_hash
                db.commit()
                print(f"✅ 密码已更新")
            else:
                print("创建admin用户...")
                from uuid import uuid4
                from datetime import datetime
                from database.src.models.user_models import User
                
                user = User(
                    id=uuid4(),
                    username="admin",
                    email="admin@example.com",
                    password_hash=password_hash,
                    full_name="系统管理员",
                    status=UserStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(user)
                db.commit()
                print(f"✅ admin用户已创建: {user.username} (ID: {user.id})")
            
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("创建admin管理员账号")
    print("=" * 50)
    if create_admin():
        print("\n✅ 成功！")
        print("用户名: admin")
        print("密码: admin123456")
    else:
        print("\n❌ 失败")
        sys.exit(1)


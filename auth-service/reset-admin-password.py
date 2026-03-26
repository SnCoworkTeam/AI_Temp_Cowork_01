"""
重置admin用户密码的脚本
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.core.database import get_db, init_database
from src.repositories.user_repository import UserRepository

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_admin_password(new_password: str = "admin123456"):
    """重置admin用户密码"""
    try:
        # 初始化数据库
        if not init_database():
            print("❌ 数据库初始化失败")
            return False
        
        # 获取数据库会话
        db: Session = next(get_db())
        
        try:
            # 查找admin用户
            user_repo = UserRepository(db)
            user = user_repo.get_by_username("admin")
            
            if not user:
                print("❌ 未找到admin用户")
                return False
            
            print(f"✅ 找到用户: {user.username} (ID: {user.id})")
            
            # 加密新密码
            new_password_hash = pwd_context.hash(new_password)
            
            # 更新密码
            user.password_hash = new_password_hash
            db.commit()
            
            print(f"✅ 密码已重置为: {new_password}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 重置密码失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="重置admin用户密码")
    parser.add_argument("--password", "-p", default="admin123456", help="新密码（默认: admin123456）")
    args = parser.parse_args()
    
    print("=" * 50)
    print("重置admin用户密码")
    print("=" * 50)
    print(f"新密码: {args.password}")
    print("=" * 50)
    
    success = reset_admin_password(args.password)
    
    if success:
        print("\n✅ 密码重置成功！")
        print(f"现在可以使用以下凭据登录:")
        print(f"  用户名: admin")
        print(f"  密码: {args.password}")
    else:
        print("\n❌ 密码重置失败")
        sys.exit(1)


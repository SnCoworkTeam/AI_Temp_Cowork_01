"""
创建admin管理员账号的脚本
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.core.database import init_database
from database.src.core.session import get_db
from src.repositories.user_repository import UserRepository
from database.src.models.user_models import UserStatus

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(password: str = "admin123456", email: str = "admin@example.com"):
    """创建admin用户"""
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
            
            if user:
                print(f"✅ admin用户已存在: {user.username} (ID: {user.id})")
                # 更新密码
                password_hash = pwd_context.hash(password)
                user.password_hash = password_hash
                db.commit()
                print(f"✅ 密码已更新为: {password}")
                return True
            else:
                print("创建admin用户...")
                
                # 加密密码
                password_hash = pwd_context.hash(password)
                
                # 创建用户
                user = user_repo.create_user(
                    username="admin",
                    email=email,
                    password_hash=password_hash,
                    full_name="系统管理员",
                    status="active"
                )
                
                db.commit()
                
                print(f"✅ admin用户已创建: {user.username} (ID: {user.id})")
                print(f"✅ 密码: {password}")
                return True
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 创建admin用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="创建admin管理员账号")
    parser.add_argument("--password", "-p", default="admin123456", help="密码（默认: admin123456）")
    parser.add_argument("--email", "-e", default="admin@example.com", help="邮箱（默认: admin@example.com）")
    args = parser.parse_args()
    
    print("=" * 50)
    print("创建admin管理员账号")
    print("=" * 50)
    print(f"用户名: admin")
    print(f"密码: {args.password}")
    print(f"邮箱: {args.email}")
    print("=" * 50)
    
    success = create_admin_user(args.password, args.email)
    
    if success:
        print("\n✅ admin账号创建/更新成功！")
        print(f"现在可以使用以下凭据登录:")
        print(f"  用户名: admin")
        print(f"  密码: {args.password}")
    else:
        print("\n❌ admin账号创建失败")
        sys.exit(1)

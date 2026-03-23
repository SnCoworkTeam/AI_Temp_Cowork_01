"""
添加processed_at列到documents表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.database import get_database_settings, get_engine
from sqlalchemy import text

def add_processed_at_column():
    """添加processed_at列"""
    try:
        settings = get_database_settings()
        engine = get_engine()
        
        with engine.connect() as conn:
            # 检查列是否已存在
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' 
                AND column_name = 'processed_at'
            """)
            result = conn.execute(check_query)
            exists = result.fetchone() is not None
            
            if not exists:
                # 添加列
                alter_query = text("""
                    ALTER TABLE documents 
                    ADD COLUMN processed_at TIMESTAMP NULL
                """)
                conn.execute(alter_query)
                
                # 添加注释
                comment_query = text("""
                    COMMENT ON COLUMN documents.processed_at IS '处理完成时间'
                """)
                conn.execute(comment_query)
                
                conn.commit()
                print("✅ processed_at 列已成功添加到 documents 表")
                return True
            else:
                print("ℹ️  processed_at 列已存在，跳过")
                return True
                
    except Exception as e:
        print(f"❌ 添加列失败: {e}")
        return False

if __name__ == "__main__":
    success = add_processed_at_column()
    sys.exit(0 if success else 1)



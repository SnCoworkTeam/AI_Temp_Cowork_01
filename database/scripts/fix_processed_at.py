"""
修复processed_at列
直接使用psycopg2连接数据库
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 从环境变量获取数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "enterprise_ai_platform")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def fix_processed_at():
    """添加processed_at列"""
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # 检查列是否存在
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            AND column_name = 'processed_at'
        """)
        
        exists = cur.fetchone() is not None
        
        if not exists:
            # 添加列
            cur.execute("""
                ALTER TABLE documents 
                ADD COLUMN processed_at TIMESTAMP NULL
            """)
            
            # 添加注释
            cur.execute("""
                COMMENT ON COLUMN documents.processed_at IS '处理完成时间'
            """)
            
            print("✅ processed_at 列已成功添加到 documents 表")
        else:
            print("ℹ️  processed_at 列已存在，跳过")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 添加列失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_processed_at()
    sys.exit(0 if success else 1)



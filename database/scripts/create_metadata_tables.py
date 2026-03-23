#!/usr/bin/env python3
"""
创建元数据表的脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.database import get_engine
from sqlalchemy import text

def create_metadata_tables():
    """创建元数据表"""
    engine = get_engine()
    
    sql_file = Path(__file__).parent / "create_metadata_tables.sql"
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print("=" * 50)
    print("创建元数据表...")
    print("=" * 50)
    
    try:
        with engine.begin() as conn:
            # 执行SQL
            conn.execute(text(sql))
        print("✅ 元数据表创建成功！")
        
        # 验证表是否创建
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('ai_models', 'data_assets', 'business_entities')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n✅ 已创建的表: {', '.join(tables)}")
            return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_metadata_tables()
    sys.exit(0 if success else 1)



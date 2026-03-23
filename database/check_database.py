#!/usr/bin/env python3
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, inspect, text
    from src.core.database import DATABASE_URL
    
    print("=== 数据库连接测试 ===")
    engine = create_engine(DATABASE_URL)
    
    # 测试连接
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        db_version = result.scalar()
        print(f"数据库版本: {db_version}")
        
        # 检查表数量
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n数据库表总数: {len(tables)}")
        
        # 显示表列表（分组显示）
        print("\n=== 主要业务表 ===")
        business_tables = [t for t in tables if any(x in t for x in ['user', 'project', 'workflow', 'agent', 'knowledge'])]
        for table in sorted(business_tables):
            print(f"  - {table}")
        
        print("\n=== 系统表 ===")
        system_tables = [t for t in tables if t in ['alembic_version', 'spatial_ref_sys'] or 'migration' in t]
        for table in sorted(system_tables):
            print(f"  - {table}")
        
        print("\n=== 其他表 ===")
        other_tables = [t for t in tables if t not in business_tables and t not in system_tables]
        for table in sorted(other_tables):
            print(f"  - {table}")
        
        # 检查alembic版本表
        print("\n=== Alembic状态 ===")
        try:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            alembic_version = result.scalar()
            print(f"Alembic版本: {alembic_version}")
        except Exception as e:
            print(f"Alembic版本表错误: {e}")
            
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n尝试使用环境变量...")
    import subprocess
    result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
    print(f"PostgreSQL客户端: {result.stdout.strip()}")
    
    # 尝试直接连接
    import psycopg2
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="your_database",
            user="your_username",
            password="your_password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), current_user")
        db, user = cursor.fetchone()
        print(f"已连接到数据库: {db}, 用户: {user}")
        conn.close()
    except Exception as e:
        print(f"连接失败: {e}")

#!/usr/bin/env python3
"""配置用户管理员权限"""
import psycopg2
import os
import json

# 数据库连接
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'ai_platform')
DB_USER = os.getenv('DB_USER', 'ai_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'ai_password')

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    cur = conn.cursor()
    
    # 添加roles列（如果不存在）
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS roles JSONB DEFAULT '[]'::jsonb;
    """)
    
    # 配置管理员权限
    admin_users = ['admin', 'guanruibei', 'zhaojun']
    for username in admin_users:
        cur.execute("""
            UPDATE users 
            SET roles = %s::jsonb 
            WHERE username = %s;
        """, (json.dumps(['admin']), username))
        print(f"✅ 已配置 {username} 为管理员")
    
    conn.commit()
    
    # 查询结果
    cur.execute("""
        SELECT username, roles 
        FROM users 
        WHERE username IN %s;
    """, (tuple(admin_users),))
    
    print("\n📋 管理员权限配置结果:")
    for row in cur.fetchall():
        username, roles = row
        print(f"  - {username}: {roles}")
    
    cur.close()
    conn.close()
    
    print("\n✅ 配置完成！")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    exit(1)


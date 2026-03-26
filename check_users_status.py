#!/usr/bin/env python3
"""
检查用户创建和项目关联状态
"""
import sys
import os
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

from src.core.database import SessionLocal, init_database
from src.repositories.user_repository import UserRepository
from sqlalchemy import text

init_database()
db = SessionLocal()

try:
    # 统计用户数量
    total_users = db.execute(text('SELECT COUNT(*) FROM users')).scalar()
    print(f'Total users: {total_users}')
    
    # 检查新创建的用户
    new_users = db.execute(text("""
        SELECT username, email, full_name 
        FROM users 
        WHERE username IN ('guanruibei', 'zhaojun', 'chenyingyi', 'liuyang', 'yinyong6')
        ORDER BY created_at DESC 
        LIMIT 10
    """)).fetchall()
    print(f'\nSample new users:')
    for user in new_users:
        print(f'  - {user[2]} ({user[0]}) - {user[1]}')
    
    # 统计项目成员关联
    member_count = db.execute(text('SELECT COUNT(*) FROM pm_project_members')).scalar()
    print(f'\nTotal project members: {member_count}')
    
    # 检查特定用户的项目关联
    user_id = db.execute(text("SELECT id FROM users WHERE username = 'guanruibei'")).scalar()
    if user_id:
        projects = db.execute(text('SELECT COUNT(*) FROM pm_project_members WHERE user_id = :user_id'), {'user_id': user_id}).scalar()
        print(f'\nUser guanruibei is member of {projects} projects')
        
        # 列出前5个项目
        project_list = db.execute(text("""
            SELECT p.name, pm.role 
            FROM pm_project_members pm
            JOIN pm_projects p ON p.id = pm.project_id
            WHERE pm.user_id = :user_id
            LIMIT 5
        """), {'user_id': user_id}).fetchall()
        print(f'\nSample projects for guanruibei:')
        for proj in project_list:
            print(f'  - {proj[0]} (role: {proj[1]})')
    
    # 统计每个用户关联的项目数
    user_project_stats = db.execute(text("""
        SELECT u.username, u.full_name, COUNT(pm.id) as project_count
        FROM users u
        LEFT JOIN pm_project_members pm ON pm.user_id = u.id
        WHERE u.username IN (
            'guanruibei', 'zhaojun', 'chenyingyi', 'liuyang', 'yinyong6',
            'xueyanghuaichao', 'chenqinxiang', 'yuhao18', 'wangchong4'
        )
        GROUP BY u.id, u.username, u.full_name
        ORDER BY project_count DESC
        LIMIT 10
    """)).fetchall()
    
    print(f'\nUser project association stats:')
    for stat in user_project_stats:
        print(f'  - {stat[1]} ({stat[0]}): {stat[2]} projects')
    
finally:
    db.close()



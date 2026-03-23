#!/usr/bin/env python3
"""
检查迁移状态和数据
"""
import sys
import os
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

from database.src.core.session import init_session_factory, get_session
from database.src.models.project_models import Project
from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
from sqlalchemy import text

init_session_factory()

with get_session() as db:
    # 检查reporter_id字段
    print("=" * 80)
    print("检查reporter_id字段")
    print("=" * 80)
    result = db.execute(text("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'pm_projects' 
        AND column_name = 'reporter_id'
    """))
    row = result.first()
    if row:
        print(f"✅ reporter_id字段存在: {row[0]} ({row[1]}, nullable: {row[2]})")
    else:
        print("❌ reporter_id字段不存在")
    
    print("")
    
    # 检查基础数据分类
    print("=" * 80)
    print("检查基础数据分类")
    print("=" * 80)
    categories = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type.in_(['project_status', 'project_phase'])
    ).all()
    print(f"找到 {len(categories)} 个分类:")
    for cat in categories:
        print(f"  - {cat.category_type}/{cat.code}: {cat.name}")
    
    print("")
    
    # 检查项目分类关联
    print("=" * 80)
    print("检查项目分类关联")
    print("=" * 80)
    mappings = db.query(ProjectBasicDataMapping).join(BasicDataCategory).filter(
        BasicDataCategory.category_type.in_(['project_status', 'project_phase'])
    ).limit(20).all()
    print(f"找到 {len(mappings)} 个关联:")
    for mapping in mappings:
        project = db.query(Project).filter(Project.id == mapping.project_id).first()
        category = db.query(BasicDataCategory).filter(BasicDataCategory.id == mapping.category_id).first()
        if project and category:
            print(f"  - {project.name}: {category.category_type}/{category.name}")
    
    print("")
    
    # 检查填报人
    print("=" * 80)
    print("检查项目填报人")
    print("=" * 80)
    projects_with_reporter = db.query(Project).filter(Project.reporter_id.isnot(None)).limit(10).all()
    print(f"找到 {len(projects_with_reporter)} 个有填报人的项目:")
    for proj in projects_with_reporter:
        from database.src.models.user_models import User
        reporter = db.query(User).filter(User.id == proj.reporter_id).first()
        if reporter:
            print(f"  - {proj.name}: {reporter.full_name} ({reporter.username})")
    
    print("")
    print("=" * 80)
    print("完成")
    print("=" * 80)



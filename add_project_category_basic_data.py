#!/usr/bin/env python3
"""
添加项目分类基础数据
"""
import sys
from pathlib import Path

project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.project_models import Project
from database.src.models.basic_data_models import BasicDataCategory

# 项目分类数据
PROJECT_CATEGORIES = [
    {"code": "01", "name": "基设网安", "sort_order": 1},
    {"code": "02", "name": "业务经营", "sort_order": 2},
    {"code": "03", "name": "管理应用", "sort_order": 3},
    {"code": "04", "name": "生产运营", "sort_order": 4},
    {"code": "05", "name": "瑞恒基地", "sort_order": 5},
]

def get_or_create_category(db, category_type: str, code: str, name: str, sort_order: int = 0):
    """获取或创建基础数据分类"""
    category = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == category_type,
        BasicDataCategory.code == code
    ).first()
    
    if category:
        # 更新现有分类
        category.name = name
        category.sort_order = sort_order
        category.is_active = True
        print(f"  ✅ 更新分类: {category_type}/{code} - {name}")
        return category
    else:
        # 创建新分类
        category = BasicDataCategory(
            category_type=category_type,
            code=code,
            name=name,
            sort_order=sort_order,
            is_active=True
        )
        db.add(category)
        print(f"  ✅ 创建分类: {category_type}/{code} - {name}")
        return category

def main():
    print("=" * 80)
    print("添加项目分类基础数据")
    print("=" * 80)
    print("")
    
    init_session_factory()
    
    try:
        with get_session() as db:
            # 更新项目分类
            print("更新项目分类 (project_category)...")
            for item in PROJECT_CATEGORIES:
                get_or_create_category(
                    db,
                    category_type="project_category",
                    code=item["code"],
                    name=item["name"],
                    sort_order=item["sort_order"]
                )
            
            db.commit()
            print("")
            print("=" * 80)
            print("✅ 项目分类基础数据添加完成！")
            print("=" * 80)
            
            # 显示统计信息
            print("")
            print("统计信息:")
            count = db.query(BasicDataCategory).filter(
                BasicDataCategory.category_type == "project_category"
            ).count()
            print(f"  项目分类 (project_category): {count} 个")
            
            # 显示所有项目分类
            categories = db.query(BasicDataCategory).filter(
                BasicDataCategory.category_type == "project_category"
            ).order_by(BasicDataCategory.sort_order, BasicDataCategory.code).all()
            
            print("")
            print("项目分类列表:")
            for cat in categories:
                print(f"  {cat.code}: {cat.name}")
            
    except Exception as e:
        print(f"❌ 添加失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()



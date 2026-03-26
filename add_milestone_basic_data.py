"""
在基础数据中添加里程碑数据
包括：实施启动、方案确认、交付上线、项目验收
"""
import sys
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

# Adjust path for imports within the Docker container
project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.basic_data_models import BasicDataCategory
from database.src.models.project_models import Project  # 导入Project以解决relationship问题

def get_or_create_category(db: Session, category_type: str, code: str, name: str, description: Optional[str] = None, sort_order: int = 0) -> BasicDataCategory:
    """获取或创建基础数据分类"""
    category = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == category_type,
        BasicDataCategory.code == code
    ).first()
    
    if category:
        # 更新现有分类
        category.name = name
        if description:
            category.description = description
        category.sort_order = sort_order
        category.is_active = True
        print(f"  ✅ 更新分类: {category_type} - {code} ({name})")
    else:
        # 创建新分类
        category = BasicDataCategory(
            category_type=category_type,
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=True
        )
        db.add(category)
        print(f"  ✅ 创建分类: {category_type} - {code} ({name})")
    
    db.commit()
    return category

def main():
    print("=" * 80)
    print("添加里程碑基础数据")
    print("=" * 80)
    print("")

    init_session_factory()

    try:
        with get_session() as db:
            # 里程碑数据
            milestone_data = [
                {"code": "01", "name": "实施启动", "sort_order": 1, "description": "项目正式启动，开始实施阶段"},
                {"code": "02", "name": "方案确认", "sort_order": 2, "description": "项目方案获得确认，进入执行阶段"},
                {"code": "03", "name": "交付上线", "sort_order": 3, "description": "项目交付物完成，系统上线运行"},
                {"code": "04", "name": "项目验收", "sort_order": 4, "description": "项目通过验收，正式结束"},
            ]

            print("添加里程碑 (milestone)...")
            for item in milestone_data:
                get_or_create_category(
                    db,
                    "milestone",
                    item["code"],
                    item["name"],
                    description=item.get("description"),
                    sort_order=item["sort_order"]
                )

            print("")
            print("=" * 80)
            print("✅ 里程碑基础数据添加完成！")
            print("=" * 80)

            print("")
            print("统计信息:")
            print(f"  里程碑 (milestone): {db.query(BasicDataCategory).filter(BasicDataCategory.category_type == 'milestone').count()} 个")

            print("")
            print("里程碑列表:")
            for cat in db.query(BasicDataCategory).filter(BasicDataCategory.category_type == 'milestone').order_by(BasicDataCategory.sort_order).all():
                print(f"  {cat.code}: {cat.name} (排序: {cat.sort_order})")

    except Exception as e:
        print(f"❌ 添加里程碑基础数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


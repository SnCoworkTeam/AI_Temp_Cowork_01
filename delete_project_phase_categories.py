"""
删除项目阶段基础数据中的三条记录：
1. 01准备_可研 (编码: 01准备_可研)
2. 02正常进行 (编码: 02正常进行)
3. 03实施 (编码: 03实施)
"""
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Adjust path for imports within the Docker container
project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.basic_data_models import BasicDataCategory, ProjectBasicDataMapping
from database.src.models.project_models import Project  # 导入Project以解决relationship问题

def main():
    print("=" * 80)
    print("删除项目阶段基础数据")
    print("=" * 80)
    print("")

    init_session_factory()

    try:
        with get_session() as db:
            # 要删除的分类编码列表
            codes_to_delete = [
                '01准备_可研',
                '02正常进行',
                '03实施'
            ]

            deleted_count = 0
            mapping_deleted_count = 0

            for code in codes_to_delete:
                # 查找要删除的分类
                category = db.query(BasicDataCategory).filter(
                    BasicDataCategory.category_type == 'project_phase',
                    BasicDataCategory.code == code
                ).first()

                if category:
                    category_id = category.id
                    category_name = category.name
                    
                    # 先删除关联的项目基础数据映射
                    mappings = db.query(ProjectBasicDataMapping).filter(
                        ProjectBasicDataMapping.category_id == category_id
                    ).all()
                    
                    for mapping in mappings:
                        db.delete(mapping)
                        mapping_deleted_count += 1
                    
                    # 删除分类本身
                    db.delete(category)
                    deleted_count += 1
                    print(f"  ✅ 删除分类: {code} ({category_name})")
                    if mappings:
                        print(f"     同时删除了 {len(mappings)} 条项目关联记录")
                else:
                    print(f"  ⚠️  未找到分类: {code}")

            db.commit()

            print("")
            print("=" * 80)
            print("✅ 删除完成！")
            print("=" * 80)
            print(f"删除分类数量: {deleted_count}")
            print(f"删除项目关联记录数量: {mapping_deleted_count}")

            # 显示剩余的项目阶段分类
            print("")
            print("剩余的项目阶段分类:")
            remaining = db.query(BasicDataCategory).filter(
                BasicDataCategory.category_type == 'project_phase'
            ).order_by(BasicDataCategory.sort_order, BasicDataCategory.code).all()
            
            if remaining:
                for cat in remaining:
                    print(f"  {cat.code}: {cat.name} (排序: {cat.sort_order})")
            else:
                print("  (无)")

    except Exception as e:
        print(f"❌ 删除失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


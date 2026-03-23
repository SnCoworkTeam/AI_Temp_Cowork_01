"""
迁移现有的项目阶段和里程碑数据，为它们设置category_id
"""
import sys
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

# Adjust path for imports within the Docker container
project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.basic_data_models import BasicDataCategory
from database.src.models.project_models import ProjectPhase, Milestone

def migrate_phases(db: Session):
    """迁移项目阶段数据"""
    print("=" * 80)
    print("迁移项目阶段数据")
    print("=" * 80)
    
    # 获取所有项目阶段分类
    phase_categories = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == 'project_phase',
        BasicDataCategory.is_active == True
    ).all()
    
    category_map = {cat.name: cat.id for cat in phase_categories}
    print(f"找到 {len(category_map)} 个项目阶段分类:")
    for name, cat_id in category_map.items():
        print(f"  {name}: {cat_id}")
    
    # 获取所有没有category_id的阶段
    phases_without_category = db.query(ProjectPhase).filter(
        ProjectPhase.category_id.is_(None)
    ).all()
    
    print(f"\n找到 {len(phases_without_category)} 个没有category_id的阶段")
    
    updated_count = 0
    not_found_count = 0
    
    for phase in phases_without_category:
        # 尝试通过名称匹配
        category_id = category_map.get(phase.name)
        
        if category_id:
            phase.category_id = category_id
            phase.name = phase.name  # 保持名称一致
            updated_count += 1
            print(f"  ✅ 更新阶段: {phase.name} -> {category_id}")
        else:
            # 尝试模糊匹配
            matched = False
            for cat_name, cat_id in category_map.items():
                if cat_name in phase.name or phase.name in cat_name:
                    phase.category_id = cat_id
                    phase.name = cat_name  # 使用基础数据中的标准名称
                    updated_count += 1
                    matched = True
                    print(f"  ✅ 模糊匹配更新阶段: {phase.name} -> {cat_name} ({cat_id})")
                    break
            
            if not matched:
                not_found_count += 1
                print(f"  ⚠️  无法匹配阶段: {phase.name} (ID: {phase.id})")
    
    db.commit()
    print(f"\n迁移完成: 更新 {updated_count} 个，未匹配 {not_found_count} 个")
    return updated_count, not_found_count

def migrate_milestones(db: Session):
    """迁移里程碑数据"""
    print("\n" + "=" * 80)
    print("迁移里程碑数据")
    print("=" * 80)
    
    # 获取所有里程碑分类
    milestone_categories = db.query(BasicDataCategory).filter(
        BasicDataCategory.category_type == 'milestone',
        BasicDataCategory.is_active == True
    ).all()
    
    category_map = {cat.name: cat.id for cat in milestone_categories}
    print(f"找到 {len(category_map)} 个里程碑分类:")
    for name, cat_id in category_map.items():
        print(f"  {name}: {cat_id}")
    
    # 获取所有没有category_id的里程碑
    milestones_without_category = db.query(Milestone).filter(
        Milestone.category_id.is_(None)
    ).all()
    
    print(f"\n找到 {len(milestones_without_category)} 个没有category_id的里程碑")
    
    updated_count = 0
    not_found_count = 0
    
    for milestone in milestones_without_category:
        # 尝试通过名称匹配
        category_id = category_map.get(milestone.name)
        
        if category_id:
            milestone.category_id = category_id
            milestone.name = milestone.name  # 保持名称一致
            updated_count += 1
            print(f"  ✅ 更新里程碑: {milestone.name} -> {category_id}")
        else:
            # 尝试模糊匹配
            matched = False
            for cat_name, cat_id in category_map.items():
                if cat_name in milestone.name or milestone.name in cat_name:
                    milestone.category_id = cat_id
                    milestone.name = cat_name  # 使用基础数据中的标准名称
                    updated_count += 1
                    matched = True
                    print(f"  ✅ 模糊匹配更新里程碑: {milestone.name} -> {cat_name} ({cat_id})")
                    break
            
            if not matched:
                not_found_count += 1
                print(f"  ⚠️  无法匹配里程碑: {milestone.name} (ID: {milestone.id})")
    
    db.commit()
    print(f"\n迁移完成: 更新 {updated_count} 个，未匹配 {not_found_count} 个")
    return updated_count, not_found_count

def main():
    print("=" * 80)
    print("迁移现有项目阶段和里程碑数据")
    print("=" * 80)
    print("")
    
    init_session_factory()
    
    try:
        with get_session() as db:
            phase_updated, phase_not_found = migrate_phases(db)
            milestone_updated, milestone_not_found = migrate_milestones(db)
            
            print("\n" + "=" * 80)
            print("迁移统计")
            print("=" * 80)
            print(f"项目阶段: 更新 {phase_updated} 个，未匹配 {phase_not_found} 个")
            print(f"里程碑: 更新 {milestone_updated} 个，未匹配 {milestone_not_found} 个")
            
            # 检查是否还有未匹配的记录
            remaining_phases = db.query(ProjectPhase).filter(ProjectPhase.category_id.is_(None)).count()
            remaining_milestones = db.query(Milestone).filter(Milestone.category_id.is_(None)).count()
            
            if remaining_phases > 0 or remaining_milestones > 0:
                print(f"\n⚠️  警告: 仍有 {remaining_phases} 个阶段和 {remaining_milestones} 个里程碑没有category_id")
                print("这些记录需要手动处理或删除")
            
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ 迁移完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()


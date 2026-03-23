#!/usr/bin/env python3
"""
更新基础数据分类
包括项目阶段和阶段状态
"""
import sys
import os
from pathlib import Path
from typing import Optional

# Adjust path for imports within the Docker container
project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
# 导入所有相关模型以确保关系正确初始化
from database.src.models.project_models import Project  # 确保Project模型被导入
from database.src.models.basic_data_models import BasicDataCategory

# 项目阶段数据
PROJECT_PHASES = [
    {"code": "01", "name": "01-准备/可研", "sort_order": 1},
    {"code": "02", "name": "02-寻源", "sort_order": 2},
    {"code": "03", "name": "03-实施", "sort_order": 3},
    {"code": "04", "name": "04-交付", "sort_order": 4},
    {"code": "05", "name": "05-收尾", "sort_order": 5},
]

# 阶段状态数据
PHASE_STATUSES = [
    {"code": "01", "name": "01-未开始", "sort_order": 1},
    {"code": "02", "name": "02-正常进行", "sort_order": 2},
    {"code": "03", "name": "03-延期进行", "sort_order": 3},
    {"code": "04", "name": "04-暂停", "sort_order": 4},
    {"code": "05", "name": "05-√部分", "sort_order": 5},
    {"code": "06", "name": "06-√全部", "sort_order": 6},
    {"code": "07", "name": "07-取消", "sort_order": 7},
    {"code": "08", "name": "08-N/A", "sort_order": 8},
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
    print("更新基础数据分类")
    print("=" * 80)
    print("")
    
    init_session_factory()
    
    try:
        with get_session() as db:
            # 更新项目阶段
            print("更新项目阶段 (project_phase)...")
            for phase in PROJECT_PHASES:
                get_or_create_category(
                    db,
                    category_type="project_phase",
                    code=phase["code"],
                    name=phase["name"],
                    sort_order=phase["sort_order"]
                )
            
            print("")
            
            # 更新阶段状态
            print("更新阶段状态 (phase_status)...")
            for status in PHASE_STATUSES:
                get_or_create_category(
                    db,
                    category_type="phase_status",
                    code=status["code"],
                    name=status["name"],
                    sort_order=status["sort_order"]
                )
            
            db.commit()
            print("")
            print("=" * 80)
            print("✅ 基础数据更新完成！")
            print("=" * 80)
            
            # 显示统计信息
            print("")
            print("统计信息:")
            phase_count = db.query(BasicDataCategory).filter(
                BasicDataCategory.category_type == "project_phase"
            ).count()
            status_count = db.query(BasicDataCategory).filter(
                BasicDataCategory.category_type == "phase_status"
            ).count()
            print(f"  项目阶段: {phase_count} 个")
            print(f"  阶段状态: {status_count} 个")
            
    except Exception as e:
        print(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


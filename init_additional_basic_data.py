#!/usr/bin/env python3
"""
初始化额外的基础数据分类
包括：产业链、生产基地/业务单元、应用领域
"""
import sys
from pathlib import Path

project_root = Path('/app')
sys.path.insert(0, str(project_root.parent / 'database' / 'src'))
sys.path.insert(0, str(project_root.parent / 'project-management' / 'src'))

from database.src.core.session import get_session, init_session_factory
from database.src.models.project_models import Project
from database.src.models.basic_data_models import BasicDataCategory

# 产业链数据（示例，可根据实际情况调整）
INDUSTRY_CHAINS = [
    {"code": "01", "name": "化工新材料", "sort_order": 1},
    {"code": "02", "name": "精细化工", "sort_order": 2},
    {"code": "03", "name": "农化", "sort_order": 3},
    {"code": "04", "name": "其他", "sort_order": 4},
]

# 生产基地/业务单元数据（示例，可根据实际情况调整）
PRODUCTION_BASES = [
    {"code": "01", "name": "中化国际总部", "sort_order": 1},
    {"code": "02", "name": "中化蓝天", "sort_order": 2},
    {"code": "03", "name": "中化塑料", "sort_order": 3},
    {"code": "04", "name": "中化物流", "sort_order": 4},
    {"code": "05", "name": "其他", "sort_order": 5},
]

# 应用领域数据（示例，可根据实际情况调整）
APPLICATION_DOMAINS = [
    {"code": "01", "name": "生产制造", "sort_order": 1},
    {"code": "02", "name": "供应链管理", "sort_order": 2},
    {"code": "03", "name": "销售与营销", "sort_order": 3},
    {"code": "04", "name": "财务管理", "sort_order": 4},
    {"code": "05", "name": "人力资源", "sort_order": 5},
    {"code": "06", "name": "研发创新", "sort_order": 6},
    {"code": "07", "name": "数字化转型", "sort_order": 7},
    {"code": "08", "name": "其他", "sort_order": 8},
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
    print("初始化额外的基础数据分类")
    print("=" * 80)
    print("")
    
    init_session_factory()
    
    try:
        with get_session() as db:
            # 更新产业链
            print("更新产业链 (industry_chain)...")
            for item in INDUSTRY_CHAINS:
                get_or_create_category(
                    db,
                    category_type="industry_chain",
                    code=item["code"],
                    name=item["name"],
                    sort_order=item["sort_order"]
                )
            
            print("")
            
            # 更新生产基地/业务单元
            print("更新生产基地/业务单元 (production_base)...")
            for item in PRODUCTION_BASES:
                get_or_create_category(
                    db,
                    category_type="production_base",
                    code=item["code"],
                    name=item["name"],
                    sort_order=item["sort_order"]
                )
            
            print("")
            
            # 更新应用领域
            print("更新应用领域 (application_domain)...")
            for item in APPLICATION_DOMAINS:
                get_or_create_category(
                    db,
                    category_type="application_domain",
                    code=item["code"],
                    name=item["name"],
                    sort_order=item["sort_order"]
                )
            
            db.commit()
            print("")
            print("=" * 80)
            print("✅ 基础数据初始化完成！")
            print("=" * 80)
            
            # 显示统计信息
            print("")
            print("统计信息:")
            for cat_type, cat_name in [
                ("industry_chain", "产业链"),
                ("production_base", "生产基地/业务单元"),
                ("application_domain", "应用领域"),
                ("project_phase", "项目阶段"),
                ("phase_status", "阶段状态"),
            ]:
                count = db.query(BasicDataCategory).filter(
                    BasicDataCategory.category_type == cat_type
                ).count()
                print(f"  {cat_name} ({cat_type}): {count} 个")
            
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()



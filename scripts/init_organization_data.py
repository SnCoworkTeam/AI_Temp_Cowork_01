#!/usr/bin/env python3
"""
初始化组织架构数据脚本
在服务器上运行此脚本来生成组织架构演示数据
"""
import sys
from pathlib import Path
from uuid import uuid4

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.src.core.session import get_db, init_session_factory
from database.src.models.enterprise_architecture_models import OrganizationUnit

def init_org_data():
    """初始化组织架构数据"""
    print("=" * 60)
    print("初始化组织架构数据...")
    print("=" * 60)
    
    # 初始化数据库会话工厂
    init_session_factory()
    db = next(get_db())
    
    try:
        # 检查是否已有数据
        existing_count = db.query(OrganizationUnit).count()
        if existing_count > 0:
            print(f"\n✅ 组织数据已存在: {existing_count} 个组织单元")
            print("如需重新生成，请先清空现有数据")
            return
        
        # 创建演示组织
        orgs = [
            {
                'name': 'LuminaOS集团',
                'code': 'LUMINA_GROUP',
                'description': 'LuminaOS企业AI平台总部',
                'organization_type': '集团',
                'level': 1
            },
            {
                'name': '技术中心',
                'code': 'TECH_CENTER',
                'description': '技术研发中心',
                'organization_type': '部门',
                'level': 2,
                'parent_code': 'LUMINA_GROUP'
            },
            {
                'name': '产品部',
                'code': 'PRODUCT_DEPT',
                'description': '产品管理部门',
                'organization_type': '部门',
                'level': 2,
                'parent_code': 'LUMINA_GROUP'
            },
            {
                'name': 'AI平台团队',
                'code': 'AI_PLATFORM_TEAM',
                'description': 'AI平台开发团队',
                'organization_type': '团队',
                'level': 3,
                'parent_code': 'TECH_CENTER'
            },
            {
                'name': '企业架构团队',
                'code': 'EA_TEAM',
                'description': '企业架构管理团队',
                'organization_type': '团队',
                'level': 3,
                'parent_code': 'TECH_CENTER'
            },
            {
                'name': '数据团队',
                'code': 'DATA_TEAM',
                'description': '数据管理团队',
                'organization_type': '团队',
                'level': 3,
                'parent_code': 'TECH_CENTER'
            },
            {
                'name': '产品规划组',
                'code': 'PRODUCT_PLANNING',
                'description': '产品规划组',
                'organization_type': '团队',
                'level': 3,
                'parent_code': 'PRODUCT_DEPT'
            }
        ]
        
        org_map = {}
        created_count = 0
        
        for org_data in orgs:
            parent_id = None
            if 'parent_code' in org_data:
                parent = org_map.get(org_data['parent_code'])
                if parent:
                    parent_id = parent.id
            
            org = OrganizationUnit(
                id=uuid4(),
                name=org_data['name'],
                code=org_data['code'],
                description=org_data['description'],
                organization_type=org_data['organization_type'],
                level=org_data['level'],
                parent_id=parent_id,
                status='active'
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            org_map[org_data['code']] = org
            created_count += 1
            print(f"  ✅ 创建组织单元: {org.name} ({org.code})")
        
        print(f"\n✅ 成功创建 {created_count} 个组织单元")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_org_data()


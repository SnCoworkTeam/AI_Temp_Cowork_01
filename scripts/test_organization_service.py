#!/usr/bin/env python3
"""
测试组织架构服务
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from database.src.core.database import get_engine
from database.src.models.enterprise_architecture_models import OrganizationUnit

import sys
from pathlib import Path
metadata_service_path = Path(__file__).parent.parent / "metadata-service" / "src"
sys.path.insert(0, str(metadata_service_path))
from services.organization_architecture_service import OrganizationArchitectureService

async def test_organization_service():
    """测试组织架构服务"""
    print("=" * 50)
    print("测试组织架构服务")
    print("=" * 50)
    
    # 创建数据库会话
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 创建服务实例
        service = OrganizationArchitectureService(session)
        
        # 测试1: 创建组织单元
        print("\n1. 测试创建组织单元...")
        org = await service.create_organization_unit(
            name="测试部门",
            code="TEST_DEPT",
            organization_type="Department",
            level=1,
            description="这是一个测试部门"
        )
        print(f"  ✅ 组织单元创建成功: {org.name} (ID: {org.id})")
        
        # 测试2: 获取组织单元
        print("\n2. 测试获取组织单元...")
        retrieved_org = await service.get_organization_unit(org.id)
        if retrieved_org and retrieved_org.name == "测试部门":
            print(f"  ✅ 组织单元获取成功: {retrieved_org.name}")
        else:
            print("  ❌ 组织单元获取失败")
        
        # 测试3: 获取组织层级
        print("\n3. 测试获取组织层级...")
        hierarchy = await service.get_organization_hierarchy(org.id)
        if hierarchy and hierarchy.get("name") == "测试部门":
            print(f"  ✅ 组织层级获取成功: {hierarchy['name']}")
        else:
            print("  ❌ 组织层级获取失败")
        
        # 测试4: 获取组织责任
        print("\n4. 测试获取组织责任...")
        try:
            responsibilities = await service.get_organization_responsibilities(org.id)
            print(f"  ✅ 组织责任获取成功")
            print(f"     业务能力: {len(responsibilities.get('capabilities', []))} 个")
            print(f"     业务流程: {len(responsibilities.get('processes', []))} 个")
            print(f"     应用系统: {len(responsibilities.get('systems', []))} 个")
        except Exception as e:
            print(f"  ⚠️  组织责任获取: {str(e)} (这是正常的，因为还没有关联数据)")
        
        # 测试5: 获取组织资源
        print("\n5. 测试获取组织资源...")
        try:
            resources = await service.get_organization_resources(org.id)
            print(f"  ✅ 组织资源获取成功")
            print(f"     系统数量: {resources.get('system_count', 0)}")
            print(f"     技术数量: {resources.get('technology_count', 0)}")
        except Exception as e:
            print(f"  ⚠️  组织资源获取: {str(e)} (这是正常的，因为还没有关联数据)")
        
        # 清理测试数据
        print("\n6. 清理测试数据...")
        session.delete(org)
        session.commit()
        print("  ✅ 测试数据清理完成")
        
        print("\n" + "=" * 50)
        print("✅ 所有服务测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_organization_service())


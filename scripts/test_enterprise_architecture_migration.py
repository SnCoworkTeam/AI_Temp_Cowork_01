#!/usr/bin/env python3
"""
测试企业架构模型增强
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.src.core.database import get_database_settings, get_engine
from database.src.models.enterprise_architecture_models import (
    OrganizationUnit, BusinessRole, TechnologyType, TechnologyInstance,
    BusinessProcess, BusinessCapability, ApplicationSystem
)

def test_migration():
    """测试迁移后的模型"""
    print("=" * 50)
    print("测试企业架构模型增强")
    print("=" * 50)
    
    # 创建数据库连接
    try:
        # 尝试使用get_engine（如果可用）
        engine = get_engine()
    except:
        # 降级到直接创建engine
        db_settings = get_database_settings()
        from sqlalchemy.engine.url import URL
        database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME
        )
        engine = create_engine(database_url)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 测试1: 检查新表是否存在
        print("\n1. 检查新表是否存在...")
        tables_to_check = [
            'organization_units',
            'business_roles',
            'technology_types',
            'technology_instances',
            'organization_business_relationships'
        ]
        
        for table in tables_to_check:
            result = session.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if exists:
                print(f"  ✅ {table} 表存在")
            else:
                print(f"  ❌ {table} 表不存在")
        
        # 测试2: 检查增强字段是否存在
        print("\n2. 检查增强字段是否存在...")
        fields_to_check = [
            ('business_processes', 'organization_id'),
            ('business_capabilities', 'owner_organization_id'),
            ('application_systems', 'system_category'),
            ('application_systems', 'business_owner_org_id'),
            ('data_entities', 'code'),
            ('data_entities', 'application_system_id'),
            ('api_interfaces', 'code'),
            ('api_interfaces', 'application_system_id'),
        ]
        
        for table, column in fields_to_check:
            result = session.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}'
                )
            """))
            exists = result.scalar()
            if exists:
                print(f"  ✅ {table}.{column} 字段存在")
            else:
                print(f"  ❌ {table}.{column} 字段不存在")
        
        # 测试3: 测试模型创建
        print("\n3. 测试模型创建...")
        try:
            # 创建组织单元
            org = OrganizationUnit(
                name="测试部门",
                code="TEST_DEPT",
                organization_type="Department",
                level=1
            )
            session.add(org)
            session.commit()
            print("  ✅ OrganizationUnit 创建成功")
            
            # 创建技术类型
            tech_type = TechnologyType(
                name="Oracle",
                category="Database",
                standard_version="19c",
                lifecycle_status="strategic"
            )
            session.add(tech_type)
            session.commit()
            print("  ✅ TechnologyType 创建成功")
            
            # 清理测试数据
            session.delete(org)
            session.delete(tech_type)
            session.commit()
            print("  ✅ 测试数据清理完成")
            
        except Exception as e:
            print(f"  ❌ 模型创建失败: {str(e)}")
            session.rollback()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_migration()


#!/usr/bin/env python3
"""检查组织架构数据"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.src.models.enterprise_architecture_models import OrganizationUnit, BusinessRole

# 数据库连接
DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/enterprise_ai_platform"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # 统计组织单元
    total_count = session.query(func.count(OrganizationUnit.id)).scalar() or 0
    departments_count = session.query(func.count(OrganizationUnit.id)).filter(
        OrganizationUnit.organization_type == "Department"
    ).scalar() or 0
    teams_count = session.query(func.count(OrganizationUnit.id)).filter(
        OrganizationUnit.organization_type == "Team"
    ).scalar() or 0
    organizations_count = session.query(func.count(OrganizationUnit.id)).filter(
        OrganizationUnit.organization_type == "Organization"
    ).scalar() or 0
    roles_count = session.query(func.count(BusinessRole.id)).scalar() or 0
    
    print(f"Organization units total: {total_count}")
    print(f"Organizations: {organizations_count}")
    print(f"Departments: {departments_count}")
    print(f"Teams: {teams_count}")
    print(f"Business roles: {roles_count}")
    
    # 列出所有组织单元
    if total_count > 0:
        orgs = session.query(OrganizationUnit).limit(10).all()
        print("\nSample organizations:")
        for org in orgs:
            print(f"  - {org.name} ({org.organization_type})")
    else:
        print("\nNo organization units found in database")
        
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    session.close()


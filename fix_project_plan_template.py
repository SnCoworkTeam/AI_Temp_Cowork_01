#!/usr/bin/env python3
"""
修复项目计划的模板关联
"""
import sys
import os
sys.path.insert(0, '/opt/enterprise-ai-platform/database/src')
sys.path.insert(0, '/opt/enterprise-ai-platform/shared_libs')

os.environ.setdefault('DB_HOST', 'postgres')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'ai_platform')
os.environ.setdefault('DB_USER', 'ai_user')
os.environ.setdefault('DB_PASSWORD', 'ai_password')

from database.src.core.session import init_session_factory, get_db
from database.src.models.project_models import ProjectPlan, ProjectTemplate
from uuid import UUID

init_session_factory()
db = next(get_db())

project_id = 'ea19c4ca-d0a0-4f5c-b823-efcc5f1fac6b'
project_uuid = UUID(project_id)

# 查找标准模板
standard_template = db.query(ProjectTemplate).filter(
    ProjectTemplate.name.like('%标准信息化项目管理模板%'),
    ProjectTemplate.is_active == True
).first()

if not standard_template:
    print('❌ 未找到标准模板')
    sys.exit(1)

print(f'找到标准模板: {standard_template.name} (ID: {standard_template.id})')

# 查找该项目的活跃计划
active_plan = db.query(ProjectPlan).filter(
    ProjectPlan.project_id == project_uuid,
    ProjectPlan.is_active == True
).first()

if active_plan:
    print(f'\n找到活跃计划: {active_plan.name} (ID: {active_plan.id})')
    print(f'当前模板ID: {active_plan.template_id}')

    # 更新模板ID
    active_plan.template_id = standard_template.id
    db.add(active_plan)
    db.commit()

    print(f'✅ 已更新计划模板ID为: {standard_template.id}')
    print(f'✅ 计划名称: {active_plan.name}')
else:
    print('❌ 未找到活跃计划')


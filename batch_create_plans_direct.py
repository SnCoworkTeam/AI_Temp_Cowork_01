#!/usr/bin/env python3
"""
批量创建项目计划脚本（直接在容器内执行，绕过API认证）
"""
import sys
import os
sys.path.insert(0, '/opt/enterprise-ai-platform/database/src')
sys.path.insert(0, '/opt/enterprise-ai-platform/shared_libs')
sys.path.insert(0, '/opt/enterprise-ai-platform/project_management/src')

# 设置环境变量
os.environ.setdefault('DB_HOST', 'postgres')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'enterprise_ai')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'postgres')

from database.src.core.session import init_session_factory, get_db
from database.src.models.project_models import Project, ProjectPlan, ProjectPhase
from database.src.models.basic_data_models import BasicDataCategory
from database.src.models.project_models import ProjectTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库会话工厂
init_session_factory()
db = next(get_db())

try:
    # 获取所有项目
    all_projects = db.query(Project).all()
    print(f'找到 {len(all_projects)} 个项目')

    # 获取所有启用的项目阶段分类
    phase_categories = (
        db.query(BasicDataCategory)
        .filter(
            BasicDataCategory.category_type == 'project_phase',
            BasicDataCategory.is_active == True
        )
        .order_by(BasicDataCategory.code.asc(), BasicDataCategory.name.asc())
        .all()
    )

    print(f'找到 {len(phase_categories)} 个项目阶段分类')

    if not phase_categories:
        print('❌ 未找到项目阶段分类，请先在基础数据中创建项目阶段分类')
        sys.exit(1)

    # 查找默认模板
    default_template = (
        db.query(ProjectTemplate)
        .filter(
            ProjectTemplate.name.like('%标准信息化项目管理模板%'),
            ProjectTemplate.is_active == True
        )
        .first()
    )

    if not default_template:
        default_template = (
            db.query(ProjectTemplate)
            .filter(ProjectTemplate.is_active == True)
            .first()
        )

    created_plans = 0
    created_phases = 0
    processed = 0

    for project in all_projects:
        try:
            processed += 1

            # 检查是否已有计划
            existing_plan = (
                db.query(ProjectPlan)
                .filter(ProjectPlan.project_id == project.id, ProjectPlan.is_active == True)
                .first()
            )

            if existing_plan:
                print(f'项目 {project.id} ({project.name}) 已有计划，跳过')
                continue

            # 创建项目阶段
            phases_created = 0
            for idx, category in enumerate(phase_categories):
                existing_phase = (
                    db.query(ProjectPhase)
                    .filter(
                        ProjectPhase.project_id == project.id,
                        ProjectPhase.category_id == category.id,
                    )
                    .first()
                )

                if not existing_phase:
                    phase = ProjectPhase(
                        project_id=project.id,
                        category_id=category.id,
                        name=category.name,
                        sequence=idx + 1,
                        description='从基础数据自动创建',
                    )
                    db.add(phase)
                    phases_created += 1

            db.flush()

            # 创建项目计划
            if default_template:
                plan = ProjectPlan(
                    project_id=project.id,
                    name=f'{project.name}项目计划',
                    description=f'基于模板"{default_template.name}"自动创建',
                    version='1.0',
                    template_id=default_template.id,
                    is_active=True,
                    is_baseline=False,
                )
                default_template.usage_count = (default_template.usage_count or 0) + 1
            else:
                plan = ProjectPlan(
                    project_id=project.id,
                    name=f'{project.name}项目计划',
                    description='自动创建的项目计划',
                    version='1.0',
                    is_active=True,
                    is_baseline=False,
                )

            db.add(plan)
            db.flush()

            created_plans += 1
            created_phases += phases_created

            # 每10个项目提交一次
            if processed % 10 == 0:
                db.commit()
                print(f'已处理 {processed} 个项目')

        except Exception as e:
            logger.error(f'为项目 {project.id} 创建计划和阶段失败: {e}', exc_info=True)
            db.rollback()
            continue

    # 最终提交
    db.commit()

    print('')
    print('=' * 60)
    print('✅ 批量创建完成')
    print('=' * 60)
    print(f'处理项目数: {processed}')
    print(f'创建计划数: {created_plans}')
    print(f'创建阶段数: {created_phases}')
    print('=' * 60)

except Exception as e:
    logger.error(f'批量创建计划失败: {e}', exc_info=True)
    db.rollback()
    sys.exit(1)

